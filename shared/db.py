import os, sqlite3, threading
from contextlib import contextmanager
from pathlib import Path

LOCK = threading.RLock()

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS sellers(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS vehicles(id INTEGER PRIMARY KEY, brand TEXT NOT NULL, model TEXT NOT NULL, year INTEGER NOT NULL, price REAL NOT NULL);
CREATE TABLE IF NOT EXISTS prospects(
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL, phone TEXT NOT NULL,
 vehicle_interest TEXT NOT NULL, stage TEXT NOT NULL CHECK(stage IN ('initial','qualification','negotiation','closed')),
 seller_id INTEGER NOT NULL, outcome TEXT CHECK(outcome IN ('won','lost') OR outcome IS NULL),
 loss_reason TEXT, last_activity TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(seller_id) REFERENCES sellers(id));

CREATE TABLE IF NOT EXISTS prospect_stage_history(
 id INTEGER PRIMARY KEY AUTOINCREMENT, prospect_id INTEGER NOT NULL, stage TEXT NOT NULL,
 entered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(prospect_id,stage), FOREIGN KEY(prospect_id) REFERENCES prospects(id) ON DELETE CASCADE);

CREATE TABLE IF NOT EXISTS sales(
 id INTEGER PRIMARY KEY AUTOINCREMENT, prospect_id INTEGER UNIQUE NOT NULL, vehicle_id INTEGER NOT NULL,
 seller_id INTEGER NOT NULL, amount REAL NOT NULL CHECK(amount>0), status TEXT NOT NULL CHECK(status IN ('completed','failed')),
 loss_reason TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(prospect_id) REFERENCES prospects(id), FOREIGN KEY(vehicle_id) REFERENCES vehicles(id), FOREIGN KEY(seller_id) REFERENCES sellers(id));

CREATE TABLE IF NOT EXISTS insurance(
 id INTEGER PRIMARY KEY AUTOINCREMENT, sale_id INTEGER UNIQUE NOT NULL, type TEXT NOT NULL,
 expected_premium REAL NOT NULL CHECK(expected_premium>=0), actual_premium REAL,
 status TEXT NOT NULL CHECK(status IN ('prospected','sold')),
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(sale_id) REFERENCES sales(id));

CREATE TABLE IF NOT EXISTS performance_runs(
 id INTEGER PRIMARY KEY AUTOINCREMENT, concurrency INTEGER NOT NULL, requests INTEGER NOT NULL,
 success INTEGER NOT NULL, error_rate_percent REAL NOT NULL, duration_seconds REAL NOT NULL,
 avg_ms REAL NOT NULL, p95_ms REAL NOT NULL, max_ms REAL NOT NULL,
 acceptance INTEGER NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE IF NOT EXISTS automation_alerts(
 id INTEGER PRIMARY KEY AUTOINCREMENT, event TEXT NOT NULL, message TEXT NOT NULL,
 payload TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
"""

def db_path(): return os.getenv('DATABASE_PATH', str(Path(__file__).parents[1] / 'automotive.db'))

def connect():
    path = db_path(); Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30); conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn

@contextmanager
def managed_connection():
    conn=connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally: conn.close()

def initialize():
    with LOCK, managed_connection() as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA synchronous=NORMAL')
        conn.executescript(SCHEMA)
        conn.executemany('INSERT OR IGNORE INTO sellers(id,name,email) VALUES(?,?,?)', [(1,'Ana Torres','ana@autos.pe'),(2,'Luis Vega','luis@autos.pe')])
        conn.executemany('INSERT OR IGNORE INTO vehicles(id,brand,model,year,price) VALUES(?,?,?,?,?)', [(1,'Toyota','Corolla',2026,24990),(2,'Kia','Sportage',2026,31990),(3,'Hyundai','Tucson',2025,29990)])
        conn.execute("INSERT OR IGNORE INTO prospect_stage_history(prospect_id,stage,entered_at) SELECT id,'initial',last_activity FROM prospects")
        conn.execute("INSERT OR IGNORE INTO prospect_stage_history(prospect_id,stage,entered_at) SELECT id,stage,last_activity FROM prospects WHERE stage!='initial'")

def query(sql, params=(), one=False):
    with LOCK, managed_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        result = [dict(r) for r in rows]
        return (result[0] if result else None) if one else result

def execute(sql, params=()):
    with LOCK, managed_connection() as conn:
        cur = conn.execute(sql, params); conn.commit(); return cur.lastrowid
