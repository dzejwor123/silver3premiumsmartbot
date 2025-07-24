#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bardzo prosty serwer HTTP tylko dla Render health check
"""

import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                'status': 'healthy',
                'service': 'Silver3premiumsmartbot',
                'timestamp': time.time(),
                'port': int(os.environ.get('PORT', 10000))
            }
            self.wfile.write(json.dumps(response).encode())
            print(f"✅ Health check OK")
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>Silver3premiumsmartbot is running!</h1>')
    
    def log_message(self, format, *args):
        print(f"🌐 HTTP: {format % args}")

def main():
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Uruchamianie prostego serwera na porcie {port}")
    
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    print(f"🌐 Serwer uruchomiony na 0.0.0.0:{port}")
    print(f"🔗 Health check: http://0.0.0.0:{port}/health")
    
    server.serve_forever()

if __name__ == '__main__':
    main() 