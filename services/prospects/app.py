import re
from datetime import datetime, timedelta, timezone
from shared.db import initialize, LOCK, connect, query, execute
from shared.http import Handler, APIError, required, serve

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

    phone = d.get('phone', '')
    if not re.match(r'^\+?\d{7,15}$', phone):
        raise APIError(400, 'Teléfono inválido: debe tener 7-15 dígitos, puede iniciar con +')

    email = d.get('email', '')
    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        raise APIError(400, 'Email inválido')

    vehicle_id = d.get('vehicle_id')
    if vehicle_id is not None:
        vehicle_id = int(vehicle_id)
        if not query('SELECT id FROM vehicles WHERE id=?', (vehicle_id,), one=True):
            raise APIError(400, 'Vehículo no encontrado')

    stage=d.get('stage','initial')
    if stage not in STAGES: raise APIError(400,'Etapa inválida')
    pid=execute('INSERT INTO prospects(name,email,phone,vehicle_id,stage,seller_id) VALUES(?,?,?,?,?,?)',(d['name'],d['email'],d['phone'],vehicle_id,stage,d['seller_id']))
    return 201,query("SELECT p.*,COALESCE(v.brand||' '||v.model||' ('||v.year||')','') vehicle_name FROM prospects p LEFT JOIN vehicles v ON v.id=p.vehicle_id WHERE p.id=?",(pid,),one=True)

def update(h, id):
    d = h._body()
    with LOCK, connect() as conn:
        row = conn.execute('SELECT * FROM prospects WHERE id=?', (id,)).fetchone()
        if not row: raise APIError(404, 'Prospecto no encontrado')
        row = {k: row[k] for k in row.keys()}
        if row['stage'] == 'closed': raise APIError(400, 'Prospecto ya está cerrado, no se puede modificar')

        stage = d.get('stage', row['stage'])
        if stage not in STAGES: raise APIError(400, 'Etapa inválida')

        if stage != row['stage']:
            expected_next = STAGE_ORDER.get(stage)
            current = STAGE_ORDER.get(row['stage'], -1)
            if expected_next != current + 1:
                valid_next = [k for k, v in STAGE_ORDER.items() if v == current + 1]
                raise APIError(400, f'Debe avanzar en orden: de {row["stage"]} solo puede ir a {valid_next[0] if valid_next else "ninguna"}')

        if stage == 'closed':
            outcome = d.get('outcome')
            if outcome not in ('won', 'lost'):
                raise APIError(400, 'Debe especificar resultado (won/lost)')
            if outcome == 'lost' and not d.get('loss_reason'):
                raise APIError(400, 'Debe indicar el motivo de pérdida')
        else:
            outcome = d.get('outcome', row.get('outcome'))
        loss_reason = d.get('loss_reason', row.get('loss_reason'))
        conn.execute("UPDATE prospects SET stage=?,outcome=?,loss_reason=?,last_activity=CURRENT_TIMESTAMP WHERE id=?",
                     (stage, outcome, loss_reason, id))
        conn.commit()
    return 200, query("SELECT p.*,COALESCE(v.brand||' '||v.model||' ('||v.year||')','') vehicle_name FROM prospects p LEFT JOIN vehicles v ON v.id=p.vehicle_id WHERE p.id=?", (id,), one=True)

def inactive(h):
    days = int(h.headers.get('X-Inactivity-Days', '3'))
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    return 200, query("SELECT * FROM prospects WHERE stage!='closed' AND last_activity <= ?", (cutoff,))
Prospects.routes={('GET','/prospects'):list_all,('GET','/prospects/inactive'):inactive,('GET','/prospects/{id}'):get_one,('POST','/prospects'):create,('PATCH','/prospects/{id}'):update}
if __name__=='__main__': initialize(); serve(Prospects,8001)
