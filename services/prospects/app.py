import sqlite3
from shared.db import LOCK, managed_connection, initialize, query
from shared.http import Handler, APIError, required, require_automation_key, serve

STAGES=('initial','qualification','negotiation','closed')
STAGE_ORDER = {'initial': 0, 'qualification': 1, 'negotiation': 2, 'closed': 3}
class Prospects(Handler): pass

def list_all(h): return 200, query("SELECT p.id,p.name,p.email,p.phone,p.vehicle_id,p.stage,p.seller_id,p.outcome,p.loss_reason,p.last_activity,s.name seller_name,COALESCE(v.brand||' '||v.model||' ('||v.year||')','') vehicle_name FROM prospects p JOIN sellers s ON s.id=p.seller_id LEFT JOIN vehicles v ON v.id=p.vehicle_id ORDER BY p.id DESC")

def get_one(h,id):
    item=query("SELECT p.*,COALESCE(v.brand||' '||v.model||' ('||v.year||')','') vehicle_name FROM prospects p LEFT JOIN vehicles v ON v.id=p.vehicle_id WHERE p.id=?",(id,),one=True)
    if not item: raise APIError(404,'Prospecto no encontrado')
    return 200,item

def create(h):
    d=h._body(); required(d,'name','email','phone','seller_id')

    existing = query('SELECT id FROM prospects WHERE email=?', (d['email'],), one=True)
    if existing: raise APIError(409, 'Ya existe un prospecto con ese email')

    seller = query('SELECT id FROM sellers WHERE id=?', (d['seller_id'],), one=True)
    if not seller: raise APIError(400, f'Vendedor id={d["seller_id"]} no encontrado')

    vehicle_id = d.get('vehicle_id')
    if vehicle_id is not None:
        try: vehicle_id = int(vehicle_id)
        except (TypeError,ValueError): raise APIError(400, 'vehicle_id debe ser un entero')
        if not query('SELECT id FROM vehicles WHERE id=?', (vehicle_id,), one=True):
            raise APIError(400, 'Vehículo no encontrado')

    stage=d.get('stage','initial')
    if stage not in STAGES: raise APIError(400,'Etapa inválida')
    try:
        with LOCK,managed_connection() as conn:
            columns={row[1] for row in conn.execute('PRAGMA table_info(prospects)')}
            if 'vehicle_interest' in columns:
                vehicle=query("SELECT brand||' '||model label FROM vehicles WHERE id=?",(vehicle_id,),one=True) if vehicle_id else None
                legacy_interest=vehicle['label'] if vehicle else 'Sin especificar'
                cur=conn.execute('INSERT INTO prospects(name,email,phone,vehicle_interest,vehicle_id,stage,seller_id) VALUES(?,?,?,?,?,?,?)',(d['name'],d['email'],d['phone'],legacy_interest,vehicle_id,stage,d['seller_id']))
            else:
                cur=conn.execute('INSERT INTO prospects(name,email,phone,vehicle_id,stage,seller_id) VALUES(?,?,?,?,?,?)',(d['name'],d['email'],d['phone'],vehicle_id,stage,d['seller_id']))
            pid=cur.lastrowid
            conn.execute('INSERT INTO prospect_stage_history(prospect_id,stage) VALUES(?,?)',(pid,'initial'))
            if stage!='initial': conn.execute('INSERT INTO prospect_stage_history(prospect_id,stage) VALUES(?,?)',(pid,stage))
    except sqlite3.IntegrityError as exc:
        if 'email' in str(exc).lower() or 'unique' in str(exc).lower():
            raise APIError(409, 'Ya existe un prospecto con ese email')
        raise APIError(400, 'Referencias o valores inválidos')
    return 201,query("SELECT p.*,COALESCE(v.brand||' '||v.model||' ('||v.year||')','') vehicle_name FROM prospects p LEFT JOIN vehicles v ON v.id=p.vehicle_id WHERE p.id=?",(pid,),one=True)

def update(h, id):
    d = h._body()
    item = query('SELECT * FROM prospects WHERE id=?', (id,), one=True)
    if not item: raise APIError(404, 'Prospecto no encontrado')
    stage = d.get('stage', item['stage'])
    if stage not in STAGES: raise APIError(400, 'Etapa inválida')
    if item['stage'] == 'closed': raise APIError(409, 'El prospecto ya está cerrado')
    if stage != item['stage']:
        current = STAGE_ORDER[item['stage']]
        if STAGE_ORDER[stage] != current + 1:
            next_stage = STAGES[current + 1] if current + 1 < len(STAGES) else 'ninguna'
            raise APIError(400, f'Debe avanzar en orden: de {item["stage"]} solo puede ir a {next_stage}')
    if stage == 'closed':
        raise APIError(400, 'El cierre se registra mediante una venta realizada o fallida')
    if 'outcome' in d or 'loss_reason' in d:
        raise APIError(400, 'El resultado y motivo se registran mediante el servicio de ventas')
    with LOCK,managed_connection() as conn:
        conn.execute("UPDATE prospects SET stage=?,last_activity=CURRENT_TIMESTAMP WHERE id=?", (stage, id))
        if stage!=item['stage']:
            conn.execute('INSERT OR IGNORE INTO prospect_stage_history(prospect_id,stage) VALUES(?,?)',(id,stage))
    return 200, query("SELECT p.*,COALESCE(v.brand||' '||v.model||' ('||v.year||')','') vehicle_name FROM prospects p LEFT JOIN vehicles v ON v.id=p.vehicle_id WHERE p.id=?", (id,), one=True)

def inactive(h):
    require_automation_key(h)
    try: days=int(h.headers.get('X-Inactivity-Days','3'))
    except (TypeError, ValueError): raise APIError(400, 'X-Inactivity-Days debe ser un entero positivo')
    if days < 1: raise APIError(400, 'X-Inactivity-Days debe ser un entero positivo')
    return 200,query("SELECT * FROM prospects WHERE stage!='closed' AND julianday('now')-julianday(last_activity)>=?",(days,))
Prospects.routes={('GET','/prospects'):list_all,('GET','/prospects/inactive'):inactive,('GET','/prospects/{id}'):get_one,('POST','/prospects'):create,('PATCH','/prospects/{id}'):update}
if __name__=='__main__': initialize(); serve(Prospects,8001)
