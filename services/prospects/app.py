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
    stage=d.get('stage','initial')
    if stage not in STAGES: raise APIError(400,'Etapa inválida')
    pid=execute('INSERT INTO prospects(name,email,phone,vehicle_interest,stage,seller_id) VALUES(?,?,?,?,?,?)',(d['name'],d['email'],d['phone'],d['vehicle_interest'],stage,d['seller_id']))
    return 201,query('SELECT * FROM prospects WHERE id=?',(pid,),one=True)
def update(h,id):
    d=h._body(); stage=d.get('stage');
    if stage not in STAGES: raise APIError(400,'Etapa inválida')
    if not query('SELECT id FROM prospects WHERE id=?',(id,),one=True): raise APIError(404,'Prospecto no encontrado')
    execute("UPDATE prospects SET stage=?,outcome=?,loss_reason=?,last_activity=CURRENT_TIMESTAMP WHERE id=?",(stage,d.get('outcome'),d.get('loss_reason'),id))
    return 200,query('SELECT * FROM prospects WHERE id=?',(id,),one=True)
def inactive(h):
    return 200,query("SELECT * FROM prospects WHERE stage!='closed' AND julianday('now')-julianday(last_activity)>=?",(int(h.headers.get('X-Inactivity-Days','3')),))
Prospects.routes={('GET','/prospects'):list_all,('GET','/prospects/inactive'):inactive,('GET','/prospects/{id}'):get_one,('POST','/prospects'):create,('PATCH','/prospects/{id}'):update}
if __name__=='__main__': initialize(); serve(Prospects,8001)
