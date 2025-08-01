#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prosty serwer HTTP dla Render
Nasłuchuje na porcie z zmiennej środowiskowej PORT
"""

import os
import threading
import time
import signal
import sys
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
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
            print(f"❌ 404 - {self.path}")
    
    def log_message(self, format, *args):
        # Lepsze logowanie dla Render
        print(f"🌐 HTTP: {format % args}")

def signal_handler(signum, frame):
    """Obsługa sygnałów dla graceful shutdown"""
    print(f"\n🛑 Otrzymano sygnał {signum}, zatrzymuję serwer...")
    sys.exit(0)

def start_bot():
    """Uruchom bota w osobnym wątku"""
    try:
        import subprocess
        import sys
        print("🤖 Uruchamianie głównego bota...")
        subprocess.run([sys.executable, "SmartAI Bot.py"])
    except Exception as e:
        print(f"❌ Błąd uruchamiania bota: {e}")

def main():
    """Główna funkcja - uruchom serwer HTTP w głównym wątku"""
    print("🚀 Uruchamianie Silver3premiumsmartbot...")
    print(f"🔧 Port: {os.environ.get('PORT', 10000)}")
    print(f"🌍 Host: 0.0.0.0")
    
    port = int(os.environ.get('PORT', 10000))
    
    try:
        # Uruchom bota w osobnym wątku (nie daemon)
        bot_thread = threading.Thread(target=start_bot)
        bot_thread.daemon = False
        bot_thread.start()
        
        # Krótkie opóźnienie aby bot się uruchomił
        time.sleep(3)
        
        # Uruchom serwer HTTP w głównym wątku
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        server.timeout = 300  # 300 sekund timeout dla Render
        server.socket.settimeout(300)  # Dodatkowy timeout dla socket
        
        print(f"🌐 Serwer HTTP uruchomiony na 0.0.0.0:{port}")
        print(f"🔗 Health check: http://0.0.0.0:{port}/health")
        print(f"⏱️ Timeout: {server.timeout} sekund")
        print(f"🔄 Render mode: {os.environ.get('RENDER', 'false')}")
        
        # Rejestruj handler sygnałów
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Serwer HTTP w głównym wątku - to jest kluczowe dla Render
        server.serve_forever()
        
    except OSError as e:
        print(f"❌ Błąd uruchamiania serwera HTTP: {e}")
        print("🔄 Uruchamiam tylko bota bez serwera HTTP...")
        # Jeśli serwer się nie uruchomi, uruchom tylko bota
        start_bot()
    except Exception as e:
        print(f"❌ Nieoczekiwany błąd: {e}")
        print("🔄 Uruchamiam tylko bota...")
        start_bot()

if __name__ == '__main__':
    main() 