from shared.db import LOCK, managed_connection, initialize, query, execute
from shared.http import Handler, APIError, required, serve

STAGES=('initial','qualification','negotiation','closed')
class Prospects(Handler): pass

def list_all(h): return 200, query('SELECT p.*,s.name seller_name FROM prospects p JOIN sellers s ON s.id=p.seller_id ORDER BY p.id DESC')

def get_one(h,id):
    item=query('SELECT * FROM prospects WHERE id=?',(id,),one=True)
    if not item: raise APIError(404,'Prospecto no encontrado')
    return 200,item

def create(h):
    d=h._body(); required(d,'name','email','phone','vehicle_interest','seller_id')

    seller = query('SELECT id FROM sellers WHERE id=?', (d['seller_id'],), one=True)
    if not seller: raise APIError(400, 'Vendedor no encontrado')

    stage=d.get('stage','initial')
    if stage not in STAGES: raise APIError(400,'Etapa inválida')
    with LOCK,managed_connection() as conn:
        cur=conn.execute('INSERT INTO prospects(name,email,phone,vehicle_interest,stage,seller_id) VALUES(?,?,?,?,?,?)',(d['name'],d['email'],d['phone'],d['vehicle_interest'],stage,d['seller_id']))
        pid=cur.lastrowid
        conn.execute('INSERT INTO prospect_stage_history(prospect_id,stage) VALUES(?,?)',(pid,'initial'))
        if stage!='initial': conn.execute('INSERT INTO prospect_stage_history(prospect_id,stage) VALUES(?,?)',(pid,stage))
        conn.commit()
    return 201,query('SELECT * FROM prospects WHERE id=?',(pid,),one=True)

def update(h, id):
    d = h._body()
    item = query('SELECT * FROM prospects WHERE id=?', (id,), one=True)
    if not item: raise APIError(404, 'Prospecto no encontrado')
    stage = d.get('stage', item['stage'])
    if stage not in STAGES: raise APIError(400, 'Etapa inválida')
    if item['stage'] == 'closed': raise APIError(409, 'El prospecto ya está cerrado')
    if stage == 'closed':
        raise APIError(400, 'El cierre se registra mediante una venta realizada o fallida')
    if 'outcome' in d or 'loss_reason' in d:
        raise APIError(400, 'El resultado y motivo se registran mediante el servicio de ventas')
    with LOCK,managed_connection() as conn:
        conn.execute("UPDATE prospects SET stage=?,last_activity=CURRENT_TIMESTAMP WHERE id=?", (stage, id))
        if stage!=item['stage']:
            conn.execute('INSERT OR IGNORE INTO prospect_stage_history(prospect_id,stage) VALUES(?,?)',(id,stage))
        conn.commit()
    return 200, query('SELECT * FROM prospects WHERE id=?', (id,), one=True)

def inactive(h):
    try: days=int(h.headers.get('X-Inactivity-Days','3'))
    except (TypeError, ValueError): raise APIError(400, 'X-Inactivity-Days debe ser un entero positivo')
    if days < 1: raise APIError(400, 'X-Inactivity-Days debe ser un entero positivo')
    return 200,query("SELECT * FROM prospects WHERE stage!='closed' AND julianday('now')-julianday(last_activity)>=?",(days,))
Prospects.routes={('GET','/prospects'):list_all,('GET','/prospects/inactive'):inactive,('GET','/prospects/{id}'):get_one,('POST','/prospects'):create,('PATCH','/prospects/{id}'):update}
if __name__=='__main__': initialize(); serve(Prospects,8001)
