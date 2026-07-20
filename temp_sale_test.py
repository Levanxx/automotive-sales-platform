from shared.db import connect

try:
    with connect() as c:
        cur = c.execute("INSERT INTO sales(prospect_id,vehicle_id,seller_id,amount,status) VALUES(49,1,1,24990,'completed') RETURNING id")
        rid = cur.lastrowid
        print('Inserted sale id:', rid)
        c.execute("UPDATE prospects SET stage='closed', outcome='won' WHERE id=49")
        c.execute("UPDATE vehicles SET sold = sold + 1 WHERE id=1")
        c.commit()
        print('Transaction committed')
except Exception as e:
    print('Error:', type(e).__name__, e)
