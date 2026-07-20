import io,json,os,tempfile,unittest
from pathlib import Path
DB=tempfile.NamedTemporaryFile(delete=False); DB.close(); os.environ['DATABASE_PATH']=DB.name
from shared.db import initialize,query
from shared.http import APIError
from services.prospects.app import create as create_prospect, update
from services.sales.app import create as create_sale, conversion
from services.insurance.app import create as create_insurance
from services.dashboard.app import metrics

class Fake:
    def __init__(self,data=None,headers=None): self.data=data or {}; self.headers=headers or {}
    def _body(self): return self.data
class ServicesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls): initialize()
    def prospect(self,n='A'):
        return create_prospect(Fake({'name':n,'email':n+'@x.pe','phone':'999','vehicle_id':1,'seller_id':1}))[1]
    def test_prospect_lifecycle(self):
        p=self.prospect('life'); self.assertEqual(p['stage'],'initial')
        result=update(Fake({'stage':'qualification'}),str(p['id']))[1]; self.assertEqual(result['stage'],'qualification')
        result=update(Fake({'stage':'negotiation'}),str(p['id']))[1]; self.assertEqual(result['stage'],'negotiation')
    def test_validation(self):
        with self.assertRaises(APIError): create_prospect(Fake({'name':'x'}))
        p=self.prospect('badstage')
        with self.assertRaises(APIError): update(Fake({'stage':'invalid'}),str(p['id']))
    def test_sale_and_insurance(self):
        p=self.prospect('buyer'); sale=create_sale(Fake({'prospect_id':p['id'],'vehicle_id':1,'seller_id':1,'amount':25000,'status':'completed'}))[1]
        self.assertEqual(sale['status'],'completed')
        self.assertEqual(query('SELECT outcome FROM prospects WHERE id=?',(p['id'],),one=True)['outcome'],'won')
        policy=create_insurance(Fake({'sale_id':sale['id'],'type':'Todo riesgo','expected_premium':1200,'actual_premium':1150,'status':'sold'}))[1]
        self.assertEqual(policy['status'],'sold')
        with self.assertRaises(APIError): create_insurance(Fake({'sale_id':sale['id'],'type':'SOAT','expected_premium':200,'status':'sold'}))
    def test_failed_sale_requires_reason(self):
        p=self.prospect('lost')
        with self.assertRaises(APIError): create_sale(Fake({'prospect_id':p['id'],'vehicle_id':1,'seller_id':1,'amount':2,'status':'failed'}))
    def test_metrics_and_conversion(self):
        data=metrics(Fake())[1]; self.assertIn('conversion_rate',data); self.assertIsInstance(data['funnel'],list)
        self.assertEqual(conversion(Fake())[0],200)

    def advance_to_negotiation(self, prospect_id):
        update(Fake({'stage':'qualification'}),str(prospect_id))
        update(Fake({'stage':'negotiation'}),str(prospect_id))

    def test_cierre_modal_won(self):
        p=self.prospect('cierre_won')
        self.advance_to_negotiation(p['id'])
        sale=create_sale(Fake({'prospect_id':p['id'],'vehicle_id':2,'seller_id':1,'amount':25000,'status':'completed'}))[1]
        self.assertEqual(sale['status'],'completed')
        self.assertEqual(sale['prospect_id'],p['id'])
        p2=query('SELECT * FROM prospects WHERE id=?',(p['id'],),one=True)
        self.assertEqual(p2['stage'],'closed')
        self.assertEqual(p2['outcome'],'won')

    def test_cierre_modal_lost(self):
        p=self.prospect('cierre_lost')
        self.advance_to_negotiation(p['id'])
        sale=create_sale(Fake({'prospect_id':p['id'],'vehicle_id':1,'seller_id':1,'amount':100,'status':'failed','loss_reason':'Precio muy alto'}))[1]
        self.assertEqual(sale['status'],'failed')
        p2=query('SELECT * FROM prospects WHERE id=?',(p['id'],),one=True)
        self.assertEqual(p2['stage'],'closed')
        self.assertEqual(p2['outcome'],'lost')
        self.assertEqual(p2['loss_reason'],'Precio muy alto')

    def test_cierre_then_seguro(self):
        p=self.prospect('seguro_flow')
        self.advance_to_negotiation(p['id'])
        sale=create_sale(Fake({'prospect_id':p['id'],'vehicle_id':3,'seller_id':1,'amount':25000,'status':'completed'}))[1]
        policy=create_insurance(Fake({'sale_id':sale['id'],'type':'Todo riesgo','expected_premium':1200,'actual_premium':1150,'status':'sold'}))[1]
        self.assertEqual(policy['sale_id'],sale['id'])
        self.assertEqual(policy['status'],'sold')
        self.assertEqual(policy['type'],'Todo riesgo')

    def test_doble_cierre_rechazado(self):
        from services.dashboard.app import create_vehicle
        v=create_vehicle(Fake({'brand':'TestV','model':'X','year':2026,'price':1000}))[1]
        p=self.prospect('doble_cierre')
        self.advance_to_negotiation(p['id'])
        create_sale(Fake({'prospect_id':p['id'],'vehicle_id':v['id'],'seller_id':1,'amount':25000,'status':'completed'}))
        with self.assertRaises(APIError) as ctx:
            create_sale(Fake({'prospect_id':p['id'],'vehicle_id':v['id'],'seller_id':1,'amount':25000,'status':'completed'}))
        self.assertIn('ya',str(ctx.exception).lower())
        sales=query("SELECT COUNT(*) c FROM sales WHERE prospect_id=?",(p['id'],))
        self.assertEqual(sales[0]['c'],1)

    def test_create_vehicle(self):
        from services.dashboard.app import create_vehicle
        v=create_vehicle(Fake({'brand':'Mazda','model':'CX-5','year':2026,'price':35000}))[1]
        self.assertEqual(v['brand'],'Mazda')
        self.assertEqual(v['model'],'CX-5')
        self.assertEqual(v['year'],2026)
        self.assertEqual(v['price'],35000)
        self.assertIsNone(v['imagen'])

    def test_create_vehicle_with_image(self):
        from services.dashboard.app import create_vehicle
        v=create_vehicle(Fake({'brand':'Mazda','model':'CX-5','year':2026,'price':35000,'imagen':'https://example.com/img.jpg'}))[1]
        self.assertEqual(v['imagen'],'https://example.com/img.jpg')

    def test_create_vehicle_missing_fields(self):
        from services.dashboard.app import create_vehicle
        with self.assertRaises(APIError): create_vehicle(Fake({'brand':'Mazda'}))

    def test_create_seller(self):
        from services.dashboard.app import create_seller
        s=create_seller(Fake({'name':'Nuevo Vendedor','email':'nuevo@autos.pe'}))[1]
        self.assertEqual(s['name'],'Nuevo Vendedor')
        self.assertEqual(s['email'],'nuevo@autos.pe')

    def test_create_seller_duplicate_email(self):
        from services.dashboard.app import create_seller
        with self.assertRaises(APIError) as ctx:
            create_seller(Fake({'name':'Otro','email':'nuevo@autos.pe'}))
        self.assertIn('registrado',str(ctx.exception).lower())

    def test_create_prospect_with_vehicle_fk(self):
        p=create_prospect(Fake({'name':'FK Test','email':'fk@x.pe','phone':'999','vehicle_id':1,'seller_id':1}))[1]
        self.assertEqual(p['vehicle_id'],1)
        self.assertEqual(p['vehicle_name'],'Toyota Corolla (2026)')

    def test_create_prospect_invalid_vehicle(self):
        with self.assertRaises(APIError) as ctx:
            create_prospect(Fake({'name':'BadV','email':'bv@x.pe','phone':'999','vehicle_id':999,'seller_id':1}))
        self.assertIn('Vehículo',str(ctx.exception))

    def test_prospect_no_vehicle_optional(self):
        p=create_prospect(Fake({'name':'NoVeh','email':'nov@x.pe','phone':'999','seller_id':1}))[1]
        self.assertIsNone(p['vehicle_id'])

if __name__=='__main__': unittest.main()

