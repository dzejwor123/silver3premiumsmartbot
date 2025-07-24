#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prosty serwer HTTP dla Render - naprawiony
Nasłuchuje na porcie z zmiennej środowiskowej PORT
"""

import os
import time
import signal
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            response = {
                'status': 'healthy',
                'service': 'Silver3premiumsmartbot',
                'timestamp': time.time(),
                'port': int(os.environ.get('PORT', 10000)),
                'host': '0.0.0.0',
                'render': os.environ.get('RENDER', 'false')
            }
            self.wfile.write(json.dumps(response).encode())
            print(f"✅ Health check OK - {self.path}")
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
            <html>
            <head><title>Silver3premiumsmartbot</title></head>
            <body>
            <h1>🤖 Silver3premiumsmartbot</h1>
            <p>Bot jest uruchomiony i działa!</p>
            <p><a href="/health">Health Check</a></p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
            print(f"❌ 404 - {self.path}")
    
    def log_message(self, format, *args):
        print(f"🌐 HTTP: {format % args}")

def signal_handler(signum, frame):
    print(f"\n🛑 Otrzymano sygnał {signum}, zatrzymuję serwer...")
    sys.exit(0)

def start_bot():
    """Uruchom bota w osobnym wątku"""
    try:
        import subprocess
        print("🤖 Uruchamianie głównego bota...")
        subprocess.run([sys.executable, "SmartAI Bot.py"])
    except Exception as e:
        print(f"❌ Błąd uruchamiania bota: {e}")

def main():
    """Główna funkcja"""
    print("🚀 Uruchamianie Silver3premiumsmartbot dla Render...")
    
    port = int(os.environ.get('PORT', 10000))
    print(f"🔧 Port: {port}")
    print(f"🌍 Host: 0.0.0.0")
    
    # Uruchom bota w osobnym wątku
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    # Krótkie opóźnienie
    time.sleep(2)
    
    try:
        # Uruchom serwer HTTP w głównym wątku
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        server.timeout = 300
        
        print(f"🌐 Serwer HTTP uruchomiony na 0.0.0.0:{port}")
        print(f"🔗 Health check: http://0.0.0.0:{port}/health")
        print(f"🔄 Render mode: {os.environ.get('RENDER', 'false')}")
        
        # Rejestruj handler sygnałów
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Serwer HTTP w głównym wątku - kluczowe dla Render
        server.serve_forever()
        
    except Exception as e:
        print(f"❌ Błąd serwera HTTP: {e}")
        # Jeśli serwer się nie uruchomi, uruchom tylko bota
        start_bot()

if __name__ == '__main__':
    main() 