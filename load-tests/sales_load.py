import argparse, json, statistics, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen

def post(base,i):
    prospect={'name':f'Carga {i}','email':f'load{i}-{time.time_ns()}@test.pe','phone':'900000000','vehicle_interest':'Toyota Corolla','seller_id':1}
    t=time.perf_counter(); req=Request(base.replace(':8002',':8001')+'/prospects',json.dumps(prospect).encode(),{'Content-Type':'application/json'},method='POST')
    with urlopen(req,timeout=10) as r: pid=json.load(r)['id']
    sale={'prospect_id':pid,'vehicle_id':1,'seller_id':1,'amount':24990,'status':'completed'}
    req=Request(base+'/sales',json.dumps(sale).encode(),{'Content-Type':'application/json'},method='POST')
    with urlopen(req,timeout=10) as r: status=r.status
    return status,(time.perf_counter()-t)*1000
def main():
    p=argparse.ArgumentParser(); p.add_argument('--concurrency',type=int,choices=[50,100],required=True); p.add_argument('--url',default='http://localhost:8002'); a=p.parse_args()
    started=time.perf_counter(); results=[]
    with ThreadPoolExecutor(max_workers=a.concurrency) as ex:
        futures=[ex.submit(post,a.url,i) for i in range(a.concurrency)]
        for f in as_completed(futures):
            try: results.append(f.result())
            except Exception: results.append((0,10000))
    times=[x[1] for x in results]; ok=sum(x[0]==201 for x in results); ordered=sorted(times)
    report={'concurrency':a.concurrency,'requests':len(results),'success':ok,'error_rate_percent':round(100*(len(results)-ok)/len(results),2),'duration_seconds':round(time.perf_counter()-started,3),'avg_ms':round(statistics.mean(times),2),'p95_ms':round(ordered[max(0,int(len(ordered)*.95)-1)],2),'max_ms':round(max(times),2),'acceptance_p95_under_2000ms':ordered[max(0,int(len(ordered)*.95)-1)]<2000}
    print(json.dumps(report,indent=2))
if __name__=='__main__': main()

