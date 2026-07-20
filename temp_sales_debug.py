import os
os.environ['DATABASE_URL'] = ''

from shared.db import connect

# Simulate what the sales endpoint does
with connect() as c:
    try:
        ps = c.execute('SELECT stage FROM prospects WHERE id=%s', (114,)).fetchone()
        print('Stage query:', ps)
        print('Stage:', ps[0])

        v = c.execute('SELECT sold FROM vehicles WHERE id=%s', (1,)).fetchone()
        print('Vehicle sold:', v, 'value:', v[0])

        # Test INSERT
        cur = c.execute("INSERT INTO sales(prospect_id,vehicle_id,seller_id,amount,status) VALUES(%s,%s,%s,%s,%s)", (114, 1, 1, 24990, 'completed'))
        print('Inserted, lastrowid:', cur.lastrowid)

        c.execute('UPDATE prospects SET stage=%s, outcome=%s WHERE id=%s', ('closed', 'won', 114))
        c.execute('UPDATE vehicles SET sold = sold + 1 WHERE id=%s', (1,))
        c.commit()
        print('All committed')
    except Exception as e:
        import traceback; traceback.print_exc()
