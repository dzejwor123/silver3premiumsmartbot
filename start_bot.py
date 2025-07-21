#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt uruchomieniowy dla VPS
Uruchamia Bota Kumpla z automatycznym restartem w przypadku błędów
"""

import sys
import time
import subprocess
import logging
import os
from datetime import datetime

# Konfiguracja logowania dla skryptu uruchomieniowego
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - STARTER - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot_starter.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_python_version():
    """Sprawdź wersję Pythona"""
    if sys.version_info < (3, 8):
        logger.error(f"❌ Python 3.8+ wymagany. Obecna wersja: {sys.version}")
        sys.exit(1)
    logger.info(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

def install_requirements():
    """Zainstaluj wymagane pakiety"""
    try:
        logger.info("📦 Sprawdzam wymagane pakiety...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        logger.info("✅ Pakiety zainstalowane")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Błąd instalacji pakietów: {e}")
        sys.exit(1)
    except FileNotFoundError:
        logger.warning("⚠️ Brak pliku requirements.txt")

def run_bot():
    """Uruchom bot z automatycznym restartem"""
    restart_count = 0
    max_restarts = 10
    restart_delay = 30  # sekund
    
    while restart_count < max_restarts:
        try:
            logger.info(f"🚀 Uruchamiam Bota Kumpla (restart #{restart_count})")
            
            # Uruchom bot
            process = subprocess.Popen([
                sys.executable, 'SmartAI Bot.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Czekaj na zakończenie procesu
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                logger.info("✅ Bot zakończył pracę normalnie")
                break
            else:
                logger.error(f"❌ Bot zakończył się błędem (kod: {process.returncode})")
                if stderr:
                    logger.error(f"Błąd: {stderr}")
                
                restart_count += 1
                if restart_count < max_restarts:
                    logger.info(f"⏳ Restart za {restart_delay} sekund...")
                    time.sleep(restart_delay)
                    restart_delay = min(restart_delay * 1.5, 300)  # Max 5 minut
                    
        except KeyboardInterrupt:
            logger.info("⏹️ Przerwano przez użytkownika")
            break
        except Exception as e:
            logger.error(f"❌ Nieoczekiwany błąd: {e}")
            restart_count += 1
            if restart_count < max_restarts:
                time.sleep(restart_delay)
    
    if restart_count >= max_restarts:
        logger.error(f"❌ Przekroczono maksymalną liczbę restartów ({max_restarts})")
        sys.exit(1)

def main():
    """Główna funkcja"""
    logger.info("=" * 50)
    logger.info("🤖 Bot Kumpel Starter")
    logger.info(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)
    
    # Sprawdź środowisko
    check_python_version()
    
    # Zainstaluj pakiety jeśli potrzeba
    if len(sys.argv) > 1 and sys.argv[1] == '--install':
        install_requirements()
    
    # Sprawdź czy istnieją wymagane pliki
    required_files = ['SmartAI Bot.py', 'bot_config.json']
    for file in required_files:
        if not os.path.exists(file):
            logger.error(f"❌ Brak wymaganego pliku: {file}")
            sys.exit(1)
    
    # Utwórz katalog logs
    os.makedirs('logs', exist_ok=True)
    
    # Uruchom bot
    run_bot()

if __name__ == "__main__":
    main()