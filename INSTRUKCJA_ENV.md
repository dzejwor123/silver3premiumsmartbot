# 🔐 INSTRUKCJA - BEZPIECZNE TOKENY I API

## ✅ **SYSTEM BEZPIECZEŃSTWA JUŻ SKONFIGUROWANY**

Bot jest już skonfigurowany do bezpiecznego używania zmiennych środowiskowych. Wszystkie wrażliwe dane są odczytywane z pliku `.env`, który jest ignorowany przez Git.

## 🚨 **PILNE - Utwórz plik .env**

### **KROK 1: Skopiuj szablon**
```bash
# W katalogu bota wykonaj:
copy env_template.txt .env
```

### **KROK 2: Edytuj plik .env**
Otwórz plik `.env` w notatniku i zamień przykładowe wartości na prawdziwe:

```env
# === KONFIGURACJA BEZPIECZEŃSTWA BOTA ===
# ZMIEŃ TE WARTOŚCI NA SWOJE PRAWDZIWE TOKENY!

# Token bota Telegram - UZYSKAJ NOWY TOKEN OD @BotFather
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Klucz API Google Gemini 2.5 Flash
GEMINI_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Klucz API AccuWeather (opcjonalny)
ACCUWEATHER_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Klucz API GIPHY
GIPHY_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ID administratorów (oddzielone przecinkami)
ADMIN_IDS=1456315126

# ID właściciela
OWNER_ID=1227822457
```

## 🔑 **Jak uzyskać tokeny:**

### **1. Token Telegram Bot:**
1. Idź do @BotFather w Telegram
2. Wyślij `/newbot` (nowy bot) lub `/mybots` -> wybierz istniejącego -> `/token`
3. Skopiuj token do `BOT_TOKEN=`

### **2. Klucz Google Gemini:**
1. Idź do https://makersuite.google.com/app/apikey
2. Zaloguj się i utwórz nowy klucz API
3. Skopiuj do `GEMINI_API_KEY=`

### **3. Klucz GIPHY (opcjonalny):**
1. Idź do https://developers.giphy.com/
2. Zarejestruj się i utwórz aplikację
3. Skopiuj klucz do `GIPHY_API_KEY=`

### **4. Klucz AccuWeather (opcjonalny):**
1. Idź do https://developer.accuweather.com/
2. Zarejestruj się i utwórz aplikację
3. Skopiuj klucz do `ACCUWEATHER_API_KEY=`

## 🛡️ **BEZPIECZEŃSTWO:**

### ✅ **Co jest chronione:**
- Plik `.env` jest w `.gitignore` - nie zostanie wysłany do Git
- Tokeny nie są w kodzie
- `bot_config.json` nie zawiera wrażliwych danych
- Kod odczytuje tokeny ze zmiennych środowiskowych

### ⚠️ **Ważne zasady:**
1. **NIGDY nie commituj pliku `.env`**
2. **NIGDY nie udostępniaj tokenów publicznie**
3. **Używaj różnych tokenów dla różnych środowisk**
4. **Regularnie zmieniaj tokeny**

## 🚀 **Uruchomienie:**

Po utworzeniu pliku `.env` z prawidłowymi tokenami:

```bash
python "SmartAI Bot.py"
```

Bot automatycznie:
- ✅ Sprawdzi czy plik `.env` istnieje
- ✅ Odczyta tokeny ze zmiennych środowiskowych
- ✅ Wyświetli informacje o konfiguracji
- ✅ Uruchomi się z bezpiecznymi danymi

## 🔍 **Weryfikacja:**

Bot wyświetli informacje o konfiguracji:
```
🤖 Uruchamianie bota w trybie: buddy_casual
🧠 Model AI: gemini-2.5-flash
🌡️ Temperature: 0.85
🎯 Max tokens: 2048
🔞 Kontrowersyjne opinie: ❌
🤬 Wulgarny język: ❌
```

Jeśli zobaczysz błędy o braku tokenów, sprawdź czy plik `.env` jest poprawnie utworzony! 