#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt testowy do sprawdzenia połączenia z Telegram API
"""

import json
import asyncio
import httpx
from telegram import Bot
from telegram.error import NetworkError, TimedOut

async def test_telegram_connection():
    """Test połączenia z Telegram API"""
    
    # Wczytaj konfigurację
    try:
        with open('bot_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        token = config['bot_token']
        print(f"✅ Konfiguracja wczytana")
        print(f"🤖 Bot: {config.get('bot_username', 'Nieznany')}")
    except Exception as e:
        print(f"❌ Błąd wczytywania konfiguracji: {e}")
        return False
    
    # Test 1: Podstawowe połączenie HTTP
    print("\n🔍 Test 1: Podstawowe połączenie HTTP...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get('https://api.telegram.org')
            print(f"✅ Połączenie HTTP OK (status: {response.status_code})")
    except Exception as e:
        print(f"❌ Błąd połączenia HTTP: {e}")
        return False
    
    # Test 2: Telegram API
    print("\n🔍 Test 2: Telegram API...")
    try:
        bot = Bot(token=token)
        me = await bot.get_me()
        print(f"✅ Telegram API OK")
        print(f"   Bot: @{me.username}")
        print(f"   ID: {me.id}")
        print(f"   Nazwa: {me.first_name}")
    except TimedOut as e:
        print(f"❌ Timeout Telegram API: {e}")
        return False
    except NetworkError as e:
        print(f"❌ Błąd sieciowy Telegram API: {e}")
        return False
    except Exception as e:
        print(f"❌ Błąd Telegram API: {e}")
        return False
    
    # Test 3: Sprawdzenie webhook/polling
    print("\n🔍 Test 3: Sprawdzenie metod aktualizacji...")
    try:
        # Sprawdź czy bot może otrzymywać aktualizacje
        updates = await bot.get_updates(limit=1, timeout=5)
        print(f"✅ Polling działa (otrzymano {len(updates)} aktualizacji)")
    except Exception as e:
        print(f"⚠️ Ostrzeżenie - problem z polling: {e}")
    
    print("\n✅ Wszystkie testy zakończone pomyślnie!")
    return True

async def test_gemini_connection():
    """Test połączenia z Gemini API"""
    
    try:
        with open('bot_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        api_key = config.get('gemini_api_key', '')
        
        if not api_key:
            print("❌ Brak klucza Gemini API")
            return False
        
        print("\n🔍 Test Gemini API...")
        
        # Proste zapytanie testowe
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": "Powiedz 'Hello World' po polsku"
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 100
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Debug - struktura odpowiedzi: {list(data.keys())}")
                if 'candidates' in data and len(data['candidates']) > 0:
                    candidate = data['candidates'][0]
                    print(f"   Debug - struktura candidate: {list(candidate.keys())}")
                    if 'content' in candidate and 'parts' in candidate['content']:
                        text = candidate['content']['parts'][0]['text']
                        print(f"✅ Gemini API OK")
                        print(f"   Odpowiedź: {text[:50]}...")
                        return True
                    else:
                        print(f"❌ Nieprawidłowa struktura odpowiedzi Gemini API")
                        print(f"   Zawartość: {candidate}")
                        return False
                else:
                    print(f"❌ Brak candidates w odpowiedzi Gemini API")
                    print(f"   Zawartość: {data}")
                    return False
            else:
                print(f"❌ Błąd Gemini API (status: {response.status_code})")
                print(f"   Odpowiedź: {response.text[:200]}...")
                return False
                
    except Exception as e:
        print(f"❌ Błąd testu Gemini API: {e}")
        return False

async def main():
    """Główna funkcja testowa"""
    print("=" * 50)
    print("🔧 Test połączeń Bot Kumpel")
    print("=" * 50)
    
    # Test Telegram
    telegram_ok = await test_telegram_connection()
    
    # Test Gemini
    gemini_ok = await test_gemini_connection()
    
    print("\n" + "=" * 50)
    print("📊 WYNIKI TESTÓW:")
    print(f"   Telegram API: {'✅ OK' if telegram_ok else '❌ BŁĄD'}")
    print(f"   Gemini API: {'✅ OK' if gemini_ok else '❌ BŁĄD'}")
    
    if telegram_ok and gemini_ok:
        print("\n🎉 Wszystko działa! Możesz uruchomić bota.")
    else:
        print("\n⚠️ Wykryto problemy. Sprawdź konfigurację i połączenie.")
    
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main()) 