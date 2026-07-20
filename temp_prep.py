import time, json
from urllib.request import Request, urlopen

base = 'http://localhost:8001'
for i in range(50):
    prospect = {'name':'Prep'+str(i),'email':'prep'+str(i)+'-'+str(time.time_ns())+'@test.pe','phone':'900000000','seller_id':1}
    req = Request(base+'/prospects', json.dumps(prospect).encode(), {'Content-Type':'application/json'}, method='POST')
    with urlopen(req, timeout=30) as r:
        pid = json.load(r)['id']
    print('Created:' + str(pid))
print('ALL 50 DONE')
