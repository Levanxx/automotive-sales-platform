"""Comprueba que un backend público está listo para los workflows de n8n Cloud."""
import argparse
import json
import os
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

def request_json(url,method='GET',body=None,key='',extra_headers=None):
    data=None if body is None else json.dumps(body).encode()
    headers={'Content-Type':'application/json'}
    if key: headers['X-Automation-Key']=key
    headers.update(extra_headers or {})
    request=Request(url,data,headers,method=method)
    try:
        with urlopen(request,timeout=15) as response: return response.status,json.load(response)
    except HTTPError as exc:
        try: detail=json.load(exc)
        except Exception: detail={'error':str(exc)}
        raise RuntimeError(f'{method} {url}: HTTP {exc.code} {detail}') from exc

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--prospects-url',default=os.getenv('N8N_PROSPECTS_URL','http://localhost:8001'))
    parser.add_argument('--sales-url',default=os.getenv('N8N_SALES_URL','http://localhost:8002'))
    parser.add_argument('--insurance-url',default=os.getenv('N8N_INSURANCE_URL','http://localhost:8003'))
    parser.add_argument('--dashboard-url',default=os.getenv('N8N_DASHBOARD_URL','http://localhost:8004'))
    parser.add_argument('--key',default=os.getenv('N8N_AUTOMATION_KEY',''))
    parser.add_argument('--inactivity-days',type=int,default=3)
    args=parser.parse_args()
    urls={'prospects':args.prospects_url.rstrip('/'),'sales':args.sales_url.rstrip('/'),'insurance':args.insurance_url.rstrip('/'),'dashboard':args.dashboard_url.rstrip('/')}
    for name,url in urls.items():
        status,data=request_json(url+'/health',key=args.key)
        if status!=200 or data.get('status')!='ok': raise RuntimeError(f'{name} no está saludable')
        print('✓ salud',name)
    _,inactive=request_json(urls['prospects']+'/prospects/inactive',key=args.key,extra_headers={'X-Inactivity-Days':str(args.inactivity_days)})
    print(f'✓ consulta de inactividad: {len(inactive)} prospectos')
    _,metrics=request_json(urls['dashboard']+'/api/metrics',key=args.key)
    if 'total_prospects' not in metrics: raise RuntimeError('respuesta de métricas incompleta')
    print('✓ métricas comerciales')
    payload={'event':'n8n_smoke_test','message':'Conectividad n8n Cloud verificada','source':'scripts/n8n_cloud_smoke_check.py'}
    status,created=request_json(urls['dashboard']+'/api/alerts','POST',payload,args.key)
    if status!=201: raise RuntimeError('no se pudo registrar alerta de prueba')
    _,alerts=request_json(urls['dashboard']+'/api/alerts',key=args.key)
    if not any(row['id']==created['id'] and row['event']=='n8n_smoke_test' for row in alerts):
        raise RuntimeError('la alerta de prueba no se recuperó')
    print('✓ escritura y lectura de alertas autenticadas')
    print('\nBackend listo para importar y ejecutar workflows en n8n Cloud.')
    return 0

if __name__=='__main__':
    try: sys.exit(main())
    except Exception as exc:
        print(f'\n✗ Comprobación n8n fallida: {exc}',file=sys.stderr); sys.exit(1)
