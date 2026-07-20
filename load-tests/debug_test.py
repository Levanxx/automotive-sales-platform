import json, time, sys
from urllib.request import Request, urlopen

base1 = 'http://localhost:8001'
base2 = 'http://localhost:8002'

print('Step 1: Creating prospect...')
sys.stdout.flush()
prospect = {'name': 'Debug1', 'email': f'debug1-{time.time_ns()}@test.pe', 'phone': '900000000', 'vehicle_interest': 'Toyota Corolla', 'seller_id': 1}
req = Request(base1 + '/prospects', json.dumps(prospect).encode(), {'Content-Type': 'application/json'}, method='POST')
with urlopen(req, timeout=5) as r:
    pid = json.load(r)['id']
    print(f'  OK - Prospect id={pid}')

print('Step 2: Creating sale...')
sys.stdout.flush()
sale = {'prospect_id': pid, 'vehicle_id': 1, 'seller_id': 1, 'amount': 24990, 'status': 'completed'}
req = Request(base2 + '/sales', json.dumps(sale).encode(), {'Content-Type': 'application/json'}, method='POST')
with urlopen(req, timeout=5) as r:
    print(f'  OK - Sale status={r.status}')

print('Done!')
