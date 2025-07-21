# 🔒 BEZPIECZEŃSTWO BOTA - INSTRUKCJE

## 🚨 PILNE! Konfiguracja bezpieczeństwa

### ✅ Co zostało zrobione:
1. **Utworzono `.gitignore`** - chroni wrażliwe pliki
2. **Dodano `python-dotenv`** - obsługa zmiennych środowiskowych
3. **Zmodyfikowano kod** - odczyt tokenów z `.env`
4. **Utworzono `env_template.txt`** - szablon konfiguracji
5. **Zabezpieczono `bot_config.json`** - usunięto wrażliwe dane

### 🔧 Co musisz zrobić TERAZ:

#### 1. Uzułnij plik `.env`:
```bash
# Otwórz plik .env w notatniku
notepad .env
```

**Zamień przykładowe wartości na prawdziwe:**
```
BOT_TOKEN=8136960047:AAHUC1dhVriicNUJ0U75Jkzb9i9CS7pheNE
GEMINI_API_KEY=AIzaSyBEzc_n4BuXl7YdrFzPjV7SyY3YcKaCK40
ACCUWEATHER_API_KEY=CTJQxR2LzJW1qJdtbSsAUX256UzfCfGJ
GIPHY_API_KEY=HQmZeiYaS0GszE7aynIqUIsPNQEwNFQW
ADMIN_IDS=1456315126
OWNER_ID=1227822457
```

#### 2. Zainstaluj nową zależność:
```bash
pip install python-dotenv
```

#### 3. Przetestuj bot:
```bash
python "SmartAI Bot.py"
```

### 🛡️ Co jest teraz bezpieczne:
- ✅ Tokeny nie są w kodzie
- ✅ `.env` jest ignorowany przez Git
- ✅ `bot_config.json` nie zawiera wrażliwych danych
- ✅ Kod odczytuje tokeny ze zmiennych środowiskowych

### ⚠️ Ważne zasady:
1. **NIGDY nie commituj pliku `.env`**
2. **NIGDY nie udostępniaj tokenów publicznie**
3. **Używaj różnych tokenów dla różnych środowisk**
4. **Regularnie zmieniaj tokeny**

### 🔄 Dla innych programistów:
1. Skopiuj `env_template.txt` jako `.env`
2. Uzułnij własne tokeny
3. Uruchom bota

### 🚀 Deployment (VPS/Heroku/Render):
- Ustaw zmienne środowiskowe w panelu hostingowym
- Nie potrzebujesz pliku `.env` na serwerze
- Tokeny będą odczytywane z systemowych zmiennych środowiskowych 