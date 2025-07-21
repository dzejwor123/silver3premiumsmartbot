#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prosty serwer HTTP dla Render
Uruchamia bota Telegram w tle i serwuje status na porcie
"""

import os
import threading
import time
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

# Port z zmiennej środowiskowej Render
PORT = int(os.environ.get('PORT', 10000))

class BotStatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Bot Kumpel - Status</title>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; background: #f0f0f0; }
                    .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    .status { padding: 15px; border-radius: 5px; margin: 10px 0; }
                    .online { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
                    .offline { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
                    h1 { color: #333; }
                    .emoji { font-size: 24px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1><span class="emoji">🤖</span> Bot Kumpel - Status</h1>
                    <div class="status online">
                        <strong>✅ Bot jest aktywny!</strong><br>
                        Bot Telegram działa w tle i odpowiada na wiadomości.
                    </div>
                    <p><strong>Username:</strong> @GrokStyleBot</p>
                    <p><strong>Status:</strong> Online i gotowy do działania</p>
                    <p><strong>Render:</strong> Background Worker</p>
                    <hr>
                    <p><small>Strona statusu dla Render.com - Bot działa jako usługa w tle</small></p>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
            
        elif self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            status = {
                "bot_name": "Bot Kumpel",
                "status": "online",
                "username": "@GrokStyleBot",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "render_service": "background_worker"
            }
            
            self.wfile.write(json.dumps(status, ensure_ascii=False).encode('utf-8'))
            
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 - Not Found')

def run_bot():
    """Uruchom bota w osobnym wątku"""
    try:
        print("🤖 Uruchamiam Bota Kumpla...")
        subprocess.run([sys.executable, "SmartAI Bot.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Błąd uruchomienia bota: {e}")
    except KeyboardInterrupt:
        print("⏹️ Przerwano działanie bota")

def run_server():
    """Uruchom serwer HTTP"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), BotStatusHandler)
        print(f"🌐 Serwer HTTP uruchomiony na porcie {PORT}")
        print(f"📱 Status dostępny pod: http://localhost:{PORT}")
        server.serve_forever()
    except KeyboardInterrupt:
        print("⏹️ Zatrzymuję serwer HTTP")
        server.shutdown()

def main():
    """Główna funkcja"""
    print("🚀 Uruchamiam Bot Kumpel z serwerem HTTP dla Render...")
    
    # Sprawdź czy istnieje główny plik bota
    if not os.path.exists("SmartAI Bot.py"):
        print("❌ Brak pliku SmartAI Bot.py")
        sys.exit(1)
    
    # Uruchom bota w osobnym wątku
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Uruchom serwer HTTP
    run_server()

if __name__ == "__main__":
    main() 