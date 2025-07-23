FROM python:3.11-slim

WORKDIR /app

# Kopiuj pliki konfiguracyjne
COPY requirements.txt .
COPY bot_config.json .
COPY "SmartAI Bot.py" .
COPY start_bot.py .
COPY *.md .

# Zainstaluj zależności
RUN pip install --no-cache-dir -r requirements.txt

# Utwórz katalog na logi
RUN mkdir -p logs

# Ustaw zmienne środowiskowe
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Uruchom bota
CMD ["python", "SmartAI Bot.py"] 