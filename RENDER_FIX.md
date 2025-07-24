# 🔧 NAPRAWA DEPLOYMENTU RENDER - INSTRUKCJE

## 🚨 **PILNE - Problem z deploymentem**

Błąd: `Fix Render host/port configuration: Use 0.0.0.0:10000 with proper timeouts`

## ✅ **Co zostało naprawione:**

### 1. **Konfiguracja portów** 🔧
- Ujednolicono port na `10000` we wszystkich plikach
- Dodano prawidłowe ustawienia `EXPOSE 10000` w Dockerfile
- Naprawiono konfigurację `render.yaml`

### 2. **Serwer HTTP** 🌐
- Zwiększono timeout do 300 sekund (wymagane przez Render)
- Dodano obsługę sygnałów dla graceful shutdown
- Poprawiono health check endpoint `/health`
- Dodano lepsze logowanie i obsługę błędów

### 3. **Zmienne środowiskowe** ⚙️
- Dodano `RENDER=true` dla wykrycia środowiska
- Ustawiono `PYTHONUNBUFFERED=1` dla lepszych logów
- Dodano `PYTHONDONTWRITEBYTECODE=1` dla optymalizacji

## 🚀 **Instrukcje deploymentu:**

### **Opcja A: Web Service (zalecane)**
```bash
# Użyj głównej konfiguracji
render.yaml
```

### **Opcja B: Worker Service (alternatywa)**
```bash
# Jeśli web service nie działa, użyj worker
render_worker.yaml
```

## 🔍 **Testowanie przed deploymentem:**

### 1. **Uruchom test lokalny:**
```bash
python test_render.py
```

### 2. **Sprawdź zmienne środowiskowe:**
- `BOT_TOKEN` - token bota Telegram
- `GEMINI_API_KEY` - klucz API Gemini
- `PORT` - port 10000 (automatycznie ustawiony)

### 3. **Sprawdź pliki konfiguracyjne:**
- `render.yaml` - główna konfiguracja
- `server.py` - serwer HTTP
- `Dockerfile` - konfiguracja kontenera

## 📋 **Kroki deploymentu:**

### 1. **Przygotuj repozytorium:**
```bash
git add .
git commit -m "Fix Render deployment configuration"
git push origin main
```

### 2. **W Render Dashboard:**
1. Wybierz projekt `silver3premiumsmartbot`
2. Sprawdź czy używa `render.yaml`
3. Ustaw zmienne środowiskowe:
   - `BOT_TOKEN`
   - `GEMINI_API_KEY`
   - `ACCUWEATHER_API_KEY` (opcjonalne)
   - `GIPHY_API_KEY` (opcjonalne)
   - `ADMIN_IDS` (opcjonalne)
   - `OWNER_ID` (opcjonalne)

### 3. **Deploy:**
- Kliknij "Manual Deploy" -> "Deploy latest commit"
- Poczekaj na zakończenie build process
- Sprawdź logi deploymentu

## 🔍 **Diagnostyka problemów:**

### **Problem: Port scan timeout**
**Rozwiązanie:**
- Sprawdź czy `server.py` uruchamia się poprawnie
- Sprawdź czy port 10000 jest eksponowany
- Sprawdź logi w Render Dashboard

### **Problem: Health check failed**
**Rozwiązanie:**
- Sprawdź endpoint `/health`
- Sprawdź czy serwer HTTP odpowiada
- Sprawdź timeouty w konfiguracji

### **Problem: Bot not starting**
**Rozwiązanie:**
- Sprawdź zmienne środowiskowe
- Sprawdź logi bota
- Użyj `render_worker.yaml` jako alternatywę

## 📊 **Monitoring:**

### **Sprawdź logi:**
```bash
# W Render Dashboard -> Logs
# Szukaj błędów związanych z:
# - Port binding
# - Health check
# - Bot startup
```

### **Test health check:**
```bash
# Po deploymentu sprawdź:
curl https://twoj-bot.onrender.com/health
```

## 🆘 **Jeśli nadal nie działa:**

### **Opcja 1: Worker Service**
```bash
# Zmień typ service na worker w Render Dashboard
# Lub użyj render_worker.yaml
```

### **Opcja 2: Sprawdź tokeny**
```bash
# Uruchom test lokalny
python test_connection.py
```

### **Opcja 3: Kontakt z supportem**
- Zbierz logi z Render Dashboard
- Przygotuj informacje o konfiguracji
- Opisz dokładnie błąd

## ✅ **Po udanym deploymentzie:**

1. **Sprawdź health check:** `https://twoj-bot.onrender.com/health`
2. **Testuj bota:** Wyślij `/start` w Telegram
3. **Monitoruj logi:** Sprawdź czy bot działa stabilnie
4. **Ustaw auto-deploy:** Włącz automatyczne deploymenty

## 📝 **Uwagi:**
- Render wymaga web service z health check
- Worker service nie wymaga portów, ale ma ograniczenia
- Zawsze sprawdzaj logi po deploymentzie
- Używaj testów przed deploymentem 