import os, threading
from pathlib import Path


from dotenv import load_dotenv


def _database_url():
    """Load the configured database, including legacy bare-URL .env files."""
    env_path = Path(__file__).parents[1] / '.env'
    load_dotenv(env_path)
    if 'DATABASE_URL' in os.environ:
        return os.environ['DATABASE_URL'].strip() or None

    # Some existing local installations stored only the connection URL in
    # .env. Keep them working instead of silently falling back to SQLite.
    if env_path.exists():
        bare_values = [
            line.strip()
            for line in env_path.read_text().splitlines()
            if line.strip() and not line.lstrip().startswith('#') and '=' not in line
        ]
        if len(bare_values) == 1 and bare_values[0].startswith(('postgresql://', 'postgres://')):
            return bare_values[0]
    return None


DATABASE_URL = _database_url()

if DATABASE_URL:  # pragma: no cover — tested manually via Supabase
    import psycopg2
    from psycopg2 import pool
    from psycopg2.extras import RealDictCursor
    from contextlib import nullcontext
    IntegrityError = psycopg2.IntegrityError

    LOCK = nullcontext()

    _pool = pool.ThreadedConnectionPool(1, 20, DATABASE_URL)

    SCHEMA = """
CREATE TABLE IF NOT EXISTS sellers(id SERIAL PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS vehicles(id SERIAL PRIMARY KEY, brand TEXT NOT NULL, model TEXT NOT NULL, year INTEGER NOT NULL, price DOUBLE PRECISION NOT NULL, sold INTEGER NOT NULL DEFAULT 0, imagen TEXT);
CREATE TABLE IF NOT EXISTS prospects(
 id SERIAL PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL, phone TEXT NOT NULL,
 vehicle_id INTEGER REFERENCES vehicles(id), stage TEXT NOT NULL CHECK(stage IN ('initial','qualification','negotiation','closed')),
 seller_id INTEGER NOT NULL REFERENCES sellers(id), outcome TEXT CHECK(outcome IN ('won','lost')),
 loss_reason TEXT, last_activity TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(seller_id) REFERENCES sellers(id));
CREATE TABLE IF NOT EXISTS sales(
 id SERIAL PRIMARY KEY, prospect_id INTEGER UNIQUE NOT NULL REFERENCES prospects(id), vehicle_id INTEGER NOT NULL REFERENCES vehicles(id),
 seller_id INTEGER NOT NULL REFERENCES sellers(id), amount DOUBLE PRECISION NOT NULL CHECK(amount>0), status TEXT NOT NULL CHECK(status IN ('completed','failed')),
 loss_reason TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(vehicle_id) REFERENCES vehicles(id), FOREIGN KEY(seller_id) REFERENCES sellers(id));
CREATE TABLE IF NOT EXISTS insurance(
 id SERIAL PRIMARY KEY, sale_id INTEGER UNIQUE NOT NULL REFERENCES sales(id), type TEXT NOT NULL,
 expected_premium DOUBLE PRECISION NOT NULL CHECK(expected_premium>=0), actual_premium DOUBLE PRECISION,
 status TEXT NOT NULL CHECK(status IN ('prospected','sold')),
 created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(sale_id) REFERENCES sales(id));
CREATE TABLE IF NOT EXISTS performance_runs(
 id SERIAL PRIMARY KEY, concurrency INTEGER NOT NULL, requests INTEGER NOT NULL,
 success INTEGER NOT NULL, error_rate_percent DOUBLE PRECISION NOT NULL, duration_seconds DOUBLE PRECISION NOT NULL,
 avg_ms DOUBLE PRECISION NOT NULL, p95_ms DOUBLE PRECISION NOT NULL, max_ms DOUBLE PRECISION NOT NULL,
 acceptance INTEGER NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS automation_alerts(
 id SERIAL PRIMARY KEY, event TEXT NOT NULL, message TEXT NOT NULL,
 payload JSONB, created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS idx_prospects_email ON prospects(email);
CREATE INDEX IF NOT EXISTS ix_prospectos_etapa ON prospects(stage);
CREATE INDEX IF NOT EXISTS ix_prospectos_actividad ON prospects(last_activity);
CREATE INDEX IF NOT EXISTS ix_ventas_estado ON sales(status);
"""

    class _CursorWrapper:
        def __init__(self, cur, lastrowid=None):
            self._cur = cur
            self.lastrowid = lastrowid
        def __getattr__(self, name):
            return getattr(self._cur, name)

    class _PgConnection:
        def __init__(self, conn):
            self._conn = conn
        def execute(self, sql, params=()):
            cur = self._conn.cursor()
            pg_sql = sql.replace('%', '%%').replace('?', '%s')
            is_insert = pg_sql.strip().upper().startswith('INSERT')
            if is_insert and 'RETURNING' not in pg_sql.upper():
                pg_sql += ' RETURNING id'
            cur.execute(pg_sql, params)
            lastrowid = None
            if is_insert and cur.description:
                row = cur.fetchone()
                lastrowid = row['id'] if row else None
            return _CursorWrapper(cur, lastrowid)
        def commit(self):
            self._conn.commit()
        def close(self):
            _pool.putconn(self._conn)
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.close()

    def connect():
        conn = _pool.getconn()
        conn.cursor_factory = RealDictCursor
        return _PgConnection(conn)

    def initialize():
        conn = connect()
        try:
            with conn._conn:
                with conn._conn.cursor() as cur:
                    for stmt in SCHEMA.split(';'):
                        stmt = stmt.strip()
                        if stmt:
                            cur.execute(stmt + ';')
                with conn._conn.cursor() as cur:
                    cur.execute("INSERT INTO sellers(id,name,email) VALUES(1,'Ana Torres','ana@autos.pe') ON CONFLICT DO NOTHING")
                    cur.execute("INSERT INTO sellers(id,name,email) VALUES(2,'Luis Vega','luis@autos.pe') ON CONFLICT DO NOTHING")
                    cur.execute("INSERT INTO vehicles(id,brand,model,year,price,imagen) VALUES(1,'Toyota','Corolla',2026,24990,'https://images.unsplash.com/photo-1621007947382-bb3c39934b6e?w=300') ON CONFLICT DO NOTHING")
                    cur.execute("INSERT INTO vehicles(id,brand,model,year,price,imagen) VALUES(2,'Kia','Sportage',2026,31990,'https://images.unsplash.com/photo-1549399542-7e8f8b658f9d?w=300') ON CONFLICT DO NOTHING")
                    cur.execute("INSERT INTO vehicles(id,brand,model,year,price,imagen) VALUES(3,'Hyundai','Tucson',2025,29990,'https://images.unsplash.com/photo-1609521263047-f8f205293f24?w=300') ON CONFLICT DO NOTHING")
                    cur.execute("SELECT setval('vehicles_id_seq', (SELECT MAX(id) FROM vehicles))")
        finally:
            conn.close()

    _POOL_MIN = 1
    def query(sql, params=(), one=False):
        conn = connect()
        try:
            with conn._conn:
                with conn._conn.cursor() as cur:
                    cur.execute(sql.replace('%', '%%').replace('?', '%s'), params)
                    rows = cur.fetchall()
                    result = [dict(r) for r in rows]
                    return (result[0] if result else None) if one else result
        finally:
            conn.close()

    def execute(sql, params=()):
        conn = connect()
        try:
            with conn._conn:
                with conn._conn.cursor() as cur:
                    pg_sql = sql.replace('%', '%%').replace('?', '%s')
                    is_insert = pg_sql.strip().upper().startswith('INSERT')
                    if is_insert and 'RETURNING' not in pg_sql.upper():
                        pg_sql += ' RETURNING id'
                    cur.execute(pg_sql, params)
                    if is_insert and cur.description:
                        row = cur.fetchone()
                        return row['id'] if row else None
                    return None
        finally:
            conn.close()

