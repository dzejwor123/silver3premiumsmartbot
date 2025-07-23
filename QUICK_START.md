# ⚡ SZYBKI START - Silver3premiumsmartbot na VPS

## 🚀 Najszybsza instalacja (Ubuntu/Debian)

### **1. Przygotowanie:**
```bash
# Połącz się z VPS przez SSH
ssh username@your-vps-ip

# Aktualizuj system
sudo apt update && sudo apt upgrade -y

# Zainstaluj Python 3.12
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update && sudo apt install python3.12 python3.12-venv python3.12-pip git screen -y
```

### **2. Pobierz bota:**
```bash
# Utwórz katalog
mkdir ~/silver-bot && cd ~/silver-bot

# Upload plików przez SCP/SFTP:
# - SmartAI Bot.py
# - bot_config.json
# - start_bot.py  
# - requirements.txt
```

### **3. Konfiguracja:**
```bash
# WAŻNE: Edytuj bot_config.json!
nano bot_config.json
# Zmień: bot_token, gemini_api_key, admin_ids, owner_id

# Utwórz środowisko Python
python3.12 -m venv bot_env
source bot_env/bin/activate
pip install -r requirements.txt
```

### **4. Uruchom:**
```bash
# Test
python3 start_bot.py

# W tle (Screen)
screen -S bot
python3 start_bot.py
# Ctrl+A, D (odłącz)

# Powrót do sesji
screen -r bot
```

---

## 🔧 SYSTEMD (Auto-start)

### **Utwórz serwis:**
```bash
sudo nano /etc/systemd/system/bot-kumpel.service
```

**Zawartość (ZMIEŃ `username`):**
```ini
[Unit]
Description=Silver3premiumsmartbot
After=network.target

[Service]
Type=simple
User=username
WorkingDirectory=/home/username/silver-bot
Environment=PATH=/home/username/silver-bot/bot_env/bin
ExecStart=/home/username/silver-bot/bot_env/bin/python start_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### **Aktywuj:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable silver-bot.service
sudo systemctl start silver-bot.service
sudo systemctl status silver-bot.service
```

---

## 🐳 DOCKER (Alternatywa)

```bash
# Build
docker build -t silver-bot .

# Run
docker run -d --name bot-kumpel --restart unless-stopped bot-kumpel

# Logs
docker logs -f bot-kumpel

# Docker Compose
docker-compose up -d
```

---

## 📊 Monitorowanie

```bash
# Logi bota
tail -f logs/bot.log

# Status serwisu
sudo systemctl status bot-kumpel.service

# Logi systemu
sudo journalctl -u bot-kumpel.service -f

# Zasoby
htop
free -h
```

---

## 🚨 Problemy?

**Bot nie startuje:**
```bash
tail -20 logs/bot.log
sudo systemctl status bot-kumpel.service
```

**Token błędny:**
- Sprawdź `bot_config.json`
- Test bot token: https://api.telegram.org/bot<TOKEN>/getMe

**Brak internetu:**
```bash
ping google.com
curl https://api.telegram.org
```

---

## ✅ Test

1. **Znajdź bota w Telegram**
2. **Wyślij `/start`**
3. **Sprawdź `/help`**
4. **Test: `/weather Warszawa`**

**🎯 Bot działa 24/7!** 🚀