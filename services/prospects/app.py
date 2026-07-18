from shared.db import initialize, query, execute
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
    pid=execute('INSERT INTO prospects(name,email,phone,vehicle_interest,stage,seller_id) VALUES(?,?,?,?,?,?)',(d['name'],d['email'],d['phone'],d['vehicle_interest'],stage,d['seller_id']))
    return 201,query('SELECT * FROM prospects WHERE id=?',(pid,),one=True)

def update(h, id):
    d = h._body()
    item = query('SELECT * FROM prospects WHERE id=?', (id,), one=True)
    if not item: raise APIError(404, 'Prospecto no encontrado')
    stage = d.get('stage', item['stage'])
    if stage not in STAGES: raise APIError(400, 'Etapa inválida')
    outcome = d.get('outcome', item.get('outcome'))
    loss_reason = d.get('loss_reason', item.get('loss_reason'))
    execute("UPDATE prospects SET stage=?,outcome=?,loss_reason=?,last_activity=CURRENT_TIMESTAMP WHERE id=?",
            (stage, outcome, loss_reason, id))
    return 200, query('SELECT * FROM prospects WHERE id=?', (id,), one=True)

def inactive(h):
    return 200,query("SELECT * FROM prospects WHERE stage!='closed' AND julianday('now')-julianday(last_activity)>=?",(int(h.headers.get('X-Inactivity-Days','3')),))
Prospects.routes={('GET','/prospects'):list_all,('GET','/prospects/inactive'):inactive,('GET','/prospects/{id}'):get_one,('POST','/prospects'):create,('PATCH','/prospects/{id}'):update}
if __name__=='__main__': initialize(); serve(Prospects,8001)
