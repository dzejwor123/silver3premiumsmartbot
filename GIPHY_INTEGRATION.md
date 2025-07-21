# 🎬 Integracja GIPHY API - Bot Kumpel

## 📋 Opis

Bot Kumpel został rozszerzony o integrację z **GIPHY API**, co pozwala na dynamiczne pobieranie fajnych GIF-ów podczas rozmów. Bot może teraz:

- 🔍 Wyszukiwać GIF-y na żywo w bazie GIPHY
- 🎯 Automatycznie dodawać GIF-y do odpowiedzi AI
- 📱 Używać komendy `/giphy` do wyszukiwania dowolnych GIF-ów
- 🛡️ Mieć fallback do lokalnej bazy GIF-ów

## ⚙️ Konfiguracja

### 1. Klucz API GIPHY

W pliku `bot_config.json` dodano:

```json
{
    "_giphy_comment": "Klucz API do GIPHY - fajne GIF-y dla bota",
    "giphy_api_key": "HQmZeiYaS0GszE7aynIqUIsPNQEwNFQW",
    
    "giphy_config": {
        "base_url": "https://api.giphy.com/v1/gifs",
        "rating": "g",
        "lang": "pl",
        "limit": 10,
        "fallback_gifs": {
            "smiech": "https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif",
            "facepalm": "https://media.giphy.com/media/26u4cqi2I30juCOGY/giphy.gif",
            "taniec": "https://media.giphy.com/media/l2Je66jG6mAAZxgqI/giphy.gif",
            "zaskoczenie": "https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif",
            "frustracja": "https://media.giphy.com/media/26u4cqi2I30juCOGY/giphy.gif",
            "sukces": "https://media.giphy.com/media/l2Je66jG6mAAZxgqI/giphy.gif",
            "programowanie": "https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif",
            "bug": "https://media.giphy.com/media/26u4cqi2I30juCOGY/giphy.gif"
        }
    }
}
```

### 2. Włączenie funkcji

```json
{
    "features": {
        "giphy_integration": true
    }
}
```

### 3. Limity użytkowania

```json
{
    "limits": {
        "giphy_requests_per_user_per_hour": 50
    }
}
```

## 🚀 Funkcjonalności

### 1. Automatyczne GIF-y w odpowiedziach AI

Bot automatycznie dodaje GIF-y do odpowiedzi AI używając tagów:

- `[GIF_TAG: smiech]` - śmieszne sytuacje
- `[GIF_TAG: facepalm]` - frustracja
- `[GIF_TAG: taniec]` - sukces/radość
- `[GIF_TAG: zaskoczenie]` - zaskoczenie
- `[GIF_TAG: frustracja]` - frustracja
- `[GIF_TAG: sukces]` - sukces
- `[GIF_TAG: programowanie]` - tematy kodowania
- `[GIF_TAG: bug]` - błędy i problemy

### 2. Komenda `/gif`

Testuje lokalne GIF-y z tagami:
```
/gif smiech
/gif taniec
/gif programowanie
```

### 3. Komenda `/giphy`

Wyszukuje dowolne GIF-y w GIPHY:
```
/giphy kot
/giphy programowanie
/giphy śmieszne
/giphy taniec
/giphy pizza
```

## 🔧 Techniczne szczegóły

### Rate Limiting

- **50 zapytań GIPHY na godzinę** na użytkownika
- Automatyczny reset licznika co godzinę
- Fallback do lokalnej bazy przy przekroczeniu limitu

### Parametry GIPHY API

- **Rating**: `g` (family-friendly)
- **Language**: `pl` (polski)
- **Limit**: 10 wyników na zapytanie
- **Timeout**: 10 sekund

### Obsługa błędów

1. **Brak klucza API** → fallback do lokalnej bazy
2. **Błąd sieci** → fallback do lokalnej bazy
3. **Brak wyników** → fallback do lokalnej bazy
4. **Rate limit** → fallback do lokalnej bazy

## 📝 Przykłady użycia

### W rozmowie z AI

Użytkownik: "Ale się dziś śmieję!"

Bot może odpowiedzieć:
```
No i słusznie! Śmiech to zdrowie, stary! 😂

[GIF_TAG: smiech]
```

### Komenda GIPHY

```
/giphy programowanie
```

Bot znajdzie i wyśle GIF związany z programowaniem.

## 🛠️ Rozszerzanie

### Dodawanie nowych tagów

1. Dodaj tag do `fallback_gifs` w konfiguracji
2. Dodaj URL fallback GIF-a
3. Bot automatycznie obsłuży nowy tag

### Zmiana parametrów GIPHY

Edytuj sekcję `giphy_config` w `bot_config.json`:

```json
{
    "rating": "pg",  // pg, g, pg-13, r
    "lang": "en",    // en, pl, de, fr, etc.
    "limit": 20      // 1-50
}
```

## 🔒 Bezpieczeństwo

- **Rating G**: Wszystkie GIF-y są family-friendly
- **Rate limiting**: Ochrona przed nadużyciem API
- **Fallback**: Bot zawsze ma backup GIF-y
- **Logowanie**: Wszystkie zapytania są logowane

## 📊 Monitoring

Bot loguje:
- ✅ Pomyślne pobranie GIF-ów z GIPHY
- ⚠️ Brak wyników w GIPHY
- ❌ Błędy API GIPHY
- 🚫 Przekroczenie rate limit

## 🎯 Korzyści

1. **Dynamiczne GIF-y** - zawsze świeże i aktualne
2. **Lepsze doświadczenie** - bot jest bardziej ekspresyjny
3. **Fallback system** - niezawodność działania
4. **Rate limiting** - ochrona przed nadużyciem
5. **Łatwa konfiguracja** - wszystko w jednym pliku

---

**Uwaga**: Upewnij się, że masz ważny klucz API GIPHY. Darmowe konto pozwala na 1000 zapytań dziennie. 