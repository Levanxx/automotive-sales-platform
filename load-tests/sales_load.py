import argparse, json, os, re, statistics, subprocess, threading, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen

ROOT=Path(__file__).parents[1]

def memory_mb(value):
    match=re.match(r'([0-9.]+)\s*([KMGT]?i?B)',value.strip())
    if not match: return 0
    number=float(match.group(1)); unit=match.group(2)
    factors={'B':1/(1024**2),'KB':1/1024,'KiB':1/1024,'MB':1,'MiB':1,'GB':1024,'GiB':1024,'TB':1024**2,'TiB':1024**2}
    return number*factors.get(unit,0)

class ResourceSampler:
    def __init__(self,pids=None):
        self.pids=[int(x) for x in (pids or [])]; self.container_ids=[]; self.samples=[]; self.stop_event=threading.Event()
        self.source='processes' if self.pids else 'docker'
        if not self.pids:
            try:
                result=subprocess.run(['docker','compose','ps','-q','prospects','sales','dashboard'],cwd=ROOT,text=True,capture_output=True,timeout=5)
                self.container_ids=[x for x in result.stdout.splitlines() if x]
            except (OSError,subprocess.SubprocessError): self.container_ids=[]
        if not self.pids and not self.container_ids:
            self.pids=[os.getpid()]; self.source='load-client'
        self.thread=threading.Thread(target=self._run,daemon=True)
    def _process_sample(self):
        cpu=memory=0
        for pid in self.pids:
            try:
                result=subprocess.run(['ps','-o','%cpu=,rss=','-p',str(pid)],text=True,capture_output=True,timeout=2)
                values=result.stdout.split()
                if len(values)>=2: cpu+=float(values[0]); memory+=float(values[1])/1024
            except (OSError,ValueError,subprocess.SubprocessError): continue
        return cpu,memory
    def _docker_sample(self):
        try:
            result=subprocess.run(['docker','stats','--no-stream','--format','{{json .}}',*self.container_ids],text=True,capture_output=True,timeout=5)
            rows=[json.loads(line) for line in result.stdout.splitlines() if line]
            return sum(float(x['CPUPerc'].strip('%')) for x in rows),sum(memory_mb(x['MemUsage'].split('/')[0]) for x in rows)
        except (OSError,ValueError,KeyError,json.JSONDecodeError,subprocess.SubprocessError): return 0,0
    def _run(self):
        while not self.stop_event.is_set():
            cpu,memory=self._docker_sample() if self.container_ids else self._process_sample()
            self.samples.append((cpu,memory)); self.stop_event.wait(.05 if self.pids else .2)
    def start(self): self.thread.start()
    def stop(self):
        self.stop_event.set(); self.thread.join(timeout=6)
        if not self.samples: self.samples.append((0,0))
        return {'resource_source':self.source,'resource_samples':len(self.samples),
          'peak_cpu_percent':round(max(x[0] for x in self.samples),2),
          'peak_memory_mb':round(max(x[1] for x in self.samples),2)}

def prepare(base,i):
    prospect={'name':f'Carga {i}','email':f'load{i}-{time.time_ns()}@test.pe','phone':'900000000','vehicle_interest':'Toyota Corolla','seller_id':1}
    req=Request(base.replace(':8002',':8001')+'/prospects',json.dumps(prospect).encode(),{'Content-Type':'application/json'},method='POST')
    with urlopen(req,timeout=10) as r: return json.load(r)['id']
def post(base,pid):
    sale={'prospect_id':pid,'vehicle_id':1,'seller_id':1,'amount':24990,'status':'completed'}
    t=time.perf_counter()
    req=Request(base+'/sales',json.dumps(sale).encode(),{'Content-Type':'application/json'},method='POST')
    with urlopen(req,timeout=10) as r: status=r.status
    return status,(time.perf_counter()-t)*1000
def main():
    p=argparse.ArgumentParser(); p.add_argument('--concurrency',type=int,choices=[50,100],required=True); p.add_argument('--url',default='http://localhost:8002'); p.add_argument('--resource-pid',type=int,action='append',default=[],help='PID de servicio a medir; puede repetirse'); a=p.parse_args()
    print(f'Preparando {a.concurrency} prospectos fuera de la medición…')
    prospects=[prepare(a.url,i) for i in range(a.concurrency)]
    sampler=ResourceSampler(a.resource_pid); sampler.start(); started=time.perf_counter(); results=[]
    with ThreadPoolExecutor(max_workers=a.concurrency) as ex:
        futures=[ex.submit(post,a.url,pid) for pid in prospects]
        for f in as_completed(futures):
            try: results.append(f.result())
            except Exception: results.append((0,10000))
    duration=time.perf_counter()-started; resources=sampler.stop()
    times=[x[1] for x in results]; ok=sum(x[0]==201 for x in results); ordered=sorted(times)
    report={'concurrency':a.concurrency,'requests':len(results),'success':ok,'error_rate_percent':round(100*(len(results)-ok)/len(results),2),'duration_seconds':round(duration,3),'avg_ms':round(statistics.mean(times),2),'p95_ms':round(ordered[max(0,int(len(ordered)*.95)-1)],2),'max_ms':round(max(times),2),'acceptance_p95_under_2000ms':ordered[max(0,int(len(ordered)*.95)-1)]<2000,**resources}
    print(json.dumps(report,indent=2))
    try:
        req=Request(a.url.replace(':8002',':8004')+'/api/performance',json.dumps(report).encode(),{'Content-Type':'application/json'},method='POST')
        with urlopen(req,timeout=5): pass
        print('Resultado publicado en el dashboard de rendimiento.')
    except Exception as e: print('Aviso: no se pudo publicar el resultado:',e)
    try:
        req=Request(a.url.replace(':8002',':8004')+'/api/testing/cleanup',b'{}',{'Content-Type':'application/json'},method='POST')
        with urlopen(req,timeout=10) as response: cleaned=json.load(response)['deleted_prospects']
        print(f'Datos temporales eliminados: {cleaned} prospectos.')
    except Exception as e: print('Aviso: no se pudieron limpiar los datos temporales:',e)
if __name__=='__main__': main()
