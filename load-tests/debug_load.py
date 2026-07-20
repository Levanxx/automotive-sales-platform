import json, time, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen

concurrency = 5
base = 'http://localhost:8002'

print(f'Creating {concurrency} prospects...')
sys.stdout.flush()
prospects = []
for i in range(concurrency):
    prospect = {'name': f'Carga {i}', 'email': f'load{i}-{time.time_ns()}@test.pe', 'phone': '900000000', 'seller_id': 1}
    req = Request(base.replace(':8002', ':8001') + '/prospects', json.dumps(prospect).encode(), {'Content-Type': 'application/json'}, method='POST')
    with urlopen(req, timeout=10) as r:
        pid = json.load(r)['id']
        prospects.append(pid)
        print(f'  {i}: id={pid}')
        sys.stdout.flush()

print(f'Firing {concurrency} concurrent sales...')
sys.stdout.flush()
started = time.perf_counter()
results = []

def post(pid):
    sale = {'prospect_id': pid, 'vehicle_id': 1, 'seller_id': 1, 'amount': 24990, 'status': 'completed'}
    t = time.perf_counter()
    req = Request(base + '/sales', json.dumps(sale).encode(), {'Content-Type': 'application/json'}, method='POST')
    try:
        with urlopen(req, timeout=10) as r:
            status = r.status
        return status, (time.perf_counter() - t) * 1000
    except Exception as e:
        print(f'  Sale failed for {pid}: {e}')
        return 0, 10000

with ThreadPoolExecutor(max_workers=concurrency) as ex:
    futures = [ex.submit(post, pid) for pid in prospects]
    for f in as_completed(futures):
        try:
            results.append(f.result())
        except Exception as e:
            print(f'Future error: {e}')
            results.append((0, 10000))

times = [x[1] for x in results]
ok = sum(x[0] == 201 for x in results)
ordered = sorted(times)
report = {
    'concurrency': concurrency,
    'requests': len(results),
    'success': ok,
    'error_rate_percent': round(100 * (len(results) - ok) / len(results), 2),
    'duration_seconds': round(time.perf_counter() - started, 3),
    'avg_ms': round(sum(times) / len(times), 2),
    'p95_ms': round(ordered[max(0, int(len(ordered) * .95) - 1)], 2),
    'max_ms': round(max(times), 2),
}
print(json.dumps(report, indent=2))
