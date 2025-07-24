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
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                'status': 'healthy',
                'service': 'Silver3premiumsmartbot',
                'timestamp': time.time(),
                'port': int(os.environ.get('PORT', 10000)),
                'host': '0.0.0.0'
            }
            self.wfile.write(json.dumps(response).encode())
            print(f"✅ Health check OK - {self.path}")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
            print(f"❌ 404 - {self.path}")
    
    def log_message(self, format, *args):
        # Lepsze logowanie dla Render
        print(f"🌐 HTTP: {format % args}")

def start_http_server():
    """Uruchom serwer HTTP na porcie z zmiennej środowiskowej PORT"""
    port = int(os.environ.get('PORT', 10000))  # Render domyślny port
    
    try:
        # Ustaw timeout dla serwera
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        server.timeout = 120  # 120 sekund timeout
        print(f"🌐 Serwer HTTP uruchomiony na 0.0.0.0:{port}")
        print(f"🔗 Health check: http://0.0.0.0:{port}/health")
        print(f"⏱️ Timeout: {server.timeout} sekund")
        server.serve_forever()
    except OSError as e:
        print(f"❌ Błąd uruchamiania serwera HTTP: {e}")
        print("🔄 Uruchamiam tylko bota bez serwera HTTP...")
    except Exception as e:
        print(f"❌ Nieoczekiwany błąd serwera HTTP: {e}")
        print("🔄 Uruchamiam tylko bota bez serwera HTTP...")

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