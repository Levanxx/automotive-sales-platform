"""Valida los workflows entregables de n8n Cloud sin conectarse a n8n."""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).parents[1]
WORKFLOW_DIR=ROOT/'n8n'
REQUIRED={
    'inactive-prospect-alert.json':{'n8n-nodes-base.scheduleTrigger','n8n-nodes-base.manualTrigger'},
    'service-sync.json':{'n8n-nodes-base.scheduleTrigger','n8n-nodes-base.manualTrigger'},
    'service-health-monitor.json':{'n8n-nodes-base.scheduleTrigger','n8n-nodes-base.manualTrigger'},
    'workflow-error-handler.json':{'n8n-nodes-base.errorTrigger'},
}

def validate_workflow(path,required_types):
    errors=[]
    try: workflow=json.loads(path.read_text())
    except (OSError,json.JSONDecodeError) as exc: return [f'JSON inválido: {exc}']
    if not workflow.get('name'): errors.append('falta name')
    nodes=workflow.get('nodes')
    if not isinstance(nodes,list) or len(nodes)<3: return errors+['debe contener al menos tres nodos']
    names=[node.get('name') for node in nodes]; ids=[node.get('id') for node in nodes]
    if len(names)!=len(set(names)): errors.append('hay nombres de nodos duplicados')
    if len(ids)!=len(set(ids)): errors.append('hay IDs de nodos duplicados')
    if any(not name for name in names): errors.append('hay nodos sin nombre')
    if any(not node.get('type') or node.get('typeVersion') is None for node in nodes): errors.append('hay nodos sin tipo o versión')
    node_types={node.get('type') for node in nodes}
    missing_types=required_types-node_types
    if missing_types: errors.append('faltan triggers: '+', '.join(sorted(missing_types)))
    node_names=set(names)
    connections=workflow.get('connections',{})
    for source,outputs in connections.items():
        if source not in node_names: errors.append(f'conexión desde nodo inexistente: {source}')
        for branches in outputs.values():
            for branch in branches:
                for target in branch:
                    if target.get('node') not in node_names: errors.append(f"conexión hacia nodo inexistente: {target.get('node')}")
    if workflow.get('active') is not False: errors.append('el template debe importarse inactivo')
    if workflow.get('settings',{}).get('timezone')!='America/Lima': errors.append('timezone debe ser America/Lima')
    serialized=json.dumps(workflow)
    for forbidden in ('$env','http://prospects:','http://sales:','http://insurance:','http://dashboard:','localhost'):
        if forbidden in serialized: errors.append(f'contiene referencia no válida para Cloud: {forbidden}')
    for node in nodes:
        if node.get('type')=='n8n-nodes-base.httpRequest':
            if node.get('parameters',{}).get('authentication')!='genericCredentialType': errors.append(f"{node['name']}: falta autenticación genérica")
            credential=node.get('credentials',{}).get('httpHeaderAuth',{})
            if credential.get('id')!='REEMPLAZAR_CREDENCIAL': errors.append(f"{node['name']}: el JSON no debe incluir una credencial real")
    return errors

def validate_all():
    errors={}
    actual={path.name for path in WORKFLOW_DIR.glob('*.json')}
    missing=set(REQUIRED)-actual
    if missing: errors['n8n/']=['faltan archivos: '+', '.join(sorted(missing))]
    for filename,types in REQUIRED.items():
        path=WORKFLOW_DIR/filename
        if path.exists():
            found=validate_workflow(path,types)
            if found: errors[filename]=found
    return errors

def main():
    errors=validate_all()
    if errors:
        for filename,messages in errors.items():
            for message in messages: print(f'✗ {filename}: {message}')
        return 1
    for filename in REQUIRED: print(f'✓ {filename}')
    print('Workflows n8n Cloud estructuralmente válidos y sin secretos.')
    return 0

if __name__=='__main__': sys.exit(main())
