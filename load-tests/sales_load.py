import argparse, json, statistics, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen

def prepare(base,i):
    prospect={'name':f'Carga {i}','email':f'load{i}-{time.time_ns()}@test.pe','phone':'900000000','vehicle_interest':'Toyota Corolla','seller_id':1}
    req=Request(base.replace(':8002',':8001')+'/prospects',json.dumps(prospect).encode(),{'Content-Type':'application/json'},method='POST')
    with urlopen(req,timeout=30) as r: return json.load(r)['id']
def post(base,pid):
    sale={'prospect_id':pid,'vehicle_id':(pid % 3) + 1,'seller_id':1,'amount':24990,'status':'completed'}
    t=time.perf_counter()
    req=Request(base+'/sales',json.dumps(sale).encode(),{'Content-Type':'application/json'},method='POST')
    with urlopen(req,timeout=30) as r: status=r.status
    return status,(time.perf_counter()-t)*1000
def main():
    p=argparse.ArgumentParser(); p.add_argument('--concurrency',type=int,choices=[50,100],required=True); p.add_argument('--url',default='http://localhost:8002'); a=p.parse_args()
    print(f'Preparando {a.concurrency} prospectos fuera de la medición…')
    prospects=[prepare(a.url,i) for i in range(a.concurrency)]
    started=time.perf_counter(); results=[]
    with ThreadPoolExecutor(max_workers=a.concurrency) as ex:
        futures=[ex.submit(post,a.url,pid) for pid in prospects]
        for f in as_completed(futures):
            try: results.append(f.result())
            except Exception: results.append((0,10000))
    times=[x[1] for x in results]; ok=sum(x[0]==201 for x in results); ordered=sorted(times)
    report={'concurrency':a.concurrency,'requests':len(results),'success':ok,'error_rate_percent':round(100*(len(results)-ok)/len(results),2),'duration_seconds':round(time.perf_counter()-started,3),'avg_ms':round(statistics.mean(times),2),'p95_ms':round(ordered[max(0,int(len(ordered)*.95)-1)],2),'max_ms':round(max(times),2),'acceptance_p95_under_2000ms':ordered[max(0,int(len(ordered)*.95)-1)]<2000}
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
