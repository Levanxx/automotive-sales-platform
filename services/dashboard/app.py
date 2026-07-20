import json
import sqlite3
from pathlib import Path
from shared.db import LOCK,managed_connection,initialize,query,execute
from shared.http import Handler,APIError,serve,required,require_automation_key
class Dashboard(Handler):
    def do_GET(self):
        if self.path in ('/','/index.html'):
            data=(Path(__file__).parent/'index.html').read_bytes(); return self._send(200,data,'text/html; charset=utf-8')
        super().do_GET()
def metrics(h):
    with LOCK, managed_connection() as conn:
        totals=conn.execute("SELECT COUNT(*) total, SUM(CASE WHEN stage!='closed' THEN 1 ELSE 0 END) active, SUM(CASE WHEN outcome='won' THEN 1 ELSE 0 END) won, SUM(CASE WHEN outcome='lost' THEN 1 ELSE 0 END) lost FROM prospects").fetchone()
        insurance=conn.execute("SELECT COUNT(*) linked, SUM(CASE WHEN status='sold' THEN 1 ELSE 0 END) sold FROM insurance").fetchone()
        funnel_raw=conn.execute("SELECT stage,COUNT(*) count FROM prospects GROUP BY stage").fetchall()
        sales_amount=conn.execute("SELECT COALESCE(SUM(amount),0) total_amount FROM sales WHERE status='completed' AND strftime('%Y-%m',created_at)=strftime('%Y-%m','now')").fetchone()
    funnel_map={r['stage']:r['count'] for r in funnel_raw}
    total=totals['total'] or 1
    funnel=[{'stage':s,'count':funnel_map.get(s,0),'conversion':round(100*funnel_map.get(s,0)/total,2)} for s in ('initial','qualification','negotiation','closed')]
    won=totals['won'] or 0
    lost=totals['lost'] or 0
    total=totals['total'] or 0
    return 200,{'total_prospects':total,'active_prospects':totals['active'] or 0,'completed_sales':won,'failed_sales':lost,'conversion_rate':round(100*won/total,2) if total else 0,'linked_insurance':insurance['linked'] or 0,'sold_insurance':insurance['sold'] or 0,'ventas_del_mes':sales_amount['total_amount'] or 0,'funnel':funnel}

def catalogs(h):
    return 200,{'sellers':query('SELECT * FROM sellers ORDER BY name'),'vehicles':query('SELECT * FROM vehicles ORDER BY brand,model')}

def performance(h):
    return 200,query('SELECT * FROM performance_runs ORDER BY id DESC LIMIT 20')

def save_performance(h):
    d=h._body(); required(d,'concurrency','requests','success','error_rate_percent','duration_seconds','avg_ms','p95_ms','max_ms','acceptance_p95_under_2000ms')
    for field in ('resource_samples','peak_cpu_percent','peak_memory_mb'):
        if d.get(field) is not None and (isinstance(d[field],bool) or not isinstance(d[field],(int,float)) or d[field] < 0):
            return 400,{'error':f'{field} debe ser un número no negativo'}
    rid=execute('''INSERT INTO performance_runs(concurrency,requests,success,error_rate_percent,duration_seconds,avg_ms,p95_ms,max_ms,acceptance,resource_source,resource_samples,peak_cpu_percent,peak_memory_mb)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''',(d['concurrency'],d['requests'],d['success'],d['error_rate_percent'],d['duration_seconds'],d['avg_ms'],d['p95_ms'],d['max_ms'],1 if d['acceptance_p95_under_2000ms'] else 0,d.get('resource_source'),d.get('resource_samples'),d.get('peak_cpu_percent'),d.get('peak_memory_mb')))
    return 201,query('SELECT * FROM performance_runs WHERE id=?',(rid,),one=True)

def save_alert(h):
    require_automation_key(h)
    d=h._body(); required(d,'event','message')
    rid=execute('INSERT INTO automation_alerts(event,message,payload) VALUES(?,?,?)',(d['event'],d['message'],json.dumps(d,ensure_ascii=False)))
    return 201,{'id':rid,'received':True}

def list_alerts(h):
    require_automation_key(h)
    return 200,query('SELECT id,event,message,payload,created_at FROM automation_alerts ORDER BY id DESC LIMIT 100')

