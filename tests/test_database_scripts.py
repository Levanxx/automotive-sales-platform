import re
import sqlite3
import unittest
from pathlib import Path

from shared.db import execute, initialize

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

if __name__=='__main__': unittest.main()