else:
    import sqlite3
    IntegrityError = sqlite3.IntegrityError

    LOCK = threading.RLock()

    SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS sellers(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS vehicles(id INTEGER PRIMARY KEY, brand TEXT NOT NULL, model TEXT NOT NULL, year INTEGER NOT NULL, price REAL NOT NULL, sold INTEGER NOT NULL DEFAULT 0, imagen TEXT);
CREATE TABLE IF NOT EXISTS prospects(
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL, phone TEXT NOT NULL,
 vehicle_id INTEGER, stage TEXT NOT NULL CHECK(stage IN ('initial','qualification','negotiation','closed')),
 seller_id INTEGER NOT NULL, outcome TEXT CHECK(outcome IN ('won','lost') OR outcome IS NULL),
 loss_reason TEXT, last_activity TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(seller_id) REFERENCES sellers(id), FOREIGN KEY(vehicle_id) REFERENCES vehicles(id));
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

    def initialize():
        with LOCK, connect() as conn:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA synchronous=NORMAL')
            conn.executescript(SCHEMA)
            for col in ('sold','imagen'):
                try: conn.execute(f"ALTER TABLE vehicles ADD COLUMN {col} TEXT" if col=='imagen' else f"ALTER TABLE vehicles ADD COLUMN {col} INTEGER NOT NULL DEFAULT 0")
                except: pass
            try: conn.execute("ALTER TABLE prospects ADD COLUMN vehicle_id INTEGER")
            except: pass
            cols=[r[1] for r in conn.execute('PRAGMA table_info(prospects)').fetchall()]
            if 'vehicle_interest' in cols:
                try: conn.execute("ALTER TABLE prospects DROP COLUMN vehicle_interest")
                except: pass
            try: conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_prospects_email ON prospects(email)')
            except: pass
            conn.executemany('INSERT OR IGNORE INTO sellers(id,name,email) VALUES(?,?,?)', [(1,'Ana Torres','ana@autos.pe'),(2,'Luis Vega','luis@autos.pe')])
            conn.executemany('INSERT OR IGNORE INTO vehicles(id,brand,model,year,price,imagen) VALUES(?,?,?,?,?,?)', [(1,'Toyota','Corolla',2026,24990,'https://images.unsplash.com/photo-1621007947382-bb3c39934b6e?w=300'),(2,'Kia','Sportage',2026,31990,'https://images.unsplash.com/photo-1549399542-7e8f8b658f9d?w=300'),(3,'Hyundai','Tucson',2025,29990,'https://images.unsplash.com/photo-1609521263047-f8f205293f24?w=300')])

    def query(sql, params=(), one=False):
        with LOCK, connect() as conn:
            rows = conn.execute(sql, params).fetchall()
            result = [{k: r[k] for k in r.keys()} for r in rows]
            return (result[0] if result else None) if one else result

    def execute(sql, params=()):
        with LOCK, connect() as conn:
            cur = conn.execute(sql, params); conn.commit(); return cur.lastrowid
