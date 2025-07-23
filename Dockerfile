FROM python:3.11-slim

WORKDIR /app

# Kopiuj wszystkie pliki
COPY . .

# Zainstaluj zależności
RUN pip install --no-cache-dir -r requirements.txt

# Utwórz katalog na logi
RUN mkdir -p logs

# Ustaw zmienne środowiskowe
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Uruchom bota
CMD ["python", "SmartAI Bot.py"] 