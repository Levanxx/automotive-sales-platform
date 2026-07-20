import io,json,os,tempfile,unittest
from pathlib import Path
DB=tempfile.NamedTemporaryFile(delete=False); DB.close(); os.environ['DATABASE_PATH']=DB.name
from shared.db import initialize,query
from shared.http import APIError
from services.prospects.app import create as create_prospect, update
from services.sales.app import create as create_sale, conversion, stage_conversion
from services.insurance.app import create as create_insurance
from services.dashboard.app import metrics

class Fake:
    def __init__(self,data=None,headers=None): self.data=data or {}; self.headers=headers or {}
    def _body(self): return self.data
class ServicesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls): initialize()
    def prospect(self,n='A'):
        return create_prospect(Fake({'name':n,'email':n+'@x.pe','phone':'999','vehicle_interest':'Corolla','seller_id':1}))[1]
    def test_prospect_lifecycle(self):
        p=self.prospect('life'); self.assertEqual(p['stage'],'initial')
        result=update(Fake({'stage':'negotiation'}),str(p['id']))[1]; self.assertEqual(result['stage'],'negotiation')
        with self.assertRaises(APIError): update(Fake({'stage':'closed'}),str(p['id']))
        with self.assertRaises(APIError): update(Fake({'outcome':'won'}),str(p['id']))
    def test_validation(self):
        with self.assertRaises(APIError): create_prospect(Fake({'name':'x'}))
        p=self.prospect('badstage')
        with self.assertRaises(APIError): update(Fake({'stage':'invalid'}),str(p['id']))
    def test_sale_and_insurance(self):
        p=self.prospect('buyer'); sale=create_sale(Fake({'prospect_id':p['id'],'vehicle_id':1,'seller_id':1,'amount':25000,'status':'completed'}))[1]
        self.assertEqual(query('SELECT outcome FROM prospects WHERE id=?',(p['id'],),one=True)['outcome'],'won')
        policy=create_insurance(Fake({'sale_id':sale['id'],'type':'Todo riesgo','expected_premium':1200,'actual_premium':1150,'status':'sold'}))[1]
        self.assertEqual(policy['status'],'sold')
        with self.assertRaises(APIError): create_insurance(Fake({'sale_id':sale['id'],'type':'SOAT','expected_premium':200,'status':'sold'}))
    def test_failed_sale_requires_reason(self):
        p=self.prospect('lost')
        with self.assertRaises(APIError): create_sale(Fake({'prospect_id':p['id'],'vehicle_id':1,'seller_id':1,'amount':2,'status':'failed'}))
    def test_sale_requires_assigned_seller_and_numeric_amount(self):
        p=self.prospect('seller')
        with self.assertRaises(APIError): create_sale(Fake({'prospect_id':p['id'],'vehicle_id':1,'seller_id':2,'amount':2,'status':'completed'}))
        with self.assertRaises(APIError): create_sale(Fake({'prospect_id':p['id'],'vehicle_id':1,'seller_id':1,'amount':'2','status':'completed'}))
    def test_insurance_validates_actual_premium(self):
        p=self.prospect('premium'); sale=create_sale(Fake({'prospect_id':p['id'],'vehicle_id':1,'seller_id':1,'amount':25000,'status':'completed'}))[1]
        with self.assertRaises(APIError): create_insurance(Fake({'sale_id':sale['id'],'type':'Todo riesgo','expected_premium':100,'actual_premium':-1,'status':'sold'}))
        with self.assertRaises(APIError): create_insurance(Fake({'sale_id':sale['id'],'type':'Todo riesgo','expected_premium':100,'status':'sold'}))
    def test_metrics_and_conversion(self):
        data=metrics(Fake())[1]; self.assertEqual(data['conversion_rate'],round(100*data['completed_sales']/data['total_prospects'],2)); self.assertIsInstance(data['funnel'],list)
        self.assertEqual(conversion(Fake())[0],200)
        stages=stage_conversion(Fake())[1]
        self.assertEqual([x['stage'] for x in stages],['initial','qualification','negotiation','closed'])
        self.assertTrue(all('from_initial_rate' in x and 'from_previous_rate' in x for x in stages))

if __name__=='__main__': unittest.main()
