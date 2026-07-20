import os, random, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from shared.db import initialize, execute, query
def main():
    initialize()
    if query('SELECT id FROM prospects LIMIT 1'): print('Ya existen datos; no se duplicaron.'); return
    stages=['initial','qualification','negotiation','closed','closed']; names=['Carla Díaz','Marco Ruiz','Elena Soto','Diego León','Rosa Paredes','José Silva','Lucía Ramos','Paolo Cruz']
    for i,name in enumerate(names):
        stage=stages[i%len(stages)]; outcome=('won' if i%2==0 else 'lost') if stage=='closed' else None
        vehicle_id=random.choice([1,2,3])
        pid=execute('INSERT INTO prospects(name,email,phone,vehicle_id,stage,seller_id,outcome,loss_reason) VALUES(?,?,?,?,?,?,?,?)',(name,f'demo{i+1}@mail.pe',f'999000{i+1:03d}',vehicle_id,stage,1+i%2,outcome,'Presupuesto' if outcome=='lost' else None))
        if i==0: execute("UPDATE prospects SET last_activity=datetime('now','-5 days') WHERE id=?",(pid,))
        execute("INSERT OR IGNORE INTO prospect_stage_history(prospect_id,stage) VALUES(?,?)",(pid,'initial'))
        if stage!='initial': execute('INSERT OR IGNORE INTO prospect_stage_history(prospect_id,stage) VALUES(?,?)',(pid,stage))
        if outcome:
            sid=execute('INSERT INTO sales(prospect_id,vehicle_id,seller_id,amount,status,loss_reason) VALUES(?,?,?,?,?,?)',(pid,vehicle_id,1+i%2,24000+i*600,'completed' if outcome=='won' else 'failed','Presupuesto' if outcome=='lost' else None))
            if outcome=='won':
                execute('UPDATE vehicles SET sold=1 WHERE id=?',(vehicle_id,))
                execute('INSERT INTO insurance(sale_id,type,expected_premium,actual_premium,status) VALUES(?,?,?,?,?)',(sid,'Todo riesgo',1250,1190,'sold'))
    print('Datos de demostración creados.')
if __name__=='__main__': main()
