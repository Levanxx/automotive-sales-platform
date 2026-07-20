"""Ejecuta los escenarios de 50 y 100 ventas en servicios temporales aislados."""
import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

ROOT=Path(__file__).parents[1]
MODULES=('prospects','sales','dashboard')

def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0)); return sock.getsockname()[1]

def wait_for_services(urls):
    deadline=time.monotonic()+10
    while time.monotonic()<deadline:
        try:
            if all(json.load(urlopen(url+'/health',timeout=1)).get('status')=='ok' for url in urls.values()): return
        except Exception: time.sleep(.1)
    raise RuntimeError('los servicios de carga no iniciaron dentro de 10 segundos')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--scenario',type=int,choices=[50,100],action='append',help='escenario a ejecutar; por defecto ejecuta ambos')
    parser.add_argument('--output-dir',type=Path,help='directorio opcional para reportes JSON')
    args=parser.parse_args(); scenarios=args.scenario or [50,100]
    urls={name:f'http://127.0.0.1:{free_port()}' for name in MODULES}; processes=[]
    with tempfile.TemporaryDirectory(prefix='autopulse-stress-') as temp_dir:
        common=os.environ.copy(); common['DATABASE_PATH']=str(Path(temp_dir)/'stress.db'); common['PYTHONPATH']=str(ROOT)
        try:
            for name in MODULES:
                env=common.copy(); env['PORT']=urls[name].rsplit(':',1)[1]
                processes.append(subprocess.Popen([sys.executable,'-m',f'services.{name}.app'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
            wait_for_services(urls)
            for concurrency in scenarios:
                command=[sys.executable,str(ROOT/'load-tests'/'sales_load.py'),'--concurrency',str(concurrency),'--url',urls['sales'],'--prospects-url',urls['prospects'],'--dashboard-url',urls['dashboard']]
                for process in processes: command.extend(('--resource-pid',str(process.pid)))
                if args.output_dir: command.extend(('--output',str(args.output_dir/f'sales-{concurrency}.json')))
                print(f'\nEscenario: {concurrency} ventas simultáneas',flush=True)
                subprocess.run(command,cwd=ROOT,check=True)
        finally:
            for process in processes: process.terminate()
            for process in processes:
                try: process.wait(timeout=3)
                except subprocess.TimeoutExpired: process.kill()
    return 0

if __name__=='__main__': sys.exit(main())
