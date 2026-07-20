import json
from pathlib import Path
from shared.db import LOCK,connect,initialize,query,execute
from shared.http import Handler,APIError,serve,required
class Dashboard(Handler):
    def do_GET(self):
        if self.path in ('/','/index.html'):
            data=(Path(__file__).parent/'index.html').read_bytes(); return self._send(200,data,'text/html; charset=utf-8')
        super().do_GET()
def metrics(h):
    with LOCK, connect() as conn:
        totals=conn.execute("SELECT COUNT(*) total, SUM(CASE WHEN stage!='closed' THEN 1 ELSE 0 END) active, SUM(CASE WHEN outcome='won' THEN 1 ELSE 0 END) won, SUM(CASE WHEN outcome='lost' THEN 1 ELSE 0 END) lost FROM prospects").fetchone()
        insurance=conn.execute("SELECT COUNT(*) linked, SUM(CASE WHEN status='sold' THEN 1 ELSE 0 END) sold FROM insurance").fetchone()
        funnel_raw=conn.execute("SELECT stage,COUNT(*) count FROM prospects GROUP BY stage").fetchall()
        sales_amount=conn.execute("SELECT COALESCE(SUM(amount),0) total_amount FROM sales WHERE status='completed'").fetchone()
    funnel_map={r['stage']:r['count'] for r in funnel_raw}
    total=totals['total'] or 1
    funnel=[{'stage':s,'count':funnel_map.get(s,0),'conversion':round(100*funnel_map.get(s,0)/total,2)} for s in ('initial','qualification','negotiation','closed')]
    won=totals['won'] or 0
    lost=totals['lost'] or 0
    total_closed=won+lost
    return 200,{'total_prospects':totals['total'] or 0,'active_prospects':totals['active'] or 0,'completed_sales':won,'failed_sales':lost,'conversion_rate':round(100*won/total_closed,2) if total_closed else 0,'linked_insurance':insurance['linked'] or 0,'sold_insurance':insurance['sold'] or 0,'ventas_del_mes':sales_amount['total_amount'] or 0,'funnel':funnel}

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
        count=conn.execute("SELECT COUNT(*) FROM prospects WHERE email LIKE 'load%@test.pe'").fetchone()['count']
        conn.execute("DELETE FROM sales WHERE prospect_id IN (SELECT id FROM prospects WHERE email LIKE 'load%@test.pe')")
        conn.execute("DELETE FROM prospects WHERE email LIKE 'load%@test.pe'"); conn.commit()
    return 200,{'deleted_prospects':count}

def create_vehicle(h):
    d=h._body(); required(d,'brand','model','year','price')
    year_val = int(d['year'])
    if year_val < 1900 or year_val > 2100:
        raise APIError(400, 'Año inválido: debe estar entre 1900 y 2100')
    price_val = float(d['price'])
    if price_val <= 0:
        raise APIError(400, 'Precio inválido: debe ser mayor a cero')
    vid=execute('INSERT INTO vehicles(brand,model,year,price,imagen) VALUES(?,?,?,?,?)',(d['brand'],d['model'],year_val,price_val,d.get('imagen')))
    return 201,query('SELECT * FROM vehicles WHERE id=?',(vid,),one=True)

def create_seller(h):
    d=h._body(); required(d,'name','email')
    try: sid=execute('INSERT INTO sellers(name,email) VALUES(?,?)',(d['name'],d['email']))
    except Exception: raise APIError(409,'El email ya está registrado')
    return 201,query('SELECT * FROM sellers WHERE id=?',(sid,),one=True)

def update_vehicle(h,id):
    d=h._body()
    row=query('SELECT * FROM vehicles WHERE id=?',(id,),one=True)
    if not row: raise APIError(404,'Vehículo no encontrado')
    brand=d.get('brand',row['brand'])
    model=d.get('model',row['model'])
    year=int(d.get('year',row['year']))
    price=float(d.get('price',row['price']))
    imagen=d.get('imagen',row['imagen'])
    execute('UPDATE vehicles SET brand=?,model=?,year=?,price=?,imagen=? WHERE id=?',(brand,model,year,price,imagen,id))
    return 200,query('SELECT * FROM vehicles WHERE id=?',(id,),one=True)

def delete_vehicle(h,id):
    row=query('SELECT id FROM vehicles WHERE id=?',(id,),one=True)
    if not row: raise APIError(404,'Vehículo no encontrado')
    execute('DELETE FROM vehicles WHERE id=?',(id,))
    return 200,{'deleted':True}

Dashboard.routes={('GET','/api/metrics'):metrics,('GET','/api/catalogs'):catalogs,('GET','/api/performance'):performance,('POST','/api/performance'):save_performance,('POST','/api/alerts'):save_alert,('POST','/api/testing/cleanup'):cleanup_load_data,('POST','/api/vehicles'):create_vehicle,('PATCH','/api/vehicles/{id}'):update_vehicle,('DELETE','/api/vehicles/{id}'):delete_vehicle,('POST','/api/sellers'):create_seller}
if __name__=='__main__': initialize(); serve(Dashboard,8004)
