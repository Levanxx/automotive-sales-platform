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
        pid=execute('INSERT INTO prospects(name,email,phone,vehicle_interest,stage,seller_id,outcome,loss_reason) VALUES(?,?,?,?,?,?,?,?)',(name,f'demo{i+1}@mail.pe',f'999000{i+1:03d}',random.choice(['Toyota Corolla','Kia Sportage','Hyundai Tucson']),stage,1+i%2,outcome,'Presupuesto' if outcome=='lost' else None))
        if outcome:
            sid=execute('INSERT INTO sales(prospect_id,vehicle_id,seller_id,amount,status,loss_reason) VALUES(?,?,?,?,?,?)',(pid,1+i%3,1+i%2,24000+i*600,'completed' if outcome=='won' else 'failed','Presupuesto' if outcome=='lost' else None))
            if outcome=='won': execute('INSERT INTO insurance(sale_id,type,expected_premium,actual_premium,status) VALUES(?,?,?,?,?)',(sid,'Todo riesgo',1250,1190,'sold'))
    print('Datos de demostración creados.')
if __name__=='__main__': main()

