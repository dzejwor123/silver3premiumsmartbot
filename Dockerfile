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

# Eksponuj port (dla Render)
EXPOSE 10000

# Ustaw zmienne środowiskowe
ENV PORT=10000
ENV PYTHONUNBUFFERED=1

# Uruchom serwer HTTP który uruchomi bota
CMD ["python", "server.py"] 