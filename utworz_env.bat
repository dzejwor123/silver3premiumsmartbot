@echo off
echo ========================================
echo    UTWORZENIE PLIKU .env
echo ========================================
echo.

REM Sprawdź czy plik .env już istnieje
if exist .env (
    echo ⚠️  Plik .env już istnieje!
    echo Czy chcesz go nadpisać? (t/n)
    set /p choice=
    if /i "%choice%"=="t" (
        echo ✅ Nadpisuję plik .env...
    ) else (
        echo ❌ Anulowano. Plik .env nie został zmieniony.
        pause
        exit /b
    )
)

REM Skopiuj szablon
echo 📋 Kopiuję szablon env_template.txt jako .env...
copy env_template.txt .env >nul

if exist .env (
    echo ✅ Plik .env został utworzony!
    echo.
    echo 🚨 WAŻNE: Edytuj plik .env i wstaw prawdziwe tokeny:
    echo.
    echo 1. Otwórz plik .env w notatniku:
    echo    notepad .env
    echo.
    echo 2. Zamień przykładowe wartości na prawdziwe tokeny
    echo 3. Zapisz plik
    echo.
    echo 📖 Szczegółowe instrukcje w pliku INSTRUKCJA_ENV.md
    echo.
    echo Czy chcesz otworzyć plik .env teraz? (t/n)
    set /p open_choice=
    if /i "%open_choice%"=="t" (
        notepad .env
    )
) else (
    echo ❌ Błąd: Nie udało się utworzyć pliku .env
    echo Sprawdź czy plik env_template.txt istnieje.
)

echo.
echo ========================================
pause 