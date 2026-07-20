import os
import re
import sqlite3
import tempfile
import unittest
from pathlib import Path

from shared.db import execute, initialize
from services.prospects.app import create as create_prospect

ROOT=Path(__file__).parents[1]

class DatabaseScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): initialize()
    def test_oracle_ddl_is_complete(self):
        ddl=(ROOT/'database'/'oracle'/'001_schema.sql').read_text()
        self.assertNotIn('...',ddl)
        tables=set(re.findall(r'CREATE\s+TABLE\s+(\w+)',ddl,re.IGNORECASE))
        self.assertTrue({'vendedores','vehiculos','prospectos','ventas','seguros'}.issubset({x.lower() for x in tables}))
        self.assertGreaterEqual(ddl.upper().count('REFERENCES'),5)
        self.assertIn('CHECK (prima_real >= 0)',ddl)
        self.assertIn('vehiculo_id NUMBER REFERENCES vehiculos(id)',ddl)
        self.assertIn('vendido NUMBER(1)',ddl)
    def test_oracle_seed_has_required_catalogs(self):
        seed=(ROOT/'database'/'oracle'/'002_seed.sql').read_text().lower()
        self.assertGreaterEqual(seed.count('insert into vendedores'),2)
        self.assertGreaterEqual(seed.count('insert into vehiculos'),3)
        self.assertIn('commit;',seed)
    def test_sqlite_enforces_referential_integrity(self):
        with self.assertRaises(sqlite3.IntegrityError):
            execute("INSERT INTO sales(prospect_id,vehicle_id,seller_id,amount,status) VALUES(999999,1,1,10,'completed')")
    def test_legacy_sqlite_schema_accepts_new_prospects(self):
        previous=os.environ.get('DATABASE_PATH')
        with tempfile.NamedTemporaryFile() as legacy:
            conn=sqlite3.connect(legacy.name)
            conn.executescript("""
              CREATE TABLE sellers(id INTEGER PRIMARY KEY,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL);
              CREATE TABLE vehicles(id INTEGER PRIMARY KEY,brand TEXT NOT NULL,model TEXT NOT NULL,year INTEGER NOT NULL,price REAL NOT NULL);
              CREATE TABLE prospects(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,email TEXT NOT NULL,phone TEXT NOT NULL,vehicle_interest TEXT NOT NULL,stage TEXT NOT NULL,seller_id INTEGER NOT NULL,outcome TEXT,loss_reason TEXT,last_activity TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
              INSERT INTO sellers VALUES(1,'Legacy Seller','legacy-seller@test.pe');
              INSERT INTO vehicles VALUES(1,'Legacy','Car',2020,1000);
            """); conn.close()
            os.environ['DATABASE_PATH']=legacy.name
            try:
                initialize()
                class Fake:
                    headers={}
                    def _body(self): return {'name':'Legacy','email':'legacy@test.pe','phone':'1','vehicle_id':1,'seller_id':1}
                created=create_prospect(Fake())[1]
                self.assertEqual(created['vehicle_id'],1)
            finally:
                if previous is None: os.environ.pop('DATABASE_PATH',None)
                else: os.environ['DATABASE_PATH']=previous

if __name__=='__main__': unittest.main()
