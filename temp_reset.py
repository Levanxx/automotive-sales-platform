from shared.db import execute, query

# Clean up test data
execute('DELETE FROM sales WHERE prospect_id IN (SELECT id FROM prospects WHERE email LIKE ''load%@test.pe'' OR email LIKE ''ld@test.pe'')')
execute("UPDATE prospects SET stage='initial', outcome=NULL, loss_reason=NULL WHERE email='ld@test.pe'")
execute('UPDATE vehicles SET sold=0 WHERE id=1')

# Check state
p = query("SELECT id, stage FROM prospects WHERE email='ld@test.pe'", one=True)
print('Prospect state:', p)
v = query('SELECT id, sold FROM vehicles WHERE id=1', one=True)
print('Vehicle state:', v)

# Now test the sales endpoint
from urllib.request import Request, urlopen
import json
sale = json.dumps({'prospect_id': p['id'], 'vehicle_id': 1, 'seller_id': 1, 'amount': 24990, 'status': 'completed'}).encode()
req = Request('http://localhost:8002/sales', sale, {'Content-Type': 'application/json'}, method='POST')
try:
    with urlopen(req, timeout=10) as r:
        print('Sale created:', r.status, r.read())
except Exception as e:
    print('Error:', e.code, e.read())
