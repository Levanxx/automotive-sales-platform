from shared.db import initialize,query,execute
from shared.http import Handler,APIError,required,serve
class Insurance(Handler): pass
def list_all(h): return 200,query('SELECT i.*,s.prospect_id,p.name prospect_name FROM insurance i JOIN sales s ON s.id=i.sale_id JOIN prospects p ON p.id=s.prospect_id ORDER BY i.id DESC')
def create(h):
    d=h._body(); required(d,'sale_id','type','expected_premium','status')
    if d['status'] not in ('prospected','sold'): raise APIError(400,'Estado inválido')
    sale=query("SELECT * FROM sales WHERE id=? AND status='completed'",(d['sale_id'],),one=True)
    if not sale: raise APIError(400,'El seguro requiere una venta efectiva')
    try: iid=execute('INSERT INTO insurance(sale_id,type,expected_premium,actual_premium,status) VALUES(?,?,?,?,?)',(d['sale_id'],d['type'],d['expected_premium'],d.get('actual_premium'),d['status']))
    except Exception: raise APIError(409,'La venta ya tiene seguro')
    return 201,query('SELECT * FROM insurance WHERE id=?',(iid,),one=True)
Insurance.routes={('GET','/insurance'):list_all,('POST','/insurance'):create}
if __name__=='__main__': initialize(); serve(Insurance,8003)
