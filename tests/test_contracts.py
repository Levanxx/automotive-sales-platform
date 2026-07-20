import io, json, os, tempfile, unittest
from pathlib import Path

DB=tempfile.NamedTemporaryFile(delete=False); DB.close(); os.environ['DATABASE_PATH']=DB.name
from shared.db import initialize, query, execute
from shared.http import APIError, Handler, match_path, required
from services.prospects.app import inactive, get_one, list_all as prospects_list
from services.sales.app import list_all as sales_list
from services.insurance.app import list_all as insurance_list
from services.dashboard.app import catalogs, cleanup_load_data, performance, save_alert, save_performance

class Fake:
    def __init__(self,data=None,headers=None): self.data=data or {}; self.headers=headers or {}
    def _body(self): return self.data

class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): initialize()
    def test_path_matching(self):
        self.assertEqual(match_path('/prospects/{id}','/prospects/42'),{'id':'42'})
        self.assertIsNone(match_path('/sales/{id}','/prospects/42'))
        self.assertIsNone(match_path('/sales','/sales/1'))
    def test_required(self):
        required({'name':'ok'},'name')
        with self.assertRaises(APIError): required({},'name','email')
    def test_catalogs(self):
        status,data=catalogs(Fake()); self.assertEqual(status,200)
        self.assertGreaterEqual(len(data['sellers']),2); self.assertGreaterEqual(len(data['vehicles']),3)
    def test_stage_history_backfill(self):
        execute("INSERT INTO prospects(name,email,phone,vehicle_interest,stage,seller_id) VALUES('Historial','history@x.pe','1','Auto','negotiation',1)")
        initialize()
        stages={x['stage'] for x in query("SELECT stage FROM prospect_stage_history WHERE prospect_id=(SELECT id FROM prospects WHERE email='history@x.pe')")}
        self.assertEqual(stages,{'initial','negotiation'})
    def test_performance_storage(self):
        payload={'concurrency':100,'requests':100,'success':100,'error_rate_percent':0,'duration_seconds':1.2,'avg_ms':200,'p95_ms':450,'max_ms':500,'acceptance_p95_under_2000ms':True}
        self.assertEqual(save_performance(Fake(payload))[0],201)
        rows=performance(Fake())[1]; self.assertEqual(rows[0]['concurrency'],100); self.assertEqual(rows[0]['acceptance'],1)
    def test_automation_alert_receiver(self):
        status,data=save_alert(Fake({'event':'inactive_prospect','message':'Prospecto inactivo'}))
        self.assertEqual(status,201); self.assertTrue(data['received'])
    def test_load_cleanup(self):
        execute("INSERT INTO prospects(name,email,phone,vehicle_interest,stage,seller_id) VALUES('Load','load-clean@test.pe','1','Auto','initial',1)")
        status,data=cleanup_load_data(Fake()); self.assertEqual(status,200); self.assertGreaterEqual(data['deleted_prospects'],1)
    def test_list_queries_and_not_found(self):
        self.assertEqual(prospects_list(Fake())[0],200); self.assertEqual(sales_list(Fake())[0],200); self.assertEqual(insurance_list(Fake())[0],200)
        with self.assertRaises(APIError): get_one(Fake(),'999999')
    def test_inactive_contract(self):
        execute("INSERT INTO prospects(name,email,phone,vehicle_interest,stage,seller_id,last_activity) VALUES('Inactivo','i@x.pe','1','Auto','initial',1,'2020-01-01')")
        result=inactive(Fake(headers={'X-Inactivity-Days':'3'}))[1]
        self.assertTrue(any(x['name']=='Inactivo' for x in result))
        with self.assertRaises(APIError): inactive(Fake(headers={'X-Inactivity-Days':'no'}))
        with self.assertRaises(APIError): inactive(Fake(headers={'X-Inactivity-Days':'0'}))
    def test_n8n_workflows_are_importable(self):
        root=Path(__file__).parents[1]/'n8n'
        for path in root.glob('*.json'):
            workflow=json.loads(path.read_text())
            self.assertTrue(workflow['name']); self.assertGreaterEqual(len(workflow['nodes']),3)
            self.assertIn('connections',workflow)

    def test_handler_body_and_send(self):
        h=object.__new__(Handler); h.headers={'Content-Length':'7'}; h.rfile=io.BytesIO(b'{"a":1}')
        self.assertEqual(h._body(),{'a':1})
        h.headers={'Content-Length':'1'}; h.rfile=io.BytesIO(b'{')
        with self.assertRaises(APIError): h._body()
        sent=[]; h.wfile=io.BytesIO(); h.send_response=lambda s:sent.append(s); h.send_header=lambda *x:None; h.end_headers=lambda:None
        h._send(200,{'ok':True}); self.assertEqual(sent,[200]); self.assertIn(b'"ok": true',h.wfile.getvalue())

    def test_handler_dispatch_paths(self):
        class Demo(Handler): pass
        Demo.routes={('GET','/ok'):lambda h:(200,{'ok':1}),('GET','/bad'):lambda h:(_ for _ in ()).throw(APIError(422,'bad')),('GET','/boom'):lambda h:1/0}
        h=object.__new__(Demo); captured=[]; h._send=lambda *x:captured.append(x)
        for path in ('/health','/ok','/missing','/bad','/boom'):
            h.path=path; h._dispatch('GET')
        self.assertEqual([x[0] for x in captured],[200,200,404,422,500])

    def test_handler_verbs(self):
        h=object.__new__(Handler); calls=[]; h._dispatch=lambda x:calls.append(x); h._send=lambda *x:calls.append(x[0])
        h.do_GET(); h.do_POST(); h.do_PATCH(); h.do_OPTIONS(); h.log_message('x')
        self.assertEqual(calls,['GET','POST','PATCH',204])

if __name__=='__main__': unittest.main()
