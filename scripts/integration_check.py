"""Prueba HTTP end-to-end de los cuatro microservicios, sin depender de n8n."""
import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT=Path(__file__).parents[1]
SERVICES=('prospects','sales','insurance','dashboard')
MODULES={name:f'services.{name}.app' for name in SERVICES}

def request_json(url,method='GET',body=None):
    payload=None if body is None else json.dumps(body).encode()
    request=Request(url,payload,{'Content-Type':'application/json'},method=method)
    try:
        with urlopen(request,timeout=10) as response:
            return response.status,json.load(response)
    except HTTPError as exc:
        try: detail=json.load(exc)
        except Exception: detail={'error':str(exc)}
        raise RuntimeError(f'{method} {url}: HTTP {exc.code} {detail}') from exc

def assert_status(actual,expected,label):
    if actual != expected: raise AssertionError(f'{label}: se esperaba HTTP {expected}, se obtuvo {actual}')

def run_checks(urls):
    for name,url in urls.items():
        status,data=request_json(url+'/health')
        assert_status(status,200,f'salud de {name}')
        if data.get('status')!='ok': raise AssertionError(f'{name} no reportó estado ok')
        print('✓ salud',name)

    run_id=uuid.uuid4().hex
    status,catalogs=request_json(urls['dashboard']+'/api/catalogs')
    assert_status(status,200,'catálogos')
    seller=catalogs['sellers'][0]; vehicle=catalogs['vehicles'][0]
    prospect={'name':'Integración HTTP','email':f'integration-{run_id}@test.pe','phone':'900000000',
      'vehicle_interest':f"{vehicle['brand']} {vehicle['model']}",'seller_id':seller['id']}
    status,created=request_json(urls['prospects']+'/prospects','POST',prospect)
    assert_status(status,201,'crear prospecto'); prospect_id=created['id']
    print('✓ prospecto creado')

    for stage in ('qualification','negotiation'):
        status,updated=request_json(urls['prospects']+f'/prospects/{prospect_id}','PATCH',{'stage':stage})
        assert_status(status,200,f'avanzar a {stage}')
        if updated['stage']!=stage: raise AssertionError(f'no se guardó la etapa {stage}')
    print('✓ etapas actualizadas')

    sale={'prospect_id':prospect_id,'vehicle_id':vehicle['id'],'seller_id':seller['id'],
      'amount':vehicle['price'],'status':'completed'}
    status,created_sale=request_json(urls['sales']+'/sales','POST',sale)
    assert_status(status,201,'crear venta')
    print('✓ venta efectiva registrada')

    policy={'sale_id':created_sale['id'],'type':'Todo riesgo','expected_premium':1200,
      'actual_premium':1150,'status':'sold'}
    status,_=request_json(urls['insurance']+'/insurance','POST',policy)
    assert_status(status,201,'crear seguro')
    print('✓ seguro vendido vinculado')

    _,metrics=request_json(urls['dashboard']+'/api/metrics')
    if metrics['completed_sales'] < 1 or metrics['sold_insurance'] < 1:
        raise AssertionError('el dashboard no consolidó la venta y el seguro')
    _,seller_conversion=request_json(urls['sales']+'/sales/conversion')
    _,stage_conversion=request_json(urls['sales']+'/sales/conversion/stages')
    if not seller_conversion or stage_conversion[-1]['reached'] < 1:
        raise AssertionError('las métricas de conversión no reflejan el recorrido')
    print('✓ métricas consolidadas')

    status,cleaned=request_json(urls['dashboard']+'/api/testing/cleanup','POST',{'scope':'integration'})
    assert_status(status,200,'limpieza de integración')
    if cleaned['deleted_prospects'] < 1: raise AssertionError('no se limpiaron los datos de integración')
    print('✓ datos temporales eliminados')

def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0)); return sock.getsockname()[1]

def self_contained_urls():
    return {name:f'http://127.0.0.1:{free_port()}' for name in SERVICES}

def run_self_contained():
    urls=self_contained_urls(); processes=[]
    with tempfile.TemporaryDirectory(prefix='autopulse-integration-') as temp_dir:
        common=os.environ.copy(); common['DATABASE_PATH']=str(Path(temp_dir)/'integration.db'); common['PYTHONPATH']=str(ROOT)
        try:
            for name in SERVICES:
                env=common.copy(); env['PORT']=urls[name].rsplit(':',1)[1]
                processes.append(subprocess.Popen([sys.executable,'-m',MODULES[name]],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
            deadline=time.monotonic()+10
            while time.monotonic()<deadline:
                try:
                    if all(request_json(url+'/health')[0]==200 for url in urls.values()): break
                except Exception: time.sleep(.1)
            else: raise RuntimeError('los servicios no iniciaron dentro de 10 segundos')
            run_checks(urls)
        finally:
            for process in processes: process.terminate()
            for process in processes:
                try: process.wait(timeout=3)
                except subprocess.TimeoutExpired: process.kill()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--self-contained',action='store_true',help='levanta servicios temporales para una prueba aislada')
    args=parser.parse_args()
    if args.self_contained: run_self_contained()
    else:
        run_checks({'prospects':'http://localhost:8001','sales':'http://localhost:8002','insurance':'http://localhost:8003','dashboard':'http://localhost:8004'})
    print('\nIntegración lista: recorrido comercial completo verificado.')
    return 0

if __name__=='__main__':
    try: sys.exit(main())
    except Exception as exc:
        print(f'\n✗ Integración fallida: {exc}',file=sys.stderr); sys.exit(1)
