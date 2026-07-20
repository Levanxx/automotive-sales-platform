import json, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

class ScalableThreadingHTTPServer(ThreadingHTTPServer):
    request_queue_size = 256
    daemon_threads = True

class APIError(Exception):
    def __init__(self, status, message): self.status, self.message = status, message

class Handler(BaseHTTPRequestHandler):
    routes = {}
    def log_message(self, fmt, *args): pass
    def _send(self, status, body=None, content_type='application/json'):
        data = b'' if body is None else (json.dumps(body, ensure_ascii=False, default=str).encode() if content_type == 'application/json' else body)
        self.send_response(status); self.send_header('Content-Type', content_type); self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Headers','Content-Type');         self.send_header('Access-Control-Allow-Methods','GET,POST,PATCH,DELETE,OPTIONS')
        self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)
    def _body(self):
        try: return json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))) or b'{}')
        except (json.JSONDecodeError, ValueError): raise APIError(400, 'JSON inválido')
    def do_OPTIONS(self): self._send(204)
    def do_GET(self): self._dispatch('GET')
    def do_POST(self): self._dispatch('POST')
    def do_PATCH(self): self._dispatch('PATCH')
    def do_DELETE(self): self._dispatch('DELETE')
    def _dispatch(self, method):
        path = urlparse(self.path).path
        try:
            if path == '/health': return self._send(200, {'status':'ok'})
            for (verb, pattern), fn in self.routes.items():
                if verb != method: continue
                match = match_path(pattern, path)
                if match is not None: return self._send(*fn(self, **match))
            raise APIError(404, 'Ruta no encontrada')
        except APIError as e: self._send(e.status, {'error':e.message})
        except Exception as e: self._send(500, {'error':'Error interno','detail':str(e)})

def match_path(pattern, path):
    a,b=pattern.strip('/').split('/') if pattern.strip('/') else [], path.strip('/').split('/') if path.strip('/') else []
    if len(a)!=len(b): return None
    out={}
    for x,y in zip(a,b):
        if x.startswith('{'): out[x[1:-1]]=y
        elif x!=y: return None
    return out

def required(data, *fields):
    missing=[f for f in fields if data.get(f) in (None,'')]
    if missing: raise APIError(400, 'Campos requeridos: '+', '.join(missing))

def serve(handler, default_port):
    port=int(os.getenv('PORT', default_port)); print(f'Servicio listo en :{port}', flush=True)
    ScalableThreadingHTTPServer(('0.0.0.0',port),handler).serve_forever()
