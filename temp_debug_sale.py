import time, json
from urllib.request import Request, urlopen
from urllib.error import HTTPError

p = {'name':'Debug','email':'deb' + str(time.time_ns()) + '@test.pe','phone':'999000000','seller_id':1}
req = Request('http://localhost:8001/prospects', json.dumps(p).encode(), {'Content-Type':'application/json'}, method='POST')
with urlopen(req, timeout=30) as r:
    pid = json.load(r)['id']
print('Created prospect: ' + str(pid))

t = time.perf_counter()
sale = {'prospect_id': pid, 'vehicle_id': 2, 'seller_id': 1, 'amount': 24990, 'status': 'completed'}
req = Request('http://localhost:8002/sales', json.dumps(sale).encode(), {'Content-Type':'application/json'}, method='POST')
try:
    with urlopen(req, timeout=30) as r:
        data = json.load(r)
        ms = (time.perf_counter()-t)*1000
        print('Sale OK: status=%d time=%.0fms id=%d' % (r.status, ms, data['id']))
except HTTPError as e:
    ms = (time.perf_counter()-t)*1000
    print('Sale FAIL: code=%d body=%s time=%.0fms' % (e.code, e.read().decode(), ms))
