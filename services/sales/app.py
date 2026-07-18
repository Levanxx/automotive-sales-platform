from shared.db import initialize, query, execute, LOCK, connect
from shared.http import Handler, APIError, required, serve
class Sales(Handler): pass
def list_all(h): return 200,query("SELECT s.*,p.name prospect_name,v.brand||' '||v.model vehicle_name,se.name seller_name FROM sales s JOIN prospects p ON p.id=s.prospect_id JOIN vehicles v ON v.id=s.vehicle_id JOIN sellers se ON se.id=s.seller_id ORDER BY s.id DESC")

def create(h):
    d=h._body(); required(d,'prospect_id','vehicle_id','seller_id','amount','status')

    vehicle = query('SELECT id FROM vehicles WHERE id=?', (d['vehicle_id'],), one=True)
    if not vehicle: raise APIError(400, 'Vehículo no encontrado')

    seller = query('SELECT id FROM sellers WHERE id=?', (d['seller_id'],), one=True)
    if not seller: raise APIError(400, 'Vendedor no encontrado')

    prospect = query('SELECT * FROM prospects WHERE id=?', (d['prospect_id'],), one=True)
    if not prospect: raise APIError(400, 'Prospecto no encontrado')
    if prospect['stage'] == 'closed': raise APIError(400, 'El prospecto ya está cerrado')

    if d['amount'] <= 0: raise APIError(400, 'El monto debe ser mayor a cero')
    if d['status'] not in ('completed', 'failed'): raise APIError(400, 'Estado inválido')
    
    if d['status']=='failed' and not d.get('loss_reason'): raise APIError(400,'Indique el motivo de pérdida')
    
    try:
        with LOCK, connect() as c:
            cur=c.execute('INSERT INTO sales(prospect_id,vehicle_id,seller_id,amount,status,loss_reason) VALUES(?,?,?,?,?,?)',(d['prospect_id'],d['vehicle_id'],d['seller_id'],d['amount'],d['status'],d.get('loss_reason')))
            c.execute('UPDATE prospects SET stage=?,outcome=?,loss_reason=?,last_activity=CURRENT_TIMESTAMP WHERE id=?',('closed','won' if d['status']=='completed' else 'lost',d.get('loss_reason'),d['prospect_id']))
            c.commit(); sid=cur.lastrowid
    except Exception as e:
        if 'UNIQUE' in str(e): raise APIError(409,'El prospecto ya tiene una venta')
        raise APIError(400,'Referencias o valores inválidos')
    return 201,query('SELECT * FROM sales WHERE id=?',(sid,),one=True)

def conversion(h):
    rows=query("SELECT se.name seller, COUNT(p.id) prospects, SUM(CASE WHEN p.outcome='won' THEN 1 ELSE 0 END) won, ROUND(100.0*SUM(CASE WHEN p.outcome='won' THEN 1 ELSE 0 END)/NULLIF(COUNT(p.id),0),2) rate FROM sellers se LEFT JOIN prospects p ON p.seller_id=se.id GROUP BY se.id")
    return 200,rows
Sales.routes={('GET','/sales'):list_all,('POST','/sales'):create,('GET','/sales/conversion'):conversion}
if __name__=='__main__': initialize(); serve(Sales,8002)
