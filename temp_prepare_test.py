import json, time
from urllib.request import Request, urlopen

# Simulate what the load test does
base1 = 'http://localhost:8001'
base2 = 'http://localhost:8002'

# Create 5 prospects sequentially
prospects = []
print('Creating prospects...')
for i in range(5):
    d = {'name': f'Carga {i}', 'email': f'load{i}-{time.time_ns()}@test.pe', 'phone': '900000000', 'vehicle_interest': 'Toyota Corolla', 'seller_id': 1}
    req = Request(base1 + '/prospects', json.dumps(d).encode(), {'Content-Type': 'application/json'}, method='POST')
    with urlopen(req, timeout=10) as r:
        pid = json.load(r)['id']
        prospects.append(pid)
        print(f'  {i}: id={pid}')

print(f'Created {len(prospects)} prospects. Now firing sales...')
for pid in prospects:
    sale = {'prospect_id': pid, 'vehicle_id': 1, 'seller_id': 1, 'amount': 24990, 'status': 'completed'}
    req = Request(base2 + '/sales', json.dumps(sale).encode(), {'Content-Type': 'application/json'}, method='POST')
    t = time.perf_counter()
    with urlopen(req, timeout=10) as r:
        ms = (time.perf_counter() - t) * 1000
        print(f'  Sale for prospect {pid}: {r.status} in {ms:.2f}ms')

print('Done')
