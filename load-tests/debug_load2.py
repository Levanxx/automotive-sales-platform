import json, time, sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError

base = 'http://localhost:8002'

# Create one prospect
p = {'name': 'DebugX', 'email': 'debugx'+str(time.time_ns())+'@test.pe', 'phone': '900000000', 'seller_id': 1}
req = Request(base.replace(':8002', ':8001') + '/prospects', json.dumps(p).encode(), {'Content-Type': 'application/json'}, method='POST')
with urlopen(req, timeout=10) as r:
    pid = json.load(r)['id']
print('Prospect:', pid)

# Try sale with vehicle_id = (pid % 3) + 1
vid = (pid % 3) + 1
print(f'Using vehicle_id={vid}')
sale = {'prospect_id': pid, 'vehicle_id': vid, 'seller_id': 1, 'amount': 24990, 'status': 'completed'}
req = Request(base + '/sales', json.dumps(sale).encode(), {'Content-Type': 'application/json'}, method='POST')
try:
    with urlopen(req, timeout=10) as r:
        print('OK:', r.status, r.read())
except HTTPError as e:
    print('Error:', e.code, e.read())
except Exception as e:
    print('Timeout:', type(e).__name__)
