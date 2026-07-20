import json, time
from urllib.request import Request, urlopen

base = 'http://localhost:8001'

# Test single prospect creation with load test format
prospect = {'name': 'Carga 0', 'email': f'load0-{time.time_ns()}@test.pe', 'phone': '900000000', 'vehicle_interest': 'Toyota Corolla', 'seller_id': 1}
req = Request(base + '/prospects', json.dumps(prospect).encode(), {'Content-Type': 'application/json'}, method='POST')
print('Creating prospect...')
try:
    with urlopen(req, timeout=10) as r:
        data = json.load(r)
        pid = data['id']
        print(f'Created prospect id={pid}')
except Exception as e:
    print(f'Prospect error: {e}')

# Test single sale
print('Creating sale...')
base2 = 'http://localhost:8002'
sale = {'prospect_id': pid, 'vehicle_id': 1, 'seller_id': 1, 'amount': 24990, 'status': 'completed'}
req = Request(base2 + '/sales', json.dumps(sale).encode(), {'Content-Type': 'application/json'}, method='POST')
try:
    with urlopen(req, timeout=10) as r:
        print(f'Sale created: {r.status}')
except Exception as e:
    print(f'Sale error: {e.code} {e.read()}')

# Test cleanup
base4 = 'http://localhost:8004'
req = Request(base4 + '/api/testing/cleanup', b'{}', {'Content-Type': 'application/json'}, method='POST')
try:
    with urlopen(req, timeout=10) as r:
        print(f'Cleanup: {json.load(r)}')
except Exception as e:
    print(f'Cleanup error: {e}')
