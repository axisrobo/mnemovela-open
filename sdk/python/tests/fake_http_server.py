from __future__ import annotations

import contextlib
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # silence
        pass

    def do_POST(self):
        length = int(self.headers.get("content-length", 0))
        req = json.loads(self.rfile.read(length) or b"{}")
        rid, method, params = req.get("id"), req.get("method", ""), req.get("params", {})
        if method == "mnemovela.add_episode":
            result = {"commit_id": "mem_1", "branch_name": params.get("branch_name")}
            body = {"jsonrpc": "2.0", "id": rid, "result": result}
        elif method == "mnemovela.search_memory":
            body = {"jsonrpc": "2.0", "id": rid, "result": [{"score": 0.9}, {"score": 0.5}]}
        elif method == "mnemovela.list_branches":
            body = {"jsonrpc": "2.0", "id": rid, "result": [{"branch_name": "main", "head_sequence": 3}]}
        else:
            body = {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "method not found"}}
        data = json.dumps(body).encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


@contextlib.contextmanager
def serve_http():
    server = HTTPServer(("localhost", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://localhost:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()
