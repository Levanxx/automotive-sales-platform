"""Verificación end-to-end para un entorno Docker ya iniciado."""
import json, sys
from pathlib import Path
from urllib.request import urlopen

TARGETS={
    'prospectos':'http://localhost:8001/health',
    'ventas':'http://localhost:8002/health',
    'seguros':'http://localhost:8003/health',
    'dashboard':'http://localhost:8004/health',
}

def main():
    failures=[]
    for name,url in TARGETS.items():
        try:
            with urlopen(url,timeout=5) as response:
                data=json.load(response)
                ok=response.status==200 and data.get('status')=='ok'
        except Exception as exc:
            ok=False; failures.append(f'{name}: {exc}')
        print(('✓' if ok else '✗'),name)
    workflows=list((Path(__file__).parents[1]/'n8n').glob('*.json'))
    for path in workflows:
        try: json.loads(path.read_text()); print('✓ workflow',path.name)
        except Exception as exc: failures.append(f'{path.name}: {exc}')
    if failures:
        print('\nErrores:\n- '+'\n- '.join(failures)); return 1
    print('\nIntegración lista: 4 servicios y workflows válidos.'); return 0

if __name__=='__main__': sys.exit(main())
