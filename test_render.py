#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt testowy dla Render - sprawdza konfigurację przed deploymentem
"""

import os
import sys
import json
import asyncio
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

def test_environment():
    """Test zmiennych środowiskowych"""
    print("🔍 Test 1: Zmienne środowiskowe...")
    
    required_vars = ['BOT_TOKEN', 'GEMINI_API_KEY']
    optional_vars = ['ACCUWEATHER_API_KEY', 'GIPHY_API_KEY', 'ADMIN_IDS', 'OWNER_ID']
    
    # Sprawdź wymagane zmienne
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('TWÓJ_'):
            print(f"❌ Brak {var}")
            return False
        else:
            print(f"✅ {var}: OK")
    
    # Sprawdź opcjonalne zmienne
    for var in optional_vars:
        value = os.getenv(var)
        if value and not value.startswith('TWÓJ_'):
            print(f"✅ {var}: OK")
        else:
            print(f"⚠️ {var}: Brak (opcjonalne)")
    
    return True

def test_port_configuration():
    """Test konfiguracji portów"""
    print("\n🔍 Test 2: Konfiguracja portów...")
    
    port = os.getenv('PORT', '10000')
    try:
        port_int = int(port)
        print(f"✅ Port: {port_int}")
        return port_int
    except ValueError:
        print(f"❌ Nieprawidłowy port: {port}")
        return None

def test_http_server():
    """Test serwera HTTP"""
    print("\n🔍 Test 3: Serwer HTTP...")
    
    port = test_port_configuration()
    if not port:
        return False
    
    try:
        # Prosty test serwera HTTP
        server = HTTPServer(('0.0.0.0', port), BaseHTTPRequestHandler)
        server.timeout = 5
        print(f"✅ Serwer HTTP może nasłuchiwać na 0.0.0.0:{port}")
        server.server_close()
        return True
    except Exception as e:
        print(f"❌ Błąd serwera HTTP: {e}")
        return False

def test_python_imports():
    """Test importów Python"""
    print("\n🔍 Test 4: Importy Python...")
    
    required_modules = [
        'telegram',
        'google.generativeai',
        'aiohttp',
        'httpx',
        'feedparser',
        'apscheduler',
        'pytz',
        'dotenv'
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}: OK")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            return False
    
    return True

def test_bot_config():
    """Test konfiguracji bota"""
    print("\n🔍 Test 5: Konfiguracja bota...")
    
    try:
        with open('bot_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("✅ bot_config.json: OK")
        return True
    except FileNotFoundError:
        print("⚠️ bot_config.json: Brak (używam zmiennych środowiskowych)")
        return True
    except Exception as e:
        print(f"❌ bot_config.json: {e}")
        return False

def main():
    """Główna funkcja testowa"""
    print("🚀 Test konfiguracji Render dla Silver3premiumsmartbot")
    print("=" * 60)
    
    tests = [
        test_environment,
        test_port_configuration,
        test_http_server,
        test_python_imports,
        test_bot_config
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Błąd testu: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Wyniki: {passed}/{total} testów przeszło")
    
    if passed == total:
        print("✅ Wszystkie testy przeszły! Bot gotowy do deploymentu.")
        return True
    else:
        print("❌ Niektóre testy nie przeszły. Sprawdź konfigurację.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 