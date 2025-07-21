@echo off
chcp 65001 >nul
title Bot Kumpel - MEGA BOT LAUNCHER
color 0A

echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║                                                                          ║
echo ║    🔥🤖 BOT KUMPEL - NAJLEPSZY AI NA TELEGRAMIE! 🤖🔥                 ║
echo ║                                                                          ║
echo ║          ⚡ GOTOWY NA KAŻDE WYZWANIE ⚡                                 ║
echo ║          💪 LUŹNY • INTELIGENTNY • SZYBKI 💪                    ║
echo ║                                                                          ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.
echo 🚀 INICJOWANIE SYSTEMU...

echo.
echo [1/5] 🔍 SPRAWDZANIE PLIKÓW BOTA...
if not exist "SmartAI Bot.py" (
    echo ❌ KRITYCZNY BŁĄD: Nie znaleziono głównego pliku bota!
    echo 📁 Sprawdź czy jesteś w odpowiednim katalogu.
    pause
    exit /b 1
)
echo       ✅ Bot Kumpel.py - ZNALEZIONY
echo.

echo [2/5] 🐍 WERYFIKACJA PYTHONA...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ BŁĄD: Python nie jest zainstalowany!
    echo 🐍 Pobierz Python 3.10+ z python.org
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set pythonver=%%i
echo       ✅ Python %pythonver% - READY
echo.

echo [3/5] ⚙️  SPRAWDZANIE KONFIGURACJI...
if not exist "bot_config.json" (
    echo ❌ BŁĄD: Brak pliku konfiguracyjnego!
    echo 📄 Utwórz plik bot_config.json
    pause
    exit /b 1
)
echo       ✅ bot_config.json - LOADED
echo.

echo [4/5] 📦 INICJALIZACJA BIBLIOTEK...
python -c "import telegram" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  INSTALOWANIE ZALEŻNOŚCI...
    pip install -r Requirements.txt
    if errorlevel 1 (
        echo ❌ BŁĄD: Nie udało się zainstalować bibliotek!
        pause
        exit /b 1
    )
)
echo       ✅ Wszystkie biblioteki - LOADED
echo.

echo [5/5] 🚀 URUCHAMIANIE AI BEAST MODE...
echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║                     🔥 BOT GOTOWY DO AKCJI! 🔥                         ║
echo ║                                                                          ║
echo ║  💡 STEROWANIE:                                                         ║
echo ║     • Ctrl+C - Zatrzymaj bota                                           ║
echo ║     • Zamknij okno - Kill process                                       ║
echo ║                                                                          ║
echo ║  📊 FUNKCJE:                                                            ║
echo ║     • AI Chat ⚡ RSS News 📰 Weather 🌤️ Web Search 🌐               ║
echo ║                                                                          ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.

python "SmartAI Bot.py"

echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║                      ⚠️  BOT ZATRZYMANY ⚠️                             ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
pause 