from shared.db import initialize, query, execute, LOCK, connect
from shared.http import Handler, APIError, required, serve
class Sales(Handler): pass
def list_all(h): return 200,query("SELECT s.*,p.name prospect_name,v.brand||' '||v.model vehicle_name,se.name seller_name,CASE WHEN i.id IS NOT NULL THEN 'Sí' ELSE 'No' END AS has_insurance FROM sales s JOIN prospects p ON p.id=s.prospect_id JOIN vehicles v ON v.id=s.vehicle_id JOIN sellers se ON se.id=s.seller_id LEFT JOIN insurance i ON i.sale_id=s.id ORDER BY s.id DESC")

def create(h):
    d=h._body(); required(d,'prospect_id','vehicle_id','seller_id','amount','status')

    vehicle = query('SELECT id, sold FROM vehicles WHERE id=?', (d['vehicle_id'],), one=True)
    if not vehicle: raise APIError(400, 'Vehículo no encontrado')

    seller = query('SELECT id FROM sellers WHERE id=?', (d['seller_id'],), one=True)
    if not seller: raise APIError(400, 'Vendedor no encontrado')

    prospect = query('SELECT * FROM prospects WHERE id=?', (d['prospect_id'],), one=True)
    if not prospect: raise APIError(400, 'Prospecto no encontrado')
    if prospect['stage'] == 'closed': raise APIError(409, 'El prospecto ya está cerrado')

    if d['amount'] <= 0: raise APIError(400, 'El monto debe ser mayor a cero')
    if d['status'] not in ('completed', 'failed'): raise APIError(400, 'Estado inválido')
    
    if d['status']=='failed' and not d.get('loss_reason'): raise APIError(400,'Indique el motivo de pérdida')
    
    try:
        with LOCK, connect() as c:
            ps = c.execute('SELECT stage FROM prospects WHERE id=?', (d['prospect_id'],)).fetchone()
            if ps is None: raise APIError(400, 'Prospecto no encontrado')
            if ps['stage'] == 'closed': raise APIError(409, 'El prospecto ya está cerrado')
            v = c.execute('SELECT sold FROM vehicles WHERE id=?', (d['vehicle_id'],)).fetchone()
            if d['status'] == 'completed' and v['sold'] > 0:
                raise APIError(400, 'Este vehículo ya fue vendido')
            cur=c.execute('INSERT INTO sales(prospect_id,vehicle_id,seller_id,amount,status,loss_reason) VALUES(?,?,?,?,?,?)',(d['prospect_id'],d['vehicle_id'],d['seller_id'],d['amount'],d['status'],d.get('loss_reason')))
            c.execute('UPDATE prospects SET stage=?,outcome=?,loss_reason=?,last_activity=CURRENT_TIMESTAMP WHERE id=?',('closed','won' if d['status']=='completed' else 'lost',d.get('loss_reason'),d['prospect_id']))
            if d['status'] == 'completed':
                c.execute('UPDATE vehicles SET sold = sold + 1 WHERE id=?', (d['vehicle_id'],))
            c.commit(); sid=cur.lastrowid
    except APIError:
        raise
    except Exception as e:
        if 'UNIQUE' in str(e): raise APIError(409,'El prospecto ya tiene una venta')
        raise APIError(400,'Referencias o valores inválidos')
    return 201,query('SELECT * FROM sales WHERE id=?',(sid,),one=True)

def conversion(h):
    rows=query("SELECT se.id seller_id, se.name seller, COUNT(p.id) prospects, SUM(CASE WHEN p.outcome='won' THEN 1 ELSE 0 END) won, ROUND(100.0*SUM(CASE WHEN p.outcome='won' THEN 1 ELSE 0 END)/NULLIF(COUNT(p.id),0),2) rate FROM sellers se LEFT JOIN prospects p ON p.seller_id=se.id GROUP BY se.id")
    return 200,rows
def get_one_sale(h,id):
    item=query("""SELECT s.*,p.name prospect_name,v.brand||' '||v.model vehicle_name,se.name seller_name,CASE WHEN i.id IS NOT NULL THEN 'Sí' ELSE 'No' END AS has_insurance
        FROM sales s
        JOIN prospects p ON p.id=s.prospect_id
        JOIN vehicles v ON v.id=s.vehicle_id
        JOIN sellers se ON se.id=s.seller_id
        LEFT JOIN insurance i ON i.sale_id=s.id
        WHERE s.id=?""",(id,),one=True)
    if not item: raise APIError(404,'Venta no encontrada')
    return 200,item

Sales.routes={('GET','/sales'):list_all,('POST','/sales'):create,('GET','/sales/conversion'):conversion,('GET','/sales/{id}'):get_one_sale}
if __name__=='__main__': initialize(); serve(Sales,8002)