def cleanup_load_data(h):
    d=h._body(); scope=d.get('scope','load')
    if scope not in ('load','integration'): return 400,{'error':'Scope de limpieza inválido'}
    pattern="load%@test.pe" if scope=='load' else "integration-%@test.pe"
    with LOCK,managed_connection() as conn:
        count=conn.execute("SELECT COUNT(*) FROM prospects WHERE email LIKE ?",(pattern,)).fetchone()[0]
        vehicle_ids=[row[0] for row in conn.execute("SELECT DISTINCT s.vehicle_id FROM sales s JOIN prospects p ON p.id=s.prospect_id WHERE p.email LIKE ?",(pattern,))]
        conn.execute("DELETE FROM insurance WHERE sale_id IN (SELECT s.id FROM sales s JOIN prospects p ON p.id=s.prospect_id WHERE p.email LIKE ?)",(pattern,))
        conn.execute("DELETE FROM sales WHERE prospect_id IN (SELECT id FROM prospects WHERE email LIKE ?)",(pattern,))
        conn.execute("DELETE FROM prospects WHERE email LIKE ?",(pattern,))
        deleted_vehicles=0
        if scope == 'load':
            for vehicle_id in vehicle_ids:
                deleted_vehicles+=conn.execute("DELETE FROM vehicles WHERE id=? AND brand='Carga'",(vehicle_id,)).rowcount
    return 200,{'deleted_prospects':count,'deleted_vehicles':deleted_vehicles}
def create_vehicle(h):
    d=h._body(); required(d,'brand','model','year','price')
    try:
        year=int(d['year']); price=float(d['price'])
    except (TypeError,ValueError):
        raise APIError(400,'El año y el precio deben ser numéricos')
    if year < 1886 or year > 2100: raise APIError(400,'Año inválido')
    if price <= 0: raise APIError(400,'El precio debe ser mayor a cero')
    vid=execute('INSERT INTO vehicles(brand,model,year,price,imagen) VALUES(?,?,?,?,?)',(d['brand'],d['model'],year,price,d.get('imagen')))
    return 201,query('SELECT * FROM vehicles WHERE id=?',(vid,),one=True)

def create_seller(h):
    d=h._body(); required(d,'name','email')
    try: sid=execute('INSERT INTO sellers(name,email) VALUES(?,?)',(d['name'],d['email']))
    except sqlite3.IntegrityError: raise APIError(409,'El email ya está registrado')
    return 201,query('SELECT * FROM sellers WHERE id=?',(sid,),one=True)

def update_vehicle(h,id):
    d=h._body()
    row=query('SELECT * FROM vehicles WHERE id=?',(id,),one=True)
    if not row: raise APIError(404,'Vehículo no encontrado')
    brand=d.get('brand',row['brand'])
    model=d.get('model',row['model'])
    try:
        year=int(d.get('year',row['year']))
        price=float(d.get('price',row['price']))
    except (TypeError,ValueError):
        raise APIError(400,'El año y el precio deben ser numéricos')
    if year < 1886 or year > 2100: raise APIError(400,'Año inválido')
    if price <= 0: raise APIError(400,'El precio debe ser mayor a cero')
    imagen=d.get('imagen',row['imagen'])
    execute('UPDATE vehicles SET brand=?,model=?,year=?,price=?,imagen=? WHERE id=?',(brand,model,year,price,imagen,id))
    return 200,query('SELECT * FROM vehicles WHERE id=?',(id,),one=True)

def delete_vehicle(h,id):
    row=query('SELECT id FROM vehicles WHERE id=?',(id,),one=True)
    if not row: raise APIError(404,'Vehículo no encontrado')
    try: execute('DELETE FROM vehicles WHERE id=?',(id,))
    except sqlite3.IntegrityError: raise APIError(409,'No se puede eliminar un vehículo asociado a prospectos o ventas')
    return 200,{'deleted':True}

Dashboard.routes={('GET','/api/metrics'):metrics,('GET','/api/catalogs'):catalogs,('GET','/api/performance'):performance,('POST','/api/performance'):save_performance,('GET','/api/alerts'):list_alerts,('POST','/api/alerts'):save_alert,('POST','/api/testing/cleanup'):cleanup_load_data,('POST','/api/vehicles'):create_vehicle,('PATCH','/api/vehicles/{id}'):update_vehicle,('DELETE','/api/vehicles/{id}'):delete_vehicle,('POST','/api/sellers'):create_seller}
if __name__=='__main__': initialize(); serve(Dashboard,8004)
