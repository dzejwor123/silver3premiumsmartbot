#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prosty serwer HTTP dla Render
Nasłuchuje na porcie z zmiennej środowiskowej PORT
"""

import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'status': 'healthy',
                'service': 'Silver3premiumsmartbot',
                'timestamp': time.time()
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def log_message(self, format, *args):
        # Wyłącz logowanie żądań HTTP
        pass

def start_http_server():
    """Uruchom serwer HTTP na porcie z zmiennej środowiskowej PORT"""
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"🌐 Serwer HTTP uruchomiony na porcie {port}")
    server.serve_forever()

def main():
    """Główna funkcja - uruchom serwer HTTP w tle"""
    # Uruchom serwer HTTP w osobnym wątku
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()
    
    # Uruchom bota
    import subprocess
    import sys
    subprocess.run([sys.executable, "SmartAI Bot.py"])

if __name__ == '__main__':
    main() 