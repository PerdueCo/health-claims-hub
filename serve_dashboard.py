#!/usr/bin/env python3
"""
MECP Dashboard Server
Serves dashboard.html and proxies API calls to MarkLogic to avoid CORS issues.
Usage: python serve_dashboard.py
Then open: http://localhost:8888/dashboard.html
"""
import http.server
import urllib.request
import urllib.error
import base64
import json
import os

PORT = 8888
ML_HOST = "http://localhost:8040"
ML_USER = "admin"
ML_PASS = "admin123"
AUTH = "Basic " + base64.b64encode(f"{ML_USER}:{ML_PASS}".encode()).decode()

class DashboardHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        # Proxy all /api/ requests to MarkLogic
        if self.path.startswith("/api/"):
            self.proxy_to_marklogic()
        else:
            super().do_GET()

    def proxy_to_marklogic(self):
        # Strip /api prefix and forward to MarkLogic
        ml_path = self.path[4:]  # remove /api
        ml_url  = ML_HOST + ml_path

        try:
            req  = urllib.request.Request(ml_url, headers={"Authorization": AUTH})
            resp = urllib.request.urlopen(req, timeout=10)
            data = resp.read()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)

        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def log_message(self, fmt, *args):
        # Cleaner log output
        print(f"  {self.address_string()} {args[0]} {args[1]}")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else ".")
    print("=" * 50)
    print("  MECP Dashboard Server")
    print(f"  http://localhost:{PORT}/dashboard.html")
    print("  Press Ctrl+C to stop")
    print("=" * 50)
    with http.server.HTTPServer(("", PORT), DashboardHandler) as httpd:
        httpd.serve_forever()
