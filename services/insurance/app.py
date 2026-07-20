import sqlite3
from shared.db import initialize,query,execute
from shared.http import Handler,APIError,required,serve
class Insurance(Handler): pass
def list_all(h): return 200,query('''SELECT i.*,s.prospect_id,p.name prospect_name,
  v.brand||' '||v.model vehicle_name
FROM insurance i
JOIN sales s ON s.id=i.sale_id
JOIN prospects p ON p.id=s.prospect_id
JOIN vehicles v ON v.id=s.vehicle_id
ORDER BY i.id DESC''')

def create(h):

    d=h._body(); required(d,'sale_id','type','expected_premium','status')
    expected=d['expected_premium']; actual=d.get('actual_premium')
    if isinstance(expected,bool) or not isinstance(expected,(int,float)) or expected < 0:
        raise APIError(400, 'La prima esperada debe ser un número no negativo')
    if actual is not None and (isinstance(actual,bool) or not isinstance(actual,(int,float)) or actual < 0):
        raise APIError(400, 'La prima real debe ser un número no negativo')
    
    if d['status'] not in ('prospected', 'sold'): raise APIError(400, 'Estado inválido')
    if d['status']=='sold' and actual is None: raise APIError(400, 'La prima real es obligatoria para un seguro vendido')
    
    sale=query("SELECT * FROM sales WHERE id=? AND status='completed'",(d['sale_id'],),one=True)
    if not sale: raise APIError(400,'El seguro requiere una venta efectiva')
    try: iid=execute('INSERT INTO insurance(sale_id,type,expected_premium,actual_premium,status) VALUES(?,?,?,?,?)',(d['sale_id'],d['type'],d['expected_premium'],d.get('actual_premium'),d['status']))
    except sqlite3.IntegrityError: raise APIError(409,'La venta ya tiene seguro')
    return 201,query('SELECT * FROM insurance WHERE id=?',(iid,),one=True)
def get_one_insurance(h,id):
    item=query("""SELECT i.*,s.prospect_id,p.name prospect_name,
        v.brand||' '||v.model vehicle_name
        FROM insurance i
        JOIN sales s ON s.id=i.sale_id
        JOIN prospects p ON p.id=s.prospect_id
        JOIN vehicles v ON v.id=s.vehicle_id
        WHERE i.id=?""",(id,),one=True)
    if not item: raise APIError(404,'Seguro no encontrado')
    return 200,item

def patch_insurance(h,id):
    d=h._body()
    row=query('SELECT * FROM insurance WHERE id=?',(id,),one=True)
    if not row: raise APIError(404,'Seguro no encontrado')
    status=d.get('status',row['status'])
    if status not in ('prospected','sold'): raise APIError(400,'Estado inválido')
    type_=d.get('type',row['type'])
    expected=d.get('expected_premium',row['expected_premium'])
    actual=d.get('actual_premium',row['actual_premium'])
    if isinstance(expected,bool) or not isinstance(expected,(int,float)) or expected < 0:
        raise APIError(400,'La prima esperada debe ser un número no negativo')
    if actual is not None and (isinstance(actual,bool) or not isinstance(actual,(int,float)) or actual < 0):
        raise APIError(400,'La prima real debe ser un número no negativo')
    if status == 'sold' and actual is None:
        raise APIError(400,'La prima real es obligatoria para un seguro vendido')
    execute('UPDATE insurance SET type=?,expected_premium=?,actual_premium=?,status=? WHERE id=?',(type_,expected,actual,status,id))
    return 200,get_one_insurance(h,id)[1]

Insurance.routes={('GET','/insurance'):list_all,('POST','/insurance'):create,('GET','/insurance/{id}'):get_one_insurance,('PATCH','/insurance/{id}'):patch_insurance}
if __name__=='__main__': initialize(); serve(Insurance,8003)
