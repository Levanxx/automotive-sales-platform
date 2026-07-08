import json
from pathlib import Path
from shared.db import LOCK,connect,initialize,query,execute
from shared.http import Handler,serve,required
class Dashboard(Handler):
    def do_GET(self):
        if self.path in ('/','/index.html'):
            data=(Path(__file__).parent/'index.html').read_bytes(); return self._send(200,data,'text/html; charset=utf-8')
        super().do_GET()
def metrics(h):
    totals=query("SELECT COUNT(*) total, SUM(CASE WHEN stage!='closed' THEN 1 ELSE 0 END) active, SUM(CASE WHEN outcome='won' THEN 1 ELSE 0 END) won, SUM(CASE WHEN outcome='lost' THEN 1 ELSE 0 END) lost FROM prospects",one=True)
    insurance=query("SELECT COUNT(*) linked, SUM(CASE WHEN status='sold' THEN 1 ELSE 0 END) sold FROM insurance",one=True)
    funnel=query("SELECT stage,COUNT(*) count FROM prospects GROUP BY stage ORDER BY CASE stage WHEN 'initial' THEN 1 WHEN 'qualification' THEN 2 WHEN 'negotiation' THEN 3 ELSE 4 END")
    total=totals['total'] or 0
    return 200,{'total_prospects':total,'active_prospects':totals['active'] or 0,'completed_sales':totals['won'] or 0,'failed_sales':totals['lost'] or 0,'conversion_rate':round(100*(totals['won'] or 0)/total,2) if total else 0,'linked_insurance':insurance['linked'] or 0,'sold_insurance':insurance['sold'] or 0,'funnel':[dict(x,conversion=round(100*x['count']/total,2) if total else 0) for x in funnel]}
def catalogs(h):
    return 200,{'sellers':query('SELECT * FROM sellers ORDER BY name'),'vehicles':query('SELECT * FROM vehicles ORDER BY brand,model')}
def performance(h):
    return 200,query('SELECT * FROM performance_runs ORDER BY id DESC LIMIT 20')
def save_performance(h):
    d=h._body(); required(d,'concurrency','requests','success','error_rate_percent','duration_seconds','avg_ms','p95_ms','max_ms','acceptance_p95_under_2000ms')
    rid=execute('INSERT INTO performance_runs(concurrency,requests,success,error_rate_percent,duration_seconds,avg_ms,p95_ms,max_ms,acceptance) VALUES(?,?,?,?,?,?,?,?,?)',(d['concurrency'],d['requests'],d['success'],d['error_rate_percent'],d['duration_seconds'],d['avg_ms'],d['p95_ms'],d['max_ms'],1 if d['acceptance_p95_under_2000ms'] else 0))
    return 201,query('SELECT * FROM performance_runs WHERE id=?',(rid,),one=True)
def save_alert(h):
    d=h._body(); required(d,'event','message')
    rid=execute('INSERT INTO automation_alerts(event,message,payload) VALUES(?,?,?)',(d['event'],d['message'],json.dumps(d,ensure_ascii=False)))
    return 201,{'id':rid,'received':True}
def cleanup_load_data(h):
    with LOCK,connect() as conn:
        count=conn.execute("SELECT COUNT(*) FROM prospects WHERE email LIKE 'load%@test.pe'").fetchone()[0]
        conn.execute("DELETE FROM sales WHERE prospect_id IN (SELECT id FROM prospects WHERE email LIKE 'load%@test.pe')")
        conn.execute("DELETE FROM prospects WHERE email LIKE 'load%@test.pe'"); conn.commit()
    return 200,{'deleted_prospects':count}
Dashboard.routes={('GET','/api/metrics'):metrics,('GET','/api/catalogs'):catalogs,('GET','/api/performance'):performance,('POST','/api/performance'):save_performance,('POST','/api/alerts'):save_alert,('POST','/api/testing/cleanup'):cleanup_load_data}
if __name__=='__main__': initialize(); serve(Dashboard,8004)
