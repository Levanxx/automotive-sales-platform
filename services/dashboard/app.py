from pathlib import Path
from shared.db import initialize,query
from shared.http import Handler,serve
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
Dashboard.routes={('GET','/api/metrics'):metrics}
if __name__=='__main__': initialize(); serve(Dashboard,8004)

