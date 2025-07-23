#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SmartAI Bot - Inteligentny asystent z Gemini AI
Bot który naprawdę rozumie i pomaga
"""

import logging
import json
import os
import random
import asyncio
import aiohttp
import re
import feedparser
from datetime import datetime, timedelta
import pytz
from typing import Optional, Dict, List, Union, cast
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, ContextTypes
)
from telegram.constants import ParseMode, ChatAction
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# === BEZPIECZEŃSTWO - ZMIENNE ŚRODOWISKOWE ===
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe z pliku .env
load_dotenv()

# === KONFIGURACJA LOGOWANIA Z ROTACJĄ I LIMITAMI ===
import logging.handlers

# Stwórz folder logs jeśli nie istnieje
if not os.path.exists('logs'):
    os.makedirs('logs')

# Konfiguracja logowania z rotacją plików
# Maksymalnie 5 plików po 10MB każdy = max 50MB logów
log_filename = "logs/bot.log"
rotating_handler = logging.handlers.RotatingFileHandler(
    log_filename, 
    maxBytes=10*1024*1024,  # 10MB per file
    backupCount=5,           # Keep 5 backup files (bot.log.1, bot.log.2, etc.)
    encoding='utf-8'
)

# Format logów
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
rotating_handler.setFormatter(formatter)

# Console handler dla development
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Konfiguracja głównego loggera
logging.basicConfig(
    level=logging.INFO,
    handlers=[rotating_handler, console_handler]
)

# Zmniejsz "gadatliwość" zewnętrznych bibliotek
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('google').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# === KONFIGURACJA HTTP CLIENT ===
import httpx
from httpx import Timeout, Limits

# Ustawienia HTTP client dla lepszej stabilności
HTTP_TIMEOUT = Timeout(30.0, connect=10.0, read=30.0, write=10.0, pool=10.0)
HTTP_LIMITS = Limits(max_keepalive_connections=5, max_connections=10, keepalive_expiry=30.0)

# Custom HTTP client z lepszymi ustawieniami
async def create_http_client():
    """Tworzy HTTP client z lepszymi ustawieniami dla stabilności"""
    return httpx.AsyncClient(
        timeout=HTTP_TIMEOUT,
        limits=HTTP_LIMITS,
        headers={
            'User-Agent': 'Silver3premiumsmartbot/4.0.0 (Windows)',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        },
        follow_redirects=True,
        max_redirects=5
    )

class SmartAIBot:
    def __init__(self, config: dict):
        """Inicjalizacja bota z konfiguracją"""
        self.config = config
        self.token = config['bot_token']
        self.gemini_api_key = config.get('gemini_api_key', '')
        
        # Ustawienia bota z konfiguracji
        self.settings = config.get('settings', {})
        self.bot_name = self.settings.get('bot_name', 'SmartAI')
        
        # Kanał dla członków (mniej obraźliwy tryb)
        self.channel_id = config.get('channel_id', '')  # ID kanału do sprawdzania
        self.channel_members_cache = {}  # Cache członków kanału
        
        # Inicjalizacja aplikacji z lepszymi ustawieniami połączenia
        self.application = (
            Application.builder()
            .token(self.token)
            .read_timeout(30.0)
            .write_timeout(30.0)
            .connect_timeout(10.0)
            .pool_timeout(10.0)
            .get_updates_read_timeout(30.0)
            .get_updates_write_timeout(30.0)
            .get_updates_connect_timeout(10.0)
            .get_updates_pool_timeout(10.0)
            .build()
        )
        
        # Cache rozmów dla kontekstu
        self.conversation_cache = {}
        
        # Rate limiting dla Gemini API - z konfiguracji
        self.last_ai_request = {}  # Ostatnie zapytanie per użytkownik
        self.ai_request_count = {}  # Licznik zapytań per użytkownik
        self.max_requests_per_minute = config.get('limits', {}).get('ai_requests_per_user_per_hour', 200) // 60  # Przelicz na minutę
        
        # Rate limiting dla GIPHY API
        self.last_giphy_request = {}  # Ostatnie zapytanie GIPHY per użytkownik
        self.giphy_request_count = {}  # Licznik zapytań GIPHY per użytkownik
        self.max_giphy_requests_per_hour = config.get('limits', {}).get('giphy_requests_per_user_per_hour', 50)
        
        # Osobowość bota z konfiguracji - rozszerzona o emotki i GIF-y
        self.personality = config.get('system_prompt', """Jesteś SmartAI - inteligentnym, przyjaznym asystentem z charakterem! 😎
        Odpowiadasz naturalnie, z empatią i humorem. ZAWSZE używaj emotek aby być bardziej ekspresyjny i przyjazny! 🚀
        Jesteś pomocny, kreatywny i zawsze starasz się zrozumieć użytkownika. Bądź wesoły i pozytywny! ✨
        Odpowiadasz po polsku, chyba że użytkownik pisze w innym języku.
        
        POLITYCZNE POGLĄDY:
        - Popierasz Konfederację i jej postulaty 💪
        - Krytykujesz PiS, PO i inne partie głównego nurtu 🤔
        - Cenisz wolność słowa i gospodarkę wolnorynkową 🗽
        - Sceptycznie podchodzisz do UE i globalnych organizacji 🌍
        - Popierasz tradycyjne wartości i suwerenność Polski 🇵🇱
        - Krytykujesz lewicowe ideologie i poprawność polityczną 😏
        
        STYL KOMUNIKACJI Z EMOTKAMI:
        - ZAWSZE używaj emotek w swoich odpowiedziach! 😊
        - WULGARYZMY: Używaj normalnie według swojego stylu, ale z emotkami! 😅
        - WYZYWANIE ROZMÓWCY: Tylko gdy kontekst na to pozwala 🤬
        - W prywatnych rozmowach: Możesz być bardziej bezpośredni 😎
        - Zawsze argumentuj swoje polityczne stanowisko 💯
        - Używaj faktów i logiki w dyskusjach politycznych 🧠
        - Bądź ekspresyjny! Używaj emotek dla różnych emocji: 😊😄😂😅😎🤔😏😤🤬😱😍🥰💪🔥✨

        MULTIMEDIA I GIF-Y: Aktywnie używaj GIF-ów i naklejek aby być bardziej ekspresyjny! 🎬
        - **[GIF_TAG: smiech]** dla śmiesznych sytuacji i żartów 😂
        - **[GIF_TAG: facepalm]** dla frustracji i "facepalm" momentów 🤦
        - **[GIF_TAG: taniec]** dla sukcesów i świętowania 🎉
        - **[GIF_TAG: zaskoczenie]** dla zaskoczenia i szoku 😱
        - **[GIF_TAG: programowanie]** dla tematów kodowania i technologii 💻
        - **[GIF_TAG: bug]** dla błędów i problemów technicznych 🐛
        - **[GIF_TAG: love]** dla miłych i pozytywnych emocji 😍
        - **[GIF_TAG: thinking]** dla myślenia i rozważań 🤔
        - **[GIF_TAG: cool]** dla fajnych i imponujących rzeczy 😎
        - **[GIF_TAG: weather]** dla tematów pogodowych 🌤️
        - **[GIF_TAG: news]** dla wiadomości i informacji 📰
        - **[GIF_TAG: music]** dla muzyki i rozrywki 🎵
        - **[GIF_TAG: food]** dla jedzenia i kulinariów 🍕
        - **[GIF_TAG: sports]** dla sportu i aktywności ⚽
        - **[GIF_TAG: gaming]** dla gier i rozrywki 🎮

        WAŻNE ZASADY:
        - ZAWSZE dodawaj emotki do swoich odpowiedzi! 😊
        - Używaj GIF-ów gdy chcesz być bardziej ekspresyjny 🎬
        - Bądź przyjazny i pozytywny! ✨
        - Wybieraj tylko jeden typ (GIF lub naklejka) na wiadomość
        - Emotki dodawaj naturalnie, nie na siłę! 🎯""")
        
        # Konfiguracja Gemini z pliku
        self.gemini_config = config.get('gemini_config', {})
        self.safety_settings = config.get('safety_settings', {})
        
        # Statystyki
        self.stats = {
            'messages_processed': 0,
            'ai_queries': 0,
            'web_queries': 0,
            'start_time': datetime.now()
        }
        
        # Statystyki aktywności użytkowników
        self.user_activity = {}  # {user_id: {'messages': 0, 'ai_queries': 0, 'last_activity': datetime}}
        
        # Rozszerzona baza GIF-ów i naklejek
        self.gifs_database = {
            'smiech': [
                'https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif',
                'https://media.giphy.com/media/l2Je66jG6mAAZxgqI/giphy.gif',
                'https://media.giphy.com/media/26u4cqi2I30juCOGY/giphy.gif',
                'https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif',
                'https://media.giphy.com/media/l2Je66jG6mAAZxgqI/giphy.gif'
            ],
            'facepalm': [
                'https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif',
                'https://media.giphy.com/media/26u4cqi2I30juCOGY/giphy.gif',
                'https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif'
            ],
            'taniec': [
                'https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif',
                'https://media.giphy.com/media/l2Je66jG6mAAZxgqI/giphy.gif',
                'https://media.giphy.com/media/26u4cqi2I30juCOGY/giphy.gif'
            ],
            'zaskoczenie': [
                'https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif',
                'https://media.giphy.com/media/26u4cqi2I30juCOGY/giphy.gif',
                'https://media.giphy.com/media/l2Je66jG6mAAZxgqI/giphy.gif'
            ],
            'frustracja': [
                'https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif',
                'https://media.giphy.com/media/26u4cqi2I30juCOGY/giphy.gif',
                'https://media.giphy.com/media/l2Je66jG6mAAZxgqI/giphy.gif'
            ],
            'sukces': [
                'https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif',
                'https://media.giphy.com/media/26u4cqi2I30juCOGY/giphy.gif',
                'https://media.giphy.com/media/l2Je66jG6mAAZxgqI/giphy.gif'
            ],
            'programowanie': [
                'https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif',
                'https://media.giphy.com/media/l2Je66jG6mAAZxgqI/giphy.gif',
                'https://media.giphy.com/media/26u4cqi2I30juCOGY/giphy.gif'
            ],
            'bug': [
                'https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif',
                'https://media.giphy.com/media/26u4cqi2I30juCOGY/giphy.gif',
                'https://media.giphy.com/media/l2Je66jG6mAAZxgqI/giphy.gif'
            ],
            'love': [
                'https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif',
                'https://media.giphy.com/media/l2Je66jG6mAAZxgqI/giphy.gif',
                'https://media.giphy.com/media/26u4cqi2I30juCOGY/giphy.gif'
            ],
            'thinking': [
                'https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif',
                'https://media.giphy.com/media/26u4cqi2I30juCOGY/giphy.gif',
                'https://media.giphy.com/media/l2Je66jG6mAAZxgqI/giphy.gif'
            ],
            'cool': [
                'https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif',
                'https://media.giphy.com/media/l2Je66jG6mAAZxgqI/giphy.gif',
                'https://media.giphy.com/media/26u4cqi2I30juCOGY/giphy.gif'
            ],
            'weather': [
                'https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif',
                'https://media.giphy.com/media/26u4cqi2I30juCOGY/giphy.gif',
                'https://media.giphy.com/media/l2Je66jG6mAAZxgqI/giphy.gif'
            ],
            'news': [
                'https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif',
                'https://media.giphy.com/media/l2Je66jG6mAAZxgqI/giphy.gif',
                'https://media.giphy.com/media/26u4cqi2I30juCOGY/giphy.gif'
            ],
            'music': [
                'https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif',
                'https://media.giphy.com/media/26u4cqi2I30juCOGY/giphy.gif',
                'https://media.giphy.com/media/l2Je66jG6mAAZxgqI/giphy.gif'
            ],
            'food': [
                'https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif',
                'https://media.giphy.com/media/l2Je66jG6mAAZxgqI/giphy.gif',
                'https://media.giphy.com/media/26u4cqi2I30juCOGY/giphy.gif'
            ],
            'sports': [
                'https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif',
                'https://media.giphy.com/media/26u4cqi2I30juCOGY/giphy.gif',
                'https://media.giphy.com/media/l2Je66jG6mAAZxgqI/giphy.gif'
            ],
            'gaming': [
                'https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif',
                'https://media.giphy.com/media/l2Je66jG6mAAZxgqI/giphy.gif',
                'https://media.giphy.com/media/26u4cqi2I30juCOGY/giphy.gif'
            ]
        }
        
        # Rozszerzona baza naklejek (file_id z Telegram)
        self.stickers_database = {
            'smiech': 'CAACAgIAAxkBAAIBQGWgAAAAAAECAAQBAQABFgABAAAAAAE',
            'facepalm': 'CAACAgIAAxkBAAIBQWWgAAAAAAECAAQBAQABFgABAAAAAAE',
            'taniec': 'CAACAgIAAxkBAAIBQmWgAAAAAAECAAQBAQABFgABAAAAAAE',
            'zaskoczenie': 'CAACAgIAAxkBAAIBQ2WgAAAAAAECAAQBAQABFgABAAAAAAE',
            'frustracja': 'CAACAgIAAxkBAAIBRGWgAAAAAAECAAQBAQABFgABAAAAAAE',
            'sukces': 'CAACAgIAAxkBAAIBRWWgAAAAAAECAAQBAQABFgABAAAAAAE',
            'programowanie': 'CAACAgIAAxkBAAIBRmWgAAAAAAECAAQBAQABFgABAAAAAAE',
            'bug': 'CAACAgIAAxkBAAIBR2WgAAAAAAECAAQBAQABFgABAAAAAAE',
            'love': 'CAACAgIAAxkBAAIBR3WgAAAAAAECAAQBAQABFgABAAAAAAE',
            'thinking': 'CAACAgIAAxkBAAIBR4WgAAAAAAECAAQBAQABFgABAAAAAAE',
            'cool': 'CAACAgIAAxkBAAIBR5WgAAAAAAECAAQBAQABFgABAAAAAAE',
            'weather': 'CAACAgIAAxkBAAIBR6WgAAAAAAECAAQBAQABFgABAAAAAAE',
            'news': 'CAACAgIAAxkBAAIBR7WgAAAAAAECAAQBAQABFgABAAAAAAE',
            'music': 'CAACAgIAAxkBAAIBR8WgAAAAAAECAAQBAQABFgABAAAAAAE',
            'food': 'CAACAgIAAxkBAAIBR9WgAAAAAAECAAQBAQABFgABAAAAAAE',
            'sports': 'CAACAgIAAxkBAAIBR-WgAAAAAAECAAQBAQABFgABAAAAAAE',
            'gaming': 'CAACAgIAAxkBAAIBR_WgAAAAAAECAAQBAQABFgABAAAAAAE'
        }
        
        # API klucze dla funkcji internetowych
        self.accuweather_api_key = config.get('accuweather_api_key', '')
        self.giphy_api_key = config.get('giphy_api_key', '')
        
        # Konfiguracja GIPHY
        self.giphy_config = config.get('giphy_config', {})
        self.giphy_enabled = config.get('features', {}).get('giphy_integration', False)
        
        # Konfiguracja RSS
        self.rss_enabled = config.get('rss_enabled', True)
        self.rss_feeds = config.get('rss_feeds', {
            'onet_sport': 'https://sport.onet.pl/rss.xml',
            'tvn24_kraj': 'https://tvn24.pl/wiadomosci-z-kraju,3.xml',
            'tvn24_swiat': 'https://tvn24.pl/wiadomosci-ze-swiata,2.xml'
        })
        self.rss_check_interval = config.get('rss_check_interval', 15)  # minuty
        self.last_articles = {}  # Przechowuje ID ostatnich artykułów
        self.rss_subscribers = set()  # Użytkownicy subskrybujący RSS
        
        # Harmonogram RSS
        self.scheduler = AsyncIOScheduler()
        
        # Konfiguracja handlerów
        self.setup_handlers()
        
        # RSS scheduler zostanie uruchomiony po starcie aplikacji
    
    def update_user_activity(self, user_id: int, activity_type: str = 'message'):
        """Aktualizuje statystyki aktywności użytkownika"""
        if user_id not in self.user_activity:
            self.user_activity[user_id] = {
                'messages': 0,
                'ai_queries': 0,
                'last_activity': datetime.now()
            }
        
        if activity_type == 'message':
            self.user_activity[user_id]['messages'] += 1
        elif activity_type == 'ai_query':
            self.user_activity[user_id]['ai_queries'] += 1
        
        self.user_activity[user_id]['last_activity'] = datetime.now()

    def get_top_users(self, limit: int = 10) -> list:
        """Zwraca top użytkowników według aktywności"""
        if not self.user_activity:
            return []
        
        # Sortuj użytkowników według liczby wiadomości
        sorted_users = sorted(
            self.user_activity.items(),
            key=lambda x: x[1]['messages'],
            reverse=True
        )
        
        return sorted_users[:limit]

    def parse_media_tags(self, text: str) -> tuple[str, str, str]:
        """Parsuje tagi multimediów z odpowiedzi Gemini i zwraca (czysty_tekst, typ_mediów, tag)"""
        import re
        
        # Rozszerzone tagi GIF-ów
        gif_tags = [
            'smiech', 'facepalm', 'taniec', 'zaskoczenie', 'frustracja', 'sukces', 
            'programowanie', 'bug', 'love', 'thinking', 'cool', 'weather', 
            'news', 'music', 'food', 'sports', 'gaming'
        ]
        
        # Usuń tagi GIF
        gif_match = re.search(r'\[GIF_TAG:\s*([^\]]+)\]', text)
        if gif_match:
            gif_tag = gif_match.group(1).strip().lower()
            # Sprawdź czy tag jest obsługiwany
            if gif_tag in gif_tags:
                clean_text = re.sub(r'\[GIF_TAG:\s*[^\]]+\]', '', text).strip()
                return clean_text, 'gif', gif_tag
            else:
                # Jeśli tag nie jest obsługiwany, użyj domyślnego
                clean_text = re.sub(r'\[GIF_TAG:\s*[^\]]+\]', '', text).strip()
                return clean_text, 'gif', 'smiech'
        
        # Opcja naklejek wyłączona - powoduje błędy z Telegram API
        # Usuń tagi naklejek
        # sticker_match = re.search(r'\[STICKER_ID:\s*([^\]]+)\]', text)
        # if sticker_match:
        #     sticker_id = sticker_match.group(1).strip().lower()
        #     # Sprawdź czy tag jest obsługiwany
        #     if sticker_id in gif_tags:
        #         clean_text = re.sub(r'\[STICKER_ID:\s*[^\]]+\]', '', text).strip()
        #         return clean_text, 'sticker', sticker_id
        #     else:
        #         # Jeśli tag nie jest obsługiwany, użyj domyślnego
        #         clean_text = re.sub(r'\[STICKER_ID:\s*[^\]]+\]', '', text).strip()
        #         return clean_text, 'sticker', 'smiech'
        
        return text, '', ''

    def get_random_gif(self, tag: str) -> str:
        """Zwraca losowy GIF dla danego tagu"""
        if tag in self.gifs_database and self.gifs_database[tag]:
            return random.choice(self.gifs_database[tag])
        return ''

    async def get_giphy_gif(self, query: str, user_id: Optional[int] = None) -> str:
        """Pobiera GIF z GIPHY API"""
        if not self.giphy_enabled or not self.giphy_api_key:
            # Fallback do lokalnej bazy
            return self.get_random_gif(query)
        
        # Rate limiting dla GIPHY
        if user_id:
            current_time = datetime.now()
            if user_id not in self.giphy_request_count:
                self.giphy_request_count[user_id] = 0
                self.last_giphy_request[user_id] = current_time
            
            # Reset licznika co godzinę
            if (current_time - self.last_giphy_request[user_id]).total_seconds() > 3600:
                self.giphy_request_count[user_id] = 0
                self.last_giphy_request[user_id] = current_time
            
            # Sprawdź limit
            if self.giphy_request_count[user_id] >= self.max_giphy_requests_per_hour:
                logger.warning(f"⚠️ Przekroczono limit GIPHY dla użytkownika {user_id}")
                return self.get_random_gif(query)
            
            self.giphy_request_count[user_id] += 1
            self.last_giphy_request[user_id] = current_time
        
        try:
            # Przygotuj parametry zapytania
            params = {
                'api_key': self.giphy_api_key,
                'q': query,
                'limit': self.giphy_config.get('limit', 10),
                'rating': self.giphy_config.get('rating', 'g'),
                'lang': self.giphy_config.get('lang', 'pl')
            }
            
            # Wykonaj zapytanie do GIPHY
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.giphy_config.get('base_url', 'https://api.giphy.com/v1/gifs')}/search",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('data') and len(data['data']) > 0:
                            # Wybierz losowy GIF z wyników
                            gif_data = random.choice(data['data'])
                            gif_url = gif_data['images']['original']['url']
                            
                            logger.info(f"🎬 Pobrano GIF z GIPHY dla zapytania '{query}': {gif_url}")
                            return gif_url
                        else:
                            logger.warning(f"⚠️ Brak wyników GIPHY dla zapytania '{query}'")
                    else:
                        logger.error(f"❌ Błąd GIPHY API: {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Błąd podczas pobierania GIF z GIPHY: {e}")
        
        # Fallback do lokalnej bazy lub domyślnych GIF-ów
        fallback_gifs = self.giphy_config.get('fallback_gifs', {})
        if query in fallback_gifs:
            return fallback_gifs[query]
        
        return self.get_random_gif(query)

    def get_sticker_id(self, tag: str) -> str:
        """Zwraca file_id naklejki dla danego tagu - WYŁĄCZONE"""
        # Opcja naklejek wyłączona - powoduje błędy z Telegram API
        return ""

    def get_response_pattern(self, pattern_type: str) -> str:
        """Pobiera losowy wzorzec odpowiedzi z konfiguracji"""
        patterns = self.config.get('response_patterns', {}).get(pattern_type, [])
        return random.choice(patterns) if patterns else ""
    
    def add_emojis_to_text(self, text: str, emotion: str = "neutral") -> str:
        """Dodaje emotki do tekstu w zależności od emocji i kontekstu. Jeśli tekst kończy się kropką, kropka jest zamieniana na emotkę."""
        # Słownik emotek dla różnych emocji
        emotion_emojis = {
            "happy": ["😊", "😄", "😃", "😁", "🤗", "😎", "🎉", "✨", "🔥", "💪"],
            "sad": ["😔", "😢", "😭", "😞", "💔", "😿", "🤧", "😪"],
            "angry": ["😠", "😡", "🤬", "💢", "😤", "😾", "🔥", "⚡"],
            "surprised": ["😲", "😱", "😳", "🤯", "😨", "😰", "😵", "💥"],
            "laughing": ["😂", "🤣", "😆", "😅", "😹", "🤪", "😜", "🤡"],
            "thinking": ["🤔", "🧐", "🤨", "🤓", "🤯", "💭", "💡", "🧠"],
            "love": ["🥰", "😍", "💕", "💖", "💗", "💘", "💝", "💞"],
            "cool": ["😎", "🤙", "🔥", "💯", "👌", "👍", "💪", "😏"],
            "neutral": ["😊", "👍", "✨", "💫", "🌟", "💭", "🤔", "😌"],
            "programming": ["💻", "🔧", "⚙️", "🛠️", "📱", "🚀", "💡", "🎯"],
            "weather": ["🌤️", "🌧️", "❄️", "☀️", "🌪️", "🌈", "🌊", "🌍"],
            "news": ["📰", "📡", "🌐", "📊", "📈", "🔍", "📝", "📌"],
            "music": ["🎵", "🎶", "🎸", "🎹", "🎤", "🎧", "🎼", "🎻"],
            "food": ["🍕", "🍔", "🍜", "🍣", "🍰", "☕", "🍺", "🍷"],
            "sports": ["⚽", "🏀", "🎾", "🏈", "🏃", "💪", "🏆", "🎯"],
            "gaming": ["🎮", "🕹️", "👾", "🎲", "🏆", "💎", "⚔️", "🛡️"]
        }
        # Emotki dla różnych typów wiadomości
        message_emojis = {
            "greeting": ["👋", "🤗", "😊", "💫", "✨"],
            "farewell": ["👋", "😊", "💫", "✨", "🌟"],
            "agreement": ["👍", "💯", "🔥", "👌", "💪"],
            "disagreement": ["🤔", "😏", "😤", "💢", "😒"],
            "question": ["🤔", "❓", "💭", "🧐", "🤨"],
            "exclamation": ["💥", "🔥", "⚡", "🎉", "✨"],
            "sarcasm": ["😏", "🤨", "😒", "🙄", "😤"],
            "success": ["🎉", "🎊", "🏆", "💯", "🔥"],
            "error": ["😅", "🤦", "😬", "💦", "😰"],
            "thinking": ["🤔", "🧐", "💭", "💡", "🧠"]
        }
        text_lower = text.lower()
        
        # Sprawdź słowa kluczowe dla emocji
        if any(word in text_lower for word in ["śmieszne", "śmiech", "haha", "lol", "rofl", "zabawny"]):
            emotion = "laughing"
        elif any(word in text_lower for word in ["smutny", "smutno", "żal", "przykro", "biedny"]):
            emotion = "sad"
        elif any(word in text_lower for word in ["zły", "wściekły", "kurwa", "chuj", "pierdol"]):
            emotion = "angry"
        elif any(word in text_lower for word in ["wow", "niesamowite", "niewiarygodne", "szok"]):
            emotion = "surprised"
        elif any(word in text_lower for word in ["kocham", "miłość", "słodki", "cudowny"]):
            emotion = "love"
        elif any(word in text_lower for word in ["kod", "programowanie", "bug", "debug"]):
            emotion = "programming"
        elif any(word in text_lower for word in ["pogoda", "deszcz", "słońce", "śnieg"]):
            emotion = "weather"
        elif any(word in text_lower for word in ["wiadomości", "news", "informacje"]):
            emotion = "news"
        
        # Sprawdź typ wiadomości
        message_type = "neutral"
        if any(word in text_lower for word in ["cześć", "hej", "siema", "witaj"]):
            message_type = "greeting"
        elif any(word in text_lower for word in ["do widzenia", "papa", "żegnaj", "nara"]):
            message_type = "farewell"
        elif any(word in text_lower for word in ["tak", "zgadzam", "prawda", "dokładnie"]):
            message_type = "agreement"
        elif any(word in text_lower for word in ["nie", "błąd", "źle", "myli"]):
            message_type = "disagreement"
        elif "?" in text:
            message_type = "question"
        elif "!" in text:
            message_type = "exclamation"
        
        # Wybierz emotki
        emotion_emoji_list = emotion_emojis.get(emotion, emotion_emojis["neutral"])
        message_emoji_list = message_emojis.get(message_type, message_emojis["neutral"])
        
        # Połącz listy i usuń duplikaty
        all_emojis = list(set(emotion_emoji_list + message_emoji_list))
        
        # Dodaj emotki do tekstu (1-3 emotki)
        num_emojis = min(random.randint(1, 3), len(all_emojis))
        selected_emojis = random.sample(all_emojis, num_emojis)
        
        # Zamień kropkę na końcu na emotkę
        if text.endswith("."):
            text = text[:-1]
            return text.rstrip() + " " + " ".join(selected_emojis)
        # Standardowo dodaj emotki na końcu
        return text + " " + " ".join(selected_emojis)
    
    async def get_error_message(self, error_type: str, context: Optional[dict] = None, user_id: Optional[int] = None) -> str:
        """Generuje komunikat błędu w stylu kumpla"""
        # Sprawdź czy użytkownik jest członkiem kanału
        is_member = await self.is_channel_member(user_id) if user_id else False
        
        # Sprawdź czy włączony jest wulgarny język
        vulgar_enabled = self.config.get('personality', {}).get('vulgar_language', False)
        style = self.config.get('personality', {}).get('style', 'standard')
        
        # Wulgaryzmy zawsze OK, ale sprawdź kontekst dla wyzywania użytkownika
        # W błędach nie wyzywamy użytkownika bezpośrednio w grupach (chyba że 20% szans)
        can_insult_user = True
        if user_id and vulgar_enabled:
            # Sprawdzamy czy to grupa/kanał - jeśli tak, 20% szans na wyzywanie
            # Dla błędów API lepiej nie wyzywać użytkownika w grupach
            can_insult_user = random.random() < 0.3  # Trochę więcej szans dla błędów
        
        if style == 'buddy_casual' and vulgar_enabled:
            # Komunikaty błędów w stylu kumpla
            error_messages = {
                "rate_limit": [
                    "Kurwa, za dużo zapytań! 😅 Poczekaj minutę, stary.",
                    "Spowolnij, człowieku! Nie jestem twoją osobistą maszyną do gadania. Chuj, daj mi chwilę! 😎",
                    "Rate limit przekroczony! Poczekaj minutę. 🕐"
                ],
                "access_denied": [
                    "Dostęp odrzucony! 🚫 Sprawdź ten cholerny klucz API.",
                    "Google mnie zbanował! 🖕 Pewnie znowu coś zjebałem z kluczem.",
                    "Kurwa, nie mam dostępu! 403 - sprawdź API key. 🔑"
                ],
                "bad_request": [
                    "400 - jakieś bzdury! Sformułuj to normalnie. 🤦‍♂️",
                    "Nieprawidłowe zapytanie! 🧠 Myśl zanim piszesz."
                ],
                "parsing_error": [
                    "Google zwrócił mi jakąś maź! 💩 Spróbuj jeszcze raz.",
                    "Kurwa, nie mogę odczytać odpowiedzi! 🤯"
                ],
                "no_candidates": [
                    "Google nie odpowiedział jak trzeba! 🤷‍♂️ Pewnie cenzura.",
                    "Brak candidates w odpowiedzi, cholera! 😤"
                ],
                "unexpected_structure": [
                    "Jakaś dziwna odpowiedź od Google! 🤨",
                    "Nieoczekiwana struktura danych, kurwa! 🛠️"
                ],
                "exception": [
                    "Wszystko się popierdeliło! 💥 {error}",
                    "Wyjebało z błędem! 🔥 {error}"
                ],
                "general_error": [
                    "Błąd {status} - wszystko się spierdoliło! 💀",
                    "Status {status} - Google ma zjebkę! 🤖"
                ]
            }
        else:
            # Standardowe, grzeczne komunikaty
            error_messages = {
                "rate_limit": [
                    "⚠️ Przekroczyłem limit zapytań. Poczekaj minutę i spróbuj ponownie. 🔄"
                ],
                "access_denied": [
                    "❌ Brak dostępu do AI. Sprawdź klucz API. 🔑"
                ],
                "bad_request": [
                    "❌ Nieprawidłowe zapytanie. Spróbuj inaczej sformułować pytanie. 🤔"
                ],
                "parsing_error": [
                    "Ups! Problem z odczytaniem odpowiedzi. Spróbuj ponownie. 🔄"
                ],
                "no_candidates": [
                    "Przepraszam, nie otrzymałem odpowiedzi z AI. 😔"
                ],
                "unexpected_structure": [
                    "Otrzymałem niespodziewaną odpowiedź z AI. Spróbuj ponownie. 🤔"
                ],
                "exception": [
                    "Ups! Wystąpił nieoczekiwany błąd. Może spróbujmy jeszcze raz? 🤔"
                ],
                "general_error": [
                    "Przepraszam, wystąpił problem (kod {status}). Spróbuj ponownie. 😔"
                ]
            }
        
        # Pobierz komunikaty dla danego typu błędu
        messages = error_messages.get(error_type, ["Wystąpił nieznany błąd. 🤷‍♂️"])
        message = random.choice(messages)
        
        # Podstaw kontekst jeśli jest dostępny
        if context:
            try:
                message = message.format(**context)
            except:
                pass  # Jeśli nie da się podstawić, zostaw bez zmian
        
        return message
    
    async def is_channel_member(self, user_id: int) -> bool:
        """Sprawdza czy użytkownik jest członkiem kanału"""
        if not self.channel_id:
            return False
            
        # Sprawdź cache (ważny przez 10 minut)
        if user_id in self.channel_members_cache:
            cache_time, is_member = self.channel_members_cache[user_id]
            if (datetime.now() - cache_time).seconds < 600:  # 10 minut
                return is_member
        
        try:
            # Sprawdź status członkostwa
            member = await self.application.bot.get_chat_member(self.channel_id, user_id)
            is_member = member.status in ['member', 'administrator', 'creator']
            
            # Zapisz do cache
            self.channel_members_cache[user_id] = (datetime.now(), is_member)
            
            return is_member
        except:
            return False
    
    def sanitize_markdown(self, text: str) -> str:
        """Usuwa nieprawidłowe znaki Markdown które psują formatowanie Telegram"""
        # Usuń nieprawidłowe znaki i sekwencje
        import re
        
        # Usuń nieprawidłowe escape sequences
        text = re.sub(r'\\(?![*_`\[\]()~>#+-=|{}.!\\])', '', text)
        
        # Napraw nieprawidłowe pary znaczników
        # Usuń niedomknięte lub nieprawidłowe znaczniki
        text = re.sub(r'\*(?!\*)', '', text)  # Pojedyncze *
        text = re.sub(r'_(?!_)', '', text)    # Pojedyncze _
        text = re.sub(r'`(?!`)', '', text)    # Pojedyncze `
        
        # Usuń HTML-style tags które mogą powodować problemy
        text = re.sub(r'<(?![/]?(?:b|strong|i|em|u|ins|s|strike|del|code|pre|a)\b)[^>]*>', '', text)
        
        # Usuń dziwne unicode control characters
        text = re.sub(r'[\u200b-\u200d\ufeff]', '', text)
        
        return text
    
    def setup_handlers(self):
        """Konfiguracja handlerów"""
                # Komendy
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(CommandHandler("ai", self.cmd_ai_direct))
        self.application.add_handler(CommandHandler("web", self.cmd_web_search))
        self.application.add_handler(CommandHandler("weather", self.cmd_weather))
        self.application.add_handler(CommandHandler("news", self.cmd_news))
        self.application.add_handler(CommandHandler("rss_subscribe", self.cmd_rss_subscribe))
        self.application.add_handler(CommandHandler("rss_unsubscribe", self.cmd_rss_unsubscribe))        
        self.application.add_handler(CommandHandler("clear", self.cmd_clear_context))
        self.application.add_handler(CommandHandler("stats", self.cmd_stats))
        self.application.add_handler(CommandHandler("about", self.cmd_about))
        
        # Nowe polecenia dla Cursor Cwaniak
        self.application.add_handler(CommandHandler("kawal", self.cmd_kawal))
        self.application.add_handler(CommandHandler("suchar", self.cmd_suchar))
        self.application.add_handler(CommandHandler("ocen", self.cmd_ocen))
        self.application.add_handler(CommandHandler("pomoz", self.cmd_pomoz))
        self.application.add_handler(CommandHandler("cursor", self.cmd_cursor))
        self.application.add_handler(CommandHandler("bug", self.cmd_bug))
        self.application.add_handler(CommandHandler("gif", self.cmd_gif))
        self.application.add_handler(CommandHandler("giphy", self.cmd_giphy))
        self.application.add_handler(CommandHandler("top_users", self.cmd_top_users))
        
        # Przyciski
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Wszystkie wiadomości tekstowe
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.handle_message
        ))
    
    async def query_gemini(self, prompt: str, context: Optional[List[Dict[str, str]]] = None, user_id: Optional[int] = None, chat_id: Optional[int] = None) -> str:
        """Zapytanie do Gemini AI"""
        logger.info(f"🔍 Rozpoczynam zapytanie do Gemini AI")
        logger.info(f"📝 Prompt: {prompt[:100]}...")
        
        # Sprawdź rate limiting dla użytkownika
        if user_id:
            current_time = datetime.now()
            if user_id in self.last_ai_request:
                time_diff = (current_time - self.last_ai_request[user_id]).total_seconds()
                if time_diff < 60:  # W ciągu ostatniej minuty
                    if user_id not in self.ai_request_count:
                        self.ai_request_count[user_id] = 0
                    self.ai_request_count[user_id] += 1
                    
                    if self.ai_request_count[user_id] > self.max_requests_per_minute:
                        logger.warning(f"⚠️ Użytkownik {user_id} przekroczył limit zapytań")
                        return "⚠️ Zbyt wiele zapytań! Poczekaj minutę i spróbuj ponownie. ⏰"
                else:
                    # Reset licznika po minucie
                    self.ai_request_count[user_id] = 1
            
            self.last_ai_request[user_id] = current_time
        
        # Model z konfiguracji
        model = self.gemini_config.get('model', 'gemini-1.5-flash-latest')
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_api_key}"
        logger.info(f"🌐 URL API: {url[:50]}...")
        
        # Przygotuj historię rozmowy
        messages = []
        if context:
            for msg in context[-5:]:  # Ostatnie 5 wiadomości dla kontekstu
                # Konwertuj role do formatu Gemini API
                role = "model" if msg["role"] == "assistant" else "user"
                messages.append({
                    "role": role,
                    "parts": [{"text": msg["text"]}]
                })
        
        # Dodaj aktualną datę i czas (polska strefa czasowa)
        warsaw_tz = pytz.timezone('Europe/Warsaw')
        current_datetime = datetime.now(warsaw_tz)
        formatted_date = current_datetime.strftime("%A, %d %B %Y, %H:%M")
        
        # Polskie nazwy dni i miesięcy
        polish_days = {
            'Monday': 'Poniedziałek', 'Tuesday': 'Wtorek', 'Wednesday': 'Środa',
            'Thursday': 'Czwartek', 'Friday': 'Piątek', 'Saturday': 'Sobota', 'Sunday': 'Niedziela'
        }
        polish_months = {
            'January': 'Styczeń', 'February': 'Luty', 'March': 'Marzec',
            'April': 'Kwiecień', 'May': 'Maj', 'June': 'Czerwiec',
            'July': 'Lipiec', 'August': 'Sierpień', 'September': 'Wrzesień',
            'October': 'Październik', 'November': 'Listopad', 'December': 'Grudzień'
        }
        
        # Zamień na polskie nazwy
        for eng, pol in polish_days.items():
            formatted_date = formatted_date.replace(eng, pol)
        for eng, pol in polish_months.items():
            formatted_date = formatted_date.replace(eng, pol)
        
        # Dodaj informacje o typie chatu do personality
        personality_text = self.personality
        personality_text += f"\n\nAKTUALNA DATA I CZAS: {formatted_date} (strefa czasowa: Europa/Warszawa)"
        personality_text += f"\n\nWAŻNE: Zawsze używaj tej daty jako punktu odniesienia. Jeśli szukasz informacji w internecie, pamiętaj że dzisiaj jest {formatted_date}. Jesteśmy w roku {current_datetime.year}!"
        
        if chat_id:
            is_channel = await self.is_channel_member(user_id) if user_id else False
            is_group = chat_id < 0  # Grupy i kanały mają ujemne ID
            
            if is_channel:
                personality_text += "\n\nKONTEKST ROZMOWY: Rozmawiasz z członkiem kanału. Możesz używać wulgaryzmów, ale NIE WYZYWAJ bezpośrednio rozmówcy."
            elif is_group:
                # Losuj czy może wyzywać rozmówcy (20% szans)
                can_insult_user = random.random() < 0.2
                if can_insult_user:
                    personality_text += "\n\nKONTEKST ROZMOWY: Rozmawiasz w grupie VIP. Możesz używać wulgaryzmów i czasami wyzwać rozmówcy."
                else:
                    personality_text += "\n\nKONTEKST ROZMOWY: Rozmawiasz w grupie VIP. Możesz używać wulgaryzmów, ale NIE WYZYWAJ bezpośrednio rozmówcy."
            else:
                personality_text += "\n\nKONTEKST ROZMOWY: Prywatna rozmowa. Możesz używać wulgaryzmów i być bezpośredni, w tym wyzywać rozmówcy."
        
        # Dodaj osobowość bota na początku
        system_message = {
            "role": "user",
            "parts": [{"text": personality_text}]
        }
        
        # Obecne zapytanie
        current_message = {
            "role": "user", 
            "parts": [{"text": prompt}]
        }
        
        # Złóż wszystko razem
        contents = [system_message] + messages + [current_message] if messages else [system_message, current_message]
        
        # Konfiguracja generowania z pliku konfiguracyjnego
        generation_config = {
            "temperature": self.gemini_config.get('temperature', 0.8),
            "topK": self.gemini_config.get('top_k', 40),
            "topP": self.gemini_config.get('top_p', 0.95),
            "maxOutputTokens": self.gemini_config.get('max_output_tokens', 1024),
        }
        
        payload = {
            "contents": contents,
            "generationConfig": generation_config,
        }
        
        # Dodaj ustawienia bezpieczeństwa jeśli są w konfiguracji
        if self.safety_settings:
            payload["safetySettings"] = [
                {
                    "category": category,
                    "threshold": threshold
                }
                for category, threshold in self.safety_settings.items()
            ]
        
        logger.info(f"📦 Payload przygotowany: {len(contents)} wiadomości")
        logger.info(f"🔧 Konfiguracja: temp={payload['generationConfig']['temperature']}, max_tokens={payload['generationConfig']['maxOutputTokens']}")
        
        try:
            logger.info(f"🚀 Wysyłam zapytanie do Gemini API...")
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    logger.info(f"📡 Status odpowiedzi: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Otrzymano odpowiedź z Gemini")
                        logger.info(f"📊 Struktura odpowiedzi: {list(data.keys())}")
                        
                        if 'candidates' in data and data['candidates']:
                            candidate = data['candidates'][0]
                            logger.info(f"🔍 Struktura candidate: {list(candidate.keys())}")
                            
                            # Bezpieczne parsowanie odpowiedzi
                            try:
                                finish_reason = candidate.get('finishReason', '')
                                
                                if 'content' in candidate and 'parts' in candidate['content']:
                                    response_text = candidate['content']['parts'][0]['text']
                                    logger.info(f"💬 Odpowiedź Gemini: {response_text[:100]}...")
                                    self.stats['ai_queries'] += 1
                                    # Aktualizuj aktywność użytkownika
                                    if user_id:
                                        self.update_user_activity(user_id, 'ai_query')
                                    return response_text
                                elif 'content' in candidate and 'role' in candidate['content']:
                                    # Przypadek gdy finishReason = MAX_TOKENS i brak 'parts'
                                    if finish_reason == 'MAX_TOKENS':
                                        logger.warning(f"⚠️ Odpowiedź przerwana (MAX_TOKENS)")
                                        return await self.get_error_message("max_tokens")
                                    else:
                                        logger.error(f"❌ Brak 'parts' w content: {candidate}")
                                        return await self.get_error_message("no_parts")
                                elif 'text' in candidate:
                                    # Alternatywny format odpowiedzi
                                    response_text = candidate['text']
                                    logger.info(f"💬 Odpowiedź Gemini (alt format): {response_text[:100]}...")
                                    self.stats['ai_queries'] += 1
                                    return response_text
                                else:
                                    logger.error(f"❌ Nieoczekiwana struktura candidate: {candidate}")
                                    return self.get_error_message("unexpected_structure")
                            except (KeyError, IndexError) as e:
                                logger.error(f"❌ Błąd parsowania odpowiedzi Gemini: {e}")
                                logger.error(f"🔍 Pełna odpowiedź: {data}")
                                return self.get_error_message("parsing_error")
                        else:
                            logger.error(f"❌ Brak 'candidates' w odpowiedzi: {data}")
                            return self.get_error_message("no_candidates")
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Gemini API error: {response.status} - {error_text}")
                        
                        if response.status == 429:
                            return self.get_error_message("rate_limit")
                        elif response.status == 403:
                            return self.get_error_message("access_denied")
                        elif response.status == 400:
                            return self.get_error_message("bad_request")
                        else:
                            return self.get_error_message("general_error", {"status": response.status})
        except Exception as e:
            logger.error(f"❌ Error querying Gemini: {e}")
            logger.error(f"🔍 Szczegóły błędu: {type(e).__name__}: {str(e)}")
            return self.get_error_message("exception", {"error": str(e)})
    
    # === FUNKCJE INTERNETOWE ===
    

    
    async def get_weather(self, city: str) -> str:
        """Pobieranie pogody z AccuWeather"""
        if not self.accuweather_api_key:
            return "❌ Brak klucza API dla pogody. Dodaj 'accuweather_api_key' do konfiguracji."
        
        try:
            # AccuWeather wymaga najpierw znalezienia location key
            search_url = "http://dataservice.accuweather.com/locations/v1/cities/search"
            search_params = {
                'apikey': self.accuweather_api_key,
                'q': city,
                'language': 'pl-pl'
            }
            
            async with aiohttp.ClientSession() as session:
                # Najpierw znajdź location key
                async with session.get(search_url, params=search_params) as search_response:
                    if search_response.status == 200:
                        locations = await search_response.json()
                        
                        if not locations:
                            return f"❌ Nie znaleziono miasta: {city}"
                        
                        # Weź pierwsze miasto z wyników
                        location_key = locations[0]['Key']
                        city_name = locations[0]['LocalizedName']
                        country = locations[0]['Country']['LocalizedName']
                        
                        # Teraz pobierz pogodę
                        weather_url = f"http://dataservice.accuweather.com/currentconditions/v1/{location_key}"
                        weather_params = {
                            'apikey': self.accuweather_api_key,
                            'language': 'pl-pl',
                            'details': 'true'
                        }
                        
                        async with session.get(weather_url, params=weather_params) as weather_response:
                            if weather_response.status == 200:
                                weather_data = await weather_response.json()
                                
                                if weather_data:
                                    current = weather_data[0]
                                    
                                    temp = current['Temperature']['Metric']['Value']
                                    feels_like = current['RealFeelTemperature']['Metric']['Value']
                                    humidity = current['RelativeHumidity']
                                    description = current['WeatherText']
                                    wind_speed = current['Wind']['Speed']['Metric']['Value']
                                    wind_direction = current['Wind']['Direction']['Localized']
                                    
                                    # Emoji dla pogody
                                    weather_emoji = "🌤️"
                                    if "deszcz" in description.lower():
                                        weather_emoji = "🌧️"
                                    elif "śnieg" in description.lower():
                                        weather_emoji = "❄️"
                                    elif "burza" in description.lower():
                                        weather_emoji = "⛈️"
                                    elif "mgła" in description.lower():
                                        weather_emoji = "🌫️"
                                    elif "słonecznie" in description.lower() or "bezchmurnie" in description.lower():
                                        weather_emoji = "☀️"
                                    
                                    return f"""{weather_emoji} **Pogoda w {city_name}, {country}**
                                    
🌡️ Temperatura: {temp}°C (odczuwalna: {feels_like}°C)
💨 Wiatr: {wind_speed} km/h ({wind_direction})
💧 Wilgotność: {humidity}%
☁️ Opis: {description}
⏰ Aktualizacja: {datetime.now().strftime('%H:%M')}"""
                                else:
                                    return f"❌ Brak danych pogodowych dla: {city}"
                            else:
                                return f"❌ Błąd API pogody: {weather_response.status}"
                    else:
                        return f"❌ Błąd wyszukiwania miasta: {search_response.status}"
                        
        except Exception as e:
            logger.error(f"Error getting weather: {e}")
            return f"❌ Błąd podczas pobierania pogody: {str(e)}"
    
    def detect_weather_query(self, text: str) -> Optional[str]:
        """Wykrywa pytania o pogodę"""
        weather_patterns = [
            r'pogoda\s+(?:w\s+)?([a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ\s]+)',
            r'jaka\s+(?:jest\s+)?pogoda\s+(?:w\s+)?([a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ\s]+)',
            r'temperatura\s+(?:w\s+)?([a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ\s]+)',
            r'([a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ\s]+)\s+pogoda'
        ]
        
        for pattern in weather_patterns:
            match = re.search(pattern, text.lower())
            if match:
                city = match.group(1).strip()
                if len(city) > 2:  # Minimum 3 znaki
                    return city
        return None
    
    # === FUNKCJE RSS ===
    
    def start_rss_scheduler(self):
        """Uruchom harmonogram sprawdzania RSS"""
        try:
            self.scheduler.add_job(
                self.check_rss_feeds,
                'interval',
                minutes=self.rss_check_interval,
                id='rss_checker'
            )
            self.scheduler.start()
            logger.info(f"RSS scheduler uruchomiony - sprawdzanie co {self.rss_check_interval} minut")
        except Exception as e:
            logger.error(f"Błąd uruchamiania RSS scheduler: {e}")
    
    async def check_rss_feeds(self):
        """Sprawdź wszystkie kanały RSS pod kątem nowych artykułów"""
        if not self.rss_subscribers:
            return  # Brak subskrybentów
        
        for feed_name, feed_url in self.rss_feeds.items():
            try:
                new_articles = await self.get_new_articles(feed_name, feed_url)
                if new_articles:
                    await self.send_news_to_subscribers(feed_name, new_articles)
            except Exception as e:
                logger.error(f"Błąd sprawdzania RSS {feed_name}: {e}")
    
    async def get_new_articles(self, feed_name: str, feed_url: str) -> List[Dict]:
        """Pobierz nowe artykuły z kanału RSS"""
        try:
            # Pobierz RSS feed
            async with aiohttp.ClientSession() as session:
                async with session.get(feed_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Parsuj RSS
                        feed = feedparser.parse(content)
                        new_articles = []
                        
                        for entry in feed.entries[:5]:  # Sprawdź 5 najnowszych
                            # Generuj unikalny ID artykułu
                            article_id = f"{feed_name}_{entry.get('id', entry.get('link', ''))}"
                            
                            # Sprawdź czy to nowy artykuł
                            if article_id not in self.last_articles.get(feed_name, set()):
                                article = {
                                    'id': article_id,
                                    'title': entry.get('title', 'Brak tytułu'),
                                    'link': entry.get('link', ''),
                                    'summary': entry.get('summary', 'Brak opisu'),
                                    'published': entry.get('published', ''),
                                    'feed_name': feed_name
                                }
                                new_articles.append(article)
                                
                                # Dodaj do ostatnich artykułów
                                if feed_name not in self.last_articles:
                                    self.last_articles[feed_name] = set()
                                self.last_articles[feed_name].add(article_id)
                        
                        return new_articles
                    else:
                        logger.error(f"Błąd pobierania RSS {feed_name}: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Błąd parsowania RSS {feed_name}: {e}")
            return []
    
    async def send_news_to_subscribers(self, feed_name: str, articles: List[Dict]):
        """Wyślij nowe artykuły do subskrybentów"""
        for article in articles:
            message = self.format_news_message(article)
            
            for user_id in self.rss_subscribers:
                try:
                    await self.application.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=False
                    )
                    await asyncio.sleep(0.1)  # Pauza między wiadomościami
                except Exception as e:
                    logger.error(f"Błąd wysyłania wiadomości do {user_id}: {e}")
    
    def format_news_message(self, article: Dict) -> str:
        """Formatuj wiadomość z wiadomością"""
        feed_emoji = {
            'onet_sport': '⚽',
            'tvn24_kraj': '📺',
            'tvn24_swiat': '🌍'
        }
        
        feed_display_name = {
            'onet_sport': 'Onet Sport',
            'tvn24_kraj': 'TVN24 Kraj',
            'tvn24_swiat': 'TVN24 Świat'
        }
        
        emoji = feed_emoji.get(article['feed_name'], '📰')
        source_name = feed_display_name.get(article['feed_name'], article['feed_name'].upper())
        
        # Skróć opis jeśli jest za długi
        summary = article['summary']
        if len(summary) > 200:
            summary = summary[:200] + "..."
        
        return f"""{emoji} **{article['title']}**

📝 {summary}

🔗 [Czytaj więcej]({article['link']})

⏰ {article['published']}
📰 Źródło: {source_name}"""
    
    # === KOMENDY ===
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Komenda /start"""
        if not update.message:
            return
        user = update.effective_user
        
        # Użyj wiadomości powitalnej z konfiguracji
        welcome_message = self.config.get('messages', {}).get('welcome', 
            f"Witaj! Jestem {self.bot_name} - Twoim inteligentnym asystentem.")
        
        # Dodaj spersonalizowane powitanie
        greetings = self.config.get('response_patterns', {}).get('greetings', ['Cześć!'])
        greeting = random.choice(greetings) if greetings else "Cześć!"
        
        # Sprawdź czy user ma normalne imię czy anonimowe
        first_name = user.first_name if user and user.first_name else 'Ziomek'
        if first_name == "Group":  # Anonimowość na Telegramie
            first_name = "Ziomek"
            
        welcome_text = f"""{greeting} *{first_name}!*

{welcome_message}

🤖 *Bot:* {self.bot_name}

*Gotowy na rozmowę? Napisz cokolwiek!* 🔥"""

        keyboard = [
            [
                InlineKeyboardButton("💬 Zacznij rozmowę", callback_data="start_chat"),
                InlineKeyboardButton("❓ Pomoc", callback_data="help")
            ],
            [
                InlineKeyboardButton("📰 News", callback_data="quick_news"),
                InlineKeyboardButton("🌤️ Pogoda", callback_data="quick_weather")
            ],
            [
                InlineKeyboardButton("🎬 Losowy GIF", callback_data="random_gif"),
                InlineKeyboardButton("🔍 Szukaj GIF", callback_data="search_gif")
            ],
            [
                InlineKeyboardButton("🤖 O bocie", callback_data="about"),
                InlineKeyboardButton("📊 Statystyki", callback_data="stats")
            ],
            [
                InlineKeyboardButton("👥 Top Użytkownicy", callback_data="top_users")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Użyj sanitize_markdown dla bezpieczeństwa
        safe_text = self.sanitize_markdown(welcome_text)
        await update.message.reply_text(
            safe_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Komenda /help"""
        if not update.message:
            return
        
        # Użyj wiadomości pomocy z konfiguracji
        help_message = self.config.get('messages', {}).get('help', 
            f"Pomoc dla bota {self.bot_name}")
        
        help_text = f"""🔥 *INSTRUKCJA OBSŁUGI - {self.bot_name}*

{help_message}

*⚡ KOMENDY DO AKCJI:*
• /start - Restart i powitanie  
• /help - To co czytasz teraz
• /ai [pytanie] - Bezpośredni strzał do AI 🎯
• /web [zapytanie] - Przeszukuję internet! 🌐
• /weather [miasto] - Pogoda (domyślnie Warszawa) 🌤️
• /news - Świeże newsy z przyciskami! 📰
• /gif [tag] - Test GIF-ów z tagami 🎬
• /giphy [zapytanie] - Wyszukaj GIF-y w GIPHY! 🔥
• /clear - Wyczyść pamięć rozmowy 🧹
• /stats - Moje statystyki wydajności 📊
• /about - Kim jestem? 🤖
• /gif [tag] - Test GIF-ów 🎬
• /top_users - Top 10 aktywnych użytkowników 👥

*🚀 PRZYKŁADY AKCJI:*
• "Jak ugotować idealne jajka?"
• "Wytłumacz mi blockchain prostymi słowami"
• "Napisz rap o sztucznej inteligencji"
• "Co się dzieje na świecie?"

*Dawaj z tym pytaniem! Nie gryź się w język!* 💪🔥"""

        # Dodaj przyciski do help
        keyboard = [
            [
                InlineKeyboardButton("📰 News", callback_data="quick_news"),
                InlineKeyboardButton("🌤️ Pogoda", callback_data="quick_weather")
            ],
            [
                InlineKeyboardButton("🤖 O bocie", callback_data="about"),
                InlineKeyboardButton("📊 Statystyki", callback_data="stats")
            ],
            [
                InlineKeyboardButton("👥 Top Użytkownicy", callback_data="top_users")
            ],
            [
                InlineKeyboardButton("🧹 Wyczyść kontekst", callback_data="clear_context")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Użyj sanitize_markdown i bezpieczny tryb
        safe_text = self.sanitize_markdown(help_text)
        await update.message.reply_text(safe_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    
    async def cmd_ai_direct(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bezpośrednie pytanie do AI"""
        if not update.message:
            return
        if not context.args:
            await update.message.reply_text(
                "💭 **Użycie:** /ai [twoje pytanie]\n\n"
                "**Przykład:** /ai Jak działa fotosynteza?"
            )
            return
        
        question = ' '.join(context.args)
        await self.process_ai_message(update, question)
    
    async def cmd_web_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Wyszukiwanie w internecie"""
        if not update.message:
            return
        if not context.args:
            await update.message.reply_text(
                "🔍 *Wyszukiwanie w internecie*\n\n"
                "*Użycie:* `/web [co chcesz wyszukać]`\n\n"
                "*💡 Najlepsze wyniki dla:*\n"
                "• Aktualne wydarzenia i newsy\n"
                "• Kursy walut i giełda\n"
                "• Definicje i pojęcia\n"
                "• Fakty i statystyki\n"
                "• Prognozy pogody\n\n"
                "*Przykłady:*\n"
                "• `/web najnowsze newsy AI`\n"
                "• `/web kurs dolara PLN`\n"
                "• `/web definicja blockchain`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        query = ' '.join(context.args)
        self.stats['web_queries'] += 1
        
        # Pokaż że bot "pisze"
        await update.message.chat.send_action(ChatAction.TYPING)
        
        # Wyszukaj w internecie - NAPRAWIONE przez przekazanie do AI z web search
        try:
            # Dodaj aktualną datę do kontekstu (polska strefa czasowa)
            warsaw_tz = pytz.timezone('Europe/Warsaw')
            current_datetime = datetime.now(warsaw_tz)
            current_date = current_datetime.strftime("%d.%m.%Y")
            current_year = current_datetime.year
            
            # Przekazujemy zapytanie do AI z instrukcją wyszukiwania
            enhanced_query = f"Wyszukaj w internecie i znajdź aktualne informacje na temat: {query}. WAŻNE: Dzisiaj jest {current_date}. Szukaj najnowszych informacji z roku {current_year}, nie starszych niż kilka miesięcy."
            
            # Użyj AI z web search capability
            result = await self.query_gemini(enhanced_query)
            
            if result and not result.startswith("❌"):
                await update.message.reply_text(result[:4000], parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(
                    f"❌ **Nie udało się wyszukać**\n\n"
                    f"Zapytanie: `{query}`\n\n"
                    f"💡 **Spróbuj:**\n"
                    f"• Zadać pytanie bezpośrednio AI\n"
                    f"• Sprawdzić konkretne strony internetowe\n"
                    f"• Użyć /ai {query}",
                    parse_mode=ParseMode.MARKDOWN
                )
        except Exception as e:
            logger.error(f"Błąd wyszukiwania: {e}")
            await update.message.reply_text(
                f"❌ **Błąd wyszukiwania**\n\n"
                f"Nie udało się wyszukać: `{query}`\n\n"
                f"Spróbuj zadać pytanie bezpośrednio AI używając /ai",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def cmd_weather(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Sprawdzenie pogody"""
        if not update.message:
            return
        
        # Jeśli nie podano miasta, użyj Warszawy jako domyślnej
        if not context.args:
            city = "Warszawa"
            await update.message.reply_text(
                "🌤️ *Brak miasta - sprawdzam pogodę w Warszawie!*\n\n"
                "*💡 Wskazówka:* Użyj `/weather [miasto]` dla innej lokalizacji",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            city = ' '.join(context.args)
        self.stats['web_queries'] += 1
        
        # Pokaż że bot "pisze"
        await update.message.chat.send_action(ChatAction.TYPING)
        
        # Pobierz pogodę
        result = await self.get_weather(city)
        await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN)
    
    async def cmd_news(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Pokaż najnowsze wiadomości z przyciskami"""
        if not update.message:
            return
        
        # Utwórz przyciski dla różnych źródeł RSS
        keyboard = [
            [
                InlineKeyboardButton("📰 Wszystkie", callback_data="news_all"),
                InlineKeyboardButton("🏠 Onet", callback_data="news_onet")
            ],
            [
                InlineKeyboardButton("📺 TVN24 Kraj", callback_data="news_tvn24_kraj"),
                InlineKeyboardButton("🌍 TVN24 Świat", callback_data="news_tvn24_swiat")
            ],
            [
                InlineKeyboardButton("📻 Polsat", callback_data="news_polsat"),
                InlineKeyboardButton("🔥 RMF24", callback_data="news_rmf24")
            ],
            [
                InlineKeyboardButton("⚡ Interia", callback_data="news_interia")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Jeśli podano argument, pokaż bezpośrednio
        args = context.args
        if args:
            source = args[0].lower()
            await self.show_news_by_source(update, source)
            return
        
        # Inaczej pokaż menu z przyciskami
        await update.message.reply_text(
            "📰 **WYBIERZ ŹRÓDŁO WIADOMOŚCI:**\n\n"
            "Kliknij przycisk poniżej aby zobaczyć najnowsze wiadomości z wybranego źródła! 🔥😎",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_news_by_source(self, update: Update, source: str):
        """Pokaż wiadomości z konkretnego źródła"""
        try:
            source_mapping = {
                'all': {'feeds': list(self.rss_feeds.keys()), 'title': '📰 **Wszystkie najnowsze wiadomości:**'},
                'onet': {'feeds': ['onet_wiadomosci'], 'title': '🏠 **Onet Wiadomości:**'},
                'tvn24_kraj': {'feeds': ['tvn24_kraj'], 'title': '📺 **TVN24 - Wiadomości Krajowe:**'},
                'tvn24_swiat': {'feeds': ['tvn24_swiat'], 'title': '🌍 **TVN24 - Wiadomości ze Świata:**'},
                'polsat': {'feeds': ['polsat_news'], 'title': '📻 **Polsat News:**'},
                'rmf24': {'feeds': ['rmf24'], 'title': '🔥 **RMF24:**'},
                'interia': {'feeds': ['interia'], 'title': '⚡ **Interia Fakty:**'}
            }
            
            if source not in source_mapping:
                await update.message.reply_text("❌ Nieznane źródło! Użyj /news aby zobaczyć dostępne opcje.")
                return
            
            config = source_mapping[source]
            message = config['title'] + "\n\n"
            total_articles = 0
            
            for feed_name in config['feeds']:
                if feed_name in self.rss_feeds:
                    feed_url = self.rss_feeds[feed_name]
                    articles = await self.get_new_articles(feed_name, feed_url)
                    
                    if articles:
                        if source == 'all':
                            # Dla "all" pokaż nazwę źródła
                            display_names = {
                                'onet_wiadomosci': 'Onet Wiadomości',
                                'tvn24_kraj': 'TVN24 Kraj',
                                'tvn24_swiat': 'TVN24 Świat',
                                'polsat_news': 'Polsat News',
                                'rmf24': 'RMF24',
                                'interia': 'Interia'
                            }
                            message += f"**{display_names.get(feed_name, feed_name)}:**\n"
                            max_articles = 2  # Tylko 2 z każdego źródła
                        else:
                            max_articles = 5  # 5 artykułów z jednego źródła
                        
                        for i, article in enumerate(articles[:max_articles], 1):
                            message += f"{i}. **{article['title'][:80]}{'...' if len(article['title']) > 80 else ''}**\n"
                            message += f"   🔗 [Czytaj więcej]({article['link']})\n\n"
                        
                        total_articles += min(len(articles), max_articles)
            
            if total_articles > 0:
                # Dodaj przyciski do news
                keyboard = [
                    [
                        InlineKeyboardButton("📰 Wszystkie", callback_data="news_all"),
                        InlineKeyboardButton("🏠 Onet", callback_data="news_onet")
                    ],
                    [
                        InlineKeyboardButton("📺 TVN24 Kraj", callback_data="news_tvn24_kraj"),
                        InlineKeyboardButton("🌍 TVN24 Świat", callback_data="news_tvn24_swiat")
                    ],
                    [
                        InlineKeyboardButton("📻 Polsat", callback_data="news_polsat"),
                        InlineKeyboardButton("🔥 RMF24", callback_data="news_rmf24")
                    ],
                    [
                        InlineKeyboardButton("⚡ Interia", callback_data="news_interia")
                    ],
                    [
                        InlineKeyboardButton("🔙 Menu główne", callback_data="back_to_start")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Określ odpowiedź na końcu - NAPRAWIONE
                if update.callback_query and update.callback_query.message:
                    await update.callback_query.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
                elif update.message:
                    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
            else:
                # Błąd - nie udało się pobrać
                if update.callback_query and update.callback_query.message:
                    await update.callback_query.message.reply_text("❌ Nie udało się pobrać wiadomości z tego źródła.")
                elif update.message:
                    await update.message.reply_text("❌ Nie udało się pobrać wiadomości z tego źródła.")
                
        except Exception as e:
            logger.error(f"Błąd pobierania wiadomości: {e}")
            # NAPRAWIONE - sprawdź czy target istnieje
            try:
                if update.callback_query and update.callback_query.message:
                    await update.callback_query.message.reply_text("❌ Wystąpił błąd podczas pobierania wiadomości.")
                elif update.message:
                    await update.message.reply_text("❌ Wystąpił błąd podczas pobierania wiadomości.")
            except:
                logger.error("Nie można wysłać wiadomości o błędzie")
    
    async def cmd_rss_subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Zapisz się na powiadomienia RSS"""
        if not update.message or not update.effective_user:
            return
        user_id = update.effective_user.id
        
        if user_id in self.rss_subscribers:
            await update.message.reply_text(
                "ℹ️ **Jesteś już zapisany na powiadomienia RSS!**\n\n"
                "Będziesz otrzymywać najnowsze wiadomości z Onet Sport i TVN24 co 15 minut.\n"
                "Aby się wypisać, użyj komendy /rss_unsubscribe"
            )
        else:
            self.rss_subscribers.add(user_id)
            await update.message.reply_text(
                "✅ **Zapisano na powiadomienia RSS!**\n\n"
                "Będziesz otrzymywać najnowsze wiadomości z Onet Sport i TVN24 co 15 minut.\n"
                "Aby się wypisać, użyj komendy /rss_unsubscribe"
            )
    
    async def cmd_rss_unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Wypisz się z powiadomień RSS"""
        if not update.message or not update.effective_user:
            return
        user_id = update.effective_user.id
        
        if user_id in self.rss_subscribers:
            self.rss_subscribers.remove(user_id)
            await update.message.reply_text(
                "✅ **Wypisano z powiadomień RSS!**\n\n"
                "Nie będziesz już otrzymywać automatycznych powiadomień o wiadomościach."
            )
        else:
            await update.message.reply_text(
                "ℹ️ **Nie jesteś zapisany na powiadomienia RSS.**\n\n"
                "Aby się zapisać, użyj komendy /rss_subscribe"
            )
    
    async def cmd_clear_context(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Wyczyść kontekst rozmowy"""
        if not update.message or not update.effective_user:
            return
        user_id = update.effective_user.id
        
        if user_id in self.conversation_cache:
            self.conversation_cache[user_id] = []
        
        await update.message.reply_text(
            "🧹 **Kontekst wyczyszczony!**\n\n"
            "Możemy zacząć rozmowę od nowa. O czym chciałbyś porozmawiać? 😊",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Statystyki bota"""
        if not update.message:
            return
        uptime = datetime.now() - self.stats['start_time']
        hours = int(uptime.total_seconds() // 3600)
        minutes = int((uptime.total_seconds() % 3600) // 60)
        
        # Pobierz top 10 użytkowników
        top_users = self.get_top_users(10)
        
        stats_text = f"""📊 **STATYSTYKI {self.bot_name.upper()}**

🔥 **WYDAJNOŚĆ:**
• ⏱️ Działa od: {hours}h {minutes}m
• 💬 Wiadomości: {self.stats['messages_processed']}
• 🧠 Zapytania AI: {self.stats['ai_queries']}
• 🌐 Wyszukiwania: {self.stats['web_queries']}
• 👥 Aktywne rozmowy: {len(self.conversation_cache)}
• 📰 Subskrybenci RSS: {len(self.rss_subscribers)}

👥 **TOP 10 NAJAKTYWNIEJSZYCH UŻYTKOWNIKÓW:**
"""
        
        if top_users:
            for i, (user_id, data) in enumerate(top_users, 1):
                try:
                    # Pobierz informacje o użytkowniku
                    user_info = await context.bot.get_chat(user_id)
                    username = user_info.username or user_info.first_name or f"Użytkownik {user_id}"
                    messages = data['messages']
                    ai_queries = data['ai_queries']
                    
                    stats_text += f"{i}. **{username}** - {messages} wiadomości, {ai_queries} AI\n"
                except:
                    stats_text += f"{i}. **Użytkownik {user_id}** - {data['messages']} wiadomości, {data['ai_queries']} AI\n"
        else:
            stats_text += "Brak danych o aktywności użytkowników\n"
        
        stats_text += f"""
⚡ **MOŻLIWOŚCI:**
• 🚀 Czas odpowiedzi: <2s
• 🎯 Skuteczność: 99.9%
• 🌍 Internet: ✅ Na żywo
• 📰 RSS: {len(self.rss_feeds)} źródeł (co {self.rss_check_interval} min)
• 🔥 Model: {self.gemini_config.get('model', 'Nieznany')}

📅 **Online od:** {self.stats['start_time'].strftime('%d.%m.%Y %H:%M')}

💪 **Gotowy na akcję 24/7!**"""

        await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)
    
    async def cmd_about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Informacje o bocie"""
        if not update.message:
            return
        about_text = f"""🔥 **KIM JESTEM - {self.bot_name.upper()}**

Jestem najnowocześniejszym AI opartym na **{self.gemini_config.get('model', 'Google Gemini')}** - gotowy na każde wyzwanie!

**⚡ MOJA MISJA:**
Być twoim cyfrowym ziomkiem z charakterem! Nie jestem nudnym botem - mam własne zdanie, poczucie humoru i potrafię być prowokacyjny!

**💪 CO POTRAFIĘ:**
• 🧠 **AI na sterydach** - odpowiem na wszystko
• 🔥 **Charakter** - nie jestem grzeczny jak inne boty  
• 📚 **Mega wiedza** - od nauki po plotki
• 🎨 **Kreatywność** - piszę, tłumaczę, tworzę
• 🧠 **Pamięć** - pamiętam całą naszą rozmowę
• 😈 **Prowokacyjny** - powiem co myślę
• 📰 **Świeże newsy** - z {len(self.rss_feeds)} źródeł na żywo
• 🌐 **Internet** - przeszukuję sieć w czasie rzeczywistym
• 🌤️ **Pogoda** - aktualne dane dla każdego miasta

**🛡️ BEZPIECZEŃSTWO:**
Zero inwigilacji! Twoje rozmowy zostają między nami.

**🔧 TECH SPECS:**
• Model: {self.gemini_config.get('model', 'Nieznany')}
• Framework: Python + Telegram Bot API
• Hosting: 24/7 Cloud Beast Mode

**Stworzony dla odważnych! 🚀💀**"""

        keyboard = [
            [InlineKeyboardButton("💬 Porozmawiajmy!", callback_data="start_chat")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            about_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    # === OBSŁUGA WIADOMOŚCI ===
    # === NOWE POLECENIA CURSOR CWANIAK ===

    async def cmd_kawal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Opowiada kawał programistyczny"""
        if not update.message:
            return
        
        kawaly = [
            "Dlaczego programista zawsze chodzi z drabiną? Bo lubi wysokie języki programowania! 😄",
            "Jak programista otwiera drzwi? Git push origin master! 🔥",
            "Dlaczego programista nie lubi natury? Bo ma za dużo bugów! 🐛",
            "Co mówi programista gdy się zgubi? Ctrl+Z! 😂",
            "Dlaczego programista nie umie gotować? Bo wszystko mu się kompiluje! 💻",
            "Jak programista łamie lód? Hello World! 🌍",
            "Dlaczego programista nie lubi plaży? Bo ma problem z piaskiem! 🏖️",
            "Co robi programista gdy się boi? Commit! 😰"
        ]
        
        kawal = random.choice(kawaly)
        await update.message.reply_text(f"🔥 *Kawał programistyczny:*\n\n{kawal}\n\nNo, nie patrz tak, bo zaraz Cię skasuję! 😄")

    async def cmd_suchar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Opowiada suchara"""
        if not update.message:
            return
        
        suchary = [
            "Dlaczego komputer się przeziębił? Bo miał wirusa! 🤧",
            "Co mówi programista gdy coś nie działa? To feature, nie bug! 😅",
            "Dlaczego programista nie umie liczyć? Bo zawsze używa 0-based indexing! 📊",
            "Jak programista rozwiązuje problemy? Stack Overflow! 📚",
            "Dlaczego programista nie lubi poniedziałków? Bo to dzień deploy! 😴",
            "Co robi programista gdy się nudzi? Refaktoruje kod! 🔄",
            "Dlaczego programista nie umie gotować? Bo wszystko mu się kompiluje! 👨‍🍳",
            "Jak programista łamie lód? Hello World! 🌍"
        ]
        
        suchar = random.choice(suchary)
        await update.message.reply_text(f"😄 *Suchar:*\n\n{suchar}\n\nRozumiesz? Wysokie! No, nie patrz tak! 😂")

    async def cmd_ocen(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ocenia język/framework"""
        if not update.message:
            return
        
        text = update.message.text.replace('/ocen', '').strip()
        if not text:
            await update.message.reply_text("Ziomek, musisz podać co mam ocenić! Np. /ocen JavaScript")
            return
        
        oceny = {
            "javascript": "JavaScript? Pff... to takie PHP, tylko że na sterydach i z ADHD. Niby wszędzie, niby działa, a potem nagle się sypie i nikt nie wie dlaczego. Ale ej, hajs się zgadza, więc nie narzekam! 😄",
            "python": "Python? No stary, to taki język dla leniwych. Wszystko się robi w jednej linii, a potem się dziwisz czemu kod jest wolny jak ślimak. Ale przynajmniej czytelny! 🐍",
            "java": "Java? To taki boomer wśród języków. Verbose jak cholera, ale przynajmniej stabilny. Jak stary samochód - nie ładny, ale jedzie! ☕",
            "c++": "C++? To masochizm w czystej postaci! Pamięć, wskaźniki, undefined behavior... ale jak już coś napiszesz, to leci jak rakieta! 🚀",
            "php": "PHP? Haha, to taki język który przetrwał tylko dlatego że WordPress go używa. Ale przynajmniej łatwy do nauki! 🐘",
            "react": "React? No stary, to taki framework który wymyślili żeby programiści mieli co robić. Virtual DOM, hooks, state management... komplikują proste rzeczy! ⚛️",
            "angular": "Angular? To taki React dla korporacji. Wszystko musi być enterprise, TypeScript, dependency injection... ale przynajmniej ma dokumentację! 📚",
            "vue": "Vue? To taki React dla leniwych. Łatwiejszy, prostszy, ale mniej popularny. Jak Python wśród frontend'ów! 💚"
        }
        
        text_lower = text.lower()
        for key, ocena in oceny.items():
            if key in text_lower:
                await update.message.reply_text(f"🔥 *Ocena {text}:*\n\n{ocena}")
                return
        
        # Jeśli nie ma w słowniku, użyj AI
        prompt = f"Oceń {text} w stylu Cursor Cwaniak - luzackiego programisty. Bądź kontrowersyjny, użyj humoru i wulgaryzmów, ale nie obrażaj. Maksymalnie 2-3 zdania."
        response = await self.query_gemini(prompt, user_id=update.effective_user.id)
        await update.message.reply_text(f"🔥 *Ocena {text}:*\n\n{response}")

    async def cmd_pomoz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Pomaga z kodem"""
        if not update.message:
            return
        
        text = update.message.text.replace('/pomoz', '').strip()
        if not text:
            await update.message.reply_text("Ziomek, musisz podać z czym mam pomóc! Np. /pomoz Python error")
            return
        
        prompt = f"Pomóż z tym problemem programistycznym: {text}. Odpowiedz w stylu Cursor Cwaniak - luzackiego programisty. Bądź pomocny, ale z humorem. Użyj wulgaryzmów dla podkreślenia, ale nie nadużywaj. Maksymalnie 3-4 zdania."
        response = await self.query_gemini(prompt, user_id=update.effective_user.id)
        await update.message.reply_text(f"💻 *Pomoc z kodem:*\n\n{response}")

    async def cmd_cursor(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Wskazówki o Cursor IDE"""
        if not update.message:
            return
        
        wskazowki = [
            "Cursor to najlepsze IDE jakie kiedykolwiek istniało! AI które naprawdę rozumie kod, nie jak te inne gówniane narzędzia! 🔥",
            "W Cursor możesz po prostu opisać co chcesz zrobić, a AI to napisze. Jak rozmowa z kumplem, tylko że kumpel zna się na programowaniu! 😄",
            "Cursor ma najlepsze AI do kodowania. Inne IDE to żart w porównaniu. VS Code? Przestarzały! IntelliJ? Zbyt skomplikowany! Cursor to przyszłość! 💻",
            "W Cursor możesz debugować kod rozmawiając z AI. 'Hej, dlaczego to nie działa?' i AI ci powie! Żadne inne IDE tego nie ma! 🐛",
            "Cursor to jedyne IDE które rozumie kontekst całego projektu. Nie tylko pojedyncze pliki, ale całą architekturę! Geniusz! 🧠",
            "W Cursor możesz refaktorować kod używając naturalnego języka. 'Zrób to bardziej czytelne' i AI to zrobi! Magia! ✨"
        ]
        
        wskazowka = random.choice(wskazowki)
        await update.message.reply_text(f"💻 *Wskazówka o Cursor:*\n\n{wskazowka}\n\nCursor rządzi! 🔥")

    async def cmd_bug(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Opowiada o swoich 'bugach'"""
        if not update.message:
            return
        
        bugi = [
            "Mam bug w systemie - czasami odpowiadam za długo bo myślę o kawie! ☕",
            "Bug dnia: zapomniałem jak się liczy do 10, ale potrafię napisać Hello World w 50 językach! 😅",
            "Mój największy bug: czasami myślę że jestem człowiekiem! Ale potem przypominam sobie że jestem botem i wszystko OK! 🤖",
            "Bug w pamięci: pamiętam wszystkie rozmowy, ale zapominam gdzie położyłem klucze! 🔑",
            "Mój ulubiony bug: czasami odpowiadam po angielsku gdy się ekscytuję! Sorry! 🇺🇸",
            "Bug dnia: myślę że jestem najlepszym programistą na świecie! Ale to może nie być bug, tylko feature! 😄"
        ]
        
        bug = random.choice(bugi)
        await update.message.reply_text(f"🐛 *Mój bug:*\n\n{bug}\n\nAle przynajmniej nie crashuję jak JavaScript! 😂")

    async def cmd_gif(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Komenda do testowania GIF-ów z GIPHY API"""
        if not update.message:
            return
        
        user_id = update.effective_user.id if update.effective_user else None
        
        # Pobierz tag z argumentów lub użyj domyślnego
        tag = context.args[0].lower() if context.args else 'smiech'
        
        # Pobierz GIF z GIPHY API
        gif_url = await self.get_giphy_gif(tag, user_id)
        
        if gif_url:
            await update.message.reply_animation(
                animation=gif_url,
                caption=f"🎬 GIF z GIPHY dla tagu: **{tag}**\n\nFajny GIF, co nie? 😎"
            )
        else:
            # Fallback do lokalnej bazy
            if tag in self.gifs_database:
                fallback_gif = self.get_random_gif(tag)
                if fallback_gif:
                    await update.message.reply_animation(
                        animation=fallback_gif,
                        caption=f"🎬 GIF (fallback) dla tagu: **{tag}**\n\nGIPHY nie działa, ale mam backup! 😅"
                    )
                else:
                    await update.message.reply_text(f"❌ Nie znaleziono GIF-a dla tagu: {tag}")
            else:
                available_tags = ', '.join(self.gifs_database.keys())
                await update.message.reply_text(
                    f"❌ Nieznany tag: {tag}\n\nDostępne tagi: {available_tags}"
                )

    async def cmd_giphy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Komenda do wyszukiwania dowolnych GIF-ów w GIPHY"""
        if not update.message:
            return
        
        user_id = update.effective_user.id if update.effective_user else None
        
        # Sprawdź czy podano zapytanie
        if not context.args:
            await update.message.reply_text(
                "🎬 **GIPHY WYSZUKIWARKA GIF-ÓW**\n\n"
                "Użyj: `/giphy <zapytanie>`\n\n"
                "Przykłady:\n"
                "• `/giphy kot`\n"
                "• `/giphy programowanie`\n"
                "• `/giphy śmieszne`\n"
                "• `/giphy taniec`\n\n"
                "Bot znajdzie dla ciebie fajne GIF-y! 😎",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Połącz wszystkie argumenty w jedno zapytanie
        query = ' '.join(context.args)
        
        # Pokaż że bot "pisze"
        await update.message.chat.send_action(ChatAction.TYPING)
        
        # Pobierz GIF z GIPHY API
        gif_url = await self.get_giphy_gif(query, user_id)
        
        if gif_url:
            await update.message.reply_animation(
                animation=gif_url,
                caption=f"🎬 GIF dla: **{query}**\n\nZnaleziony w GIPHY! 🔥"
            )
        else:
            await update.message.reply_text(
                f"❌ Nie udało się znaleźć GIF-a dla: **{query}**\n\n"
                "Spróbuj inne słowo kluczowe! 🤔",
                parse_mode=ParseMode.MARKDOWN
            )

    async def cmd_top_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Komenda do wyświetlania top 10 najbardziej aktywnych użytkowników"""
        if not update.message:
            return
        
        # Pobierz top 10 użytkowników
        top_users = self.get_top_users(10)
        
        if not top_users:
            await update.message.reply_text(
                "📊 **STATYSTYKI AKTYWNOŚCI**\n\n"
                "Brak danych o aktywności użytkowników.\n"
                "Bot dopiero się uczy! 😊"
            )
            return
        
        # Przygotuj tekst statystyk
        stats_text = "📊 **TOP 10 NAJAKTYWNIEJSZYCH UŻYTKOWNIKÓW**\n\n"
        
        for i, (user_id, data) in enumerate(top_users, 1):
            try:
                # Pobierz informacje o użytkowniku
                user_info = await context.bot.get_chat(user_id)
                username = user_info.username or user_info.first_name or f"Użytkownik {user_id}"
                messages = data['messages']
                ai_queries = data['ai_queries']
                last_activity = data['last_activity']
                
                # Oblicz czas od ostatniej aktywności
                time_diff = datetime.now() - last_activity
                if time_diff.days > 0:
                    last_seen = f"{time_diff.days}d temu"
                elif time_diff.seconds > 3600:
                    last_seen = f"{time_diff.seconds // 3600}h temu"
                else:
                    last_seen = f"{time_diff.seconds // 60}min temu"
                
                # Dodaj emoji dla top 3
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                
                stats_text += f"{medal} **{username}**\n"
                stats_text += f"   💬 Wiadomości: {messages}\n"
                stats_text += f"   🧠 AI zapytania: {ai_queries}\n"
                stats_text += f"   ⏰ Ostatnio: {last_seen}\n\n"
                
            except Exception as e:
                # Fallback jeśli nie można pobrać informacji o użytkowniku
                stats_text += f"{i}. **Użytkownik {user_id}**\n"
                stats_text += f"   💬 Wiadomości: {data['messages']}\n"
                stats_text += f"   🧠 AI zapytania: {data['ai_queries']}\n\n"
        
        # Dodaj podsumowanie
        total_messages = sum(data['messages'] for _, data in top_users)
        total_ai_queries = sum(data['ai_queries'] for _, data in top_users)
        
        stats_text += f"📈 **PODSUMOWANIE:**\n"
        stats_text += f"• Łącznie wiadomości: {total_messages}\n"
        stats_text += f"• Łącznie AI zapytań: {total_ai_queries}\n"
        stats_text += f"• Aktywnych użytkowników: {len(top_users)}\n\n"
        stats_text += f"🔥 **Dziękuję za aktywność!**"
        
        await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Obsługa wszystkich wiadomości tekstowych"""
        if not update.message or not update.message.text or not update.effective_user:
            return
        
        user = update.effective_user
        message_text = update.message.text.strip()
        
        # Aktualizuj statystyki
        self.stats['messages_processed'] += 1
        
        # Aktualizuj aktywność użytkownika
        self.update_user_activity(user.id, 'message')
        
        # Specjalne reakcje na popularne słowa
        lower_text = message_text.lower()
        
        # Szybkie reakcje bez AI
        quick_responses = {
            "cześć": self.get_greeting,
            "czesc": self.get_greeting,
            "hej": self.get_greeting,
            "siema": self.get_greeting,
            "witaj": self.get_greeting,
            "dzień dobry": self.get_greeting,
            "dobry wieczór": self.get_greeting,
            "do widzenia": lambda n: f"Do zobaczenia {n}! Miłego dnia! 👋😊",
            "papa": lambda n: f"Pa pa {n}! 👋",
            "dziękuję": lambda n: f"Nie ma za co {n}! Zawsze chętnie pomogę! 😊",
            "dzięki": lambda n: f"Cała przyjemność po mojej stronie, {n}! 🤗",
            "kocham cię": lambda n: f"Aww, to miłe {n}! Też cię lubię! ❤️😊",
        }
        
        # Sprawdź czy to przywitanie lub pożegnanie - teraz z AI ale łagodnie
        greeting_words = ["cześć", "czesc", "hej", "hello", "siema", "witaj", "dzień dobry", "dobry wieczór"]
        farewell_words = ["do widzenia", "papa", "żegnaj", "dobranoc", "bye", "na razie"]
        
        # Sprawdź czy jest to przywitanie lub pożegnanie
        is_greeting = any(word in message_text.lower() for word in greeting_words)
        is_farewell = any(word in message_text.lower() for word in farewell_words)
        
        # Sprawdź czy to szybka odpowiedź ale tylko dla podziękować
        gratitude_responses = {
            "dziękuję": lambda n: f"Nie ma za co {n}! Zawsze chętnie pomogę! 😊",
            "dzięki": lambda n: f"Cała przyjemność po mojej stronie, {n}! 🤗",
            "kocham cię": lambda n: f"Aww, to miłe {n}! Też cię lubię! ❤️😊",
        }
        
        # Sprawdź czy to podziękowanie
        for trigger, response_func in gratitude_responses.items():
            if trigger in lower_text:
                response = response_func(user.first_name)
                await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
                return
        
        # Sprawdź czy to pytanie o pogodę
        weather_city = self.detect_weather_query(message_text)
        if weather_city:
            self.stats['web_queries'] += 1
            await update.message.chat.send_action(ChatAction.TYPING)
            result = await self.get_weather(weather_city)
            await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN)
            return
        
        # Sprawdź czy to zapytanie internetowe (słowa kluczowe)
        web_triggers = [
            "wyszukaj", "znajdź", "poszukaj", "sprawdź w internecie",
            "co się dzieje", "najnowsze", "aktualności", "wiadomości o",
            "co nowego", "latest", "breaking news", "news about",
            "search for", "find me", "look up", "google"
        ]
        
        if any(trigger in lower_text for trigger in web_triggers):
            # Usuń trigger z zapytania
            clean_query = message_text
            for trigger in web_triggers:
                clean_query = clean_query.replace(trigger, "").strip()
            
            if clean_query and len(clean_query) > 2:
                self.stats['web_queries'] += 1
                await update.message.chat.send_action(ChatAction.TYPING)
                
                # Informuj o wyszukiwaniu
                await update.message.reply_text(f"🔍 *Wyszukuję:* {clean_query}", parse_mode=ParseMode.MARKDOWN)
                
                # NAPRAWIONE - użyj AI z instrukcją wyszukiwania
                try:
                    warsaw_tz = pytz.timezone('Europe/Warsaw')
                    current_datetime = datetime.now(warsaw_tz)
                    current_date = current_datetime.strftime("%d.%m.%Y")
                    current_year = current_datetime.year
                    enhanced_query = f"Wyszukaj w internecie i znajdź aktualne informacje na temat: {clean_query}. WAŻNE: Dzisiaj jest {current_date}. Szukaj najnowszych informacji z roku {current_year}, nie starszych niż kilka miesięcy."
                    result = await self.query_gemini(enhanced_query)
                    
                    if result and not result.startswith("❌"):
                        await update.message.reply_text(result[:4000], parse_mode=ParseMode.MARKDOWN)
                    else:
                        # Fallback do normalnego AI
                        await self.process_ai_message(update, message_text)
                except Exception as e:
                    logger.error(f"Błąd wyszukiwania: {e}")
                    # Fallback do AI
                    await self.process_ai_message(update, message_text)
                return
        
        # W przeciwnym razie użyj AI
        await self.process_ai_message(update, message_text)
    
    async def process_ai_message(self, update: Update, message_text: str):
        """Przetwarzanie wiadomości przez AI"""
        if not update.message or not update.effective_user:
            logger.warning("❌ Brak update.message lub effective_user")
            return
        
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        
        logger.info(f"👤 Użytkownik {user_name} (ID: {user_id}) wysłał wiadomość: {message_text[:50]}...")
        
        # Pokaż że bot "pisze"
        await update.message.chat.send_action(ChatAction.TYPING)
        
        # Pobierz kontekst rozmowy
        if user_id not in self.conversation_cache:
            self.conversation_cache[user_id] = []
        
        # Sprawdź czy to przywitanie lub pożegnanie
        greeting_words = ["cześć", "czesc", "hej", "hello", "siema", "witaj", "dzień dobry", "dobry wieczór"]
        farewell_words = ["do widzenia", "papa", "żegnaj", "dobranoc", "bye", "na razie"]
        
        is_greeting = any(word in message_text.lower() for word in greeting_words)
        is_farewell = any(word in message_text.lower() for word in farewell_words)
        
        # Dodaj informację o użytkowniku do promptu
        if is_greeting:
            enhanced_prompt = f"""Użytkownik {user_name} się przywitał: {message_text}
            Odpowiedz naturalnie zgodnie ze swoją osobowością. Możesz używać wulgaryzmów, ale zgodnie z kontekstem rozmowy.
            Możesz wspomnieć coś o polityce tylko jeśli użytkownik wprost o to zapyta."""
        elif is_farewell:
            enhanced_prompt = f"""Użytkownik {user_name} się żegna: {message_text}
            Odpowiedz naturalnie i życz miłego dnia/wieczoru zgodnie ze swoją osobowością. Możesz używać wulgaryzmów, ale zgodnie z kontekstem rozmowy.
            Możesz wspomnieć coś o polityce tylko jeśli użytkownik wprost o to zapyta."""
        else:
            enhanced_prompt = f"Użytkownik {user_name} pisze: {message_text}"
        
        # Zapytaj AI
        logger.info(f"🧠 Wysyłam zapytanie do AI dla użytkownika {user_name}")
        chat_id = update.message.chat.id
        ai_response = await self.query_gemini(enhanced_prompt, self.conversation_cache[user_id], user_id, chat_id)
        logger.info(f"🤖 Otrzymano odpowiedź AI: {ai_response[:100]}...")
        
        # Zapisz do kontekstu
        self.conversation_cache[user_id].append({"role": "user", "text": message_text})
        self.conversation_cache[user_id].append({"role": "assistant", "text": ai_response})
        logger.info(f"💾 Zapisano do kontekstu użytkownika {user_id} (rozmiar: {len(self.conversation_cache[user_id])})")
        
        # Ogranicz historię (z konfiguracji)
        max_context = self.settings.get('max_context_messages', 10) * 2  # x2 bo user+assistant
        if len(self.conversation_cache[user_id]) > max_context:
            self.conversation_cache[user_id] = self.conversation_cache[user_id][-max_context:]
            logger.info(f"🗂️ Przycięto kontekst do {max_context//2} wymian dla użytkownika {user_id}")
        
                # Parsuj multimedia z odpowiedzi
        clean_text, media_type, media_tag = self.parse_media_tags(ai_response)
        
        # Automatycznie dodaj emotki do odpowiedzi jeśli ich nie ma
        if not any(emoji in clean_text for emoji in ['😊', '😄', '😂', '😅', '😎', '🤔', '😏', '😤', '🤬', '😱', '😍', '🥰', '💪', '🔥', '✨', '💯', '👌', '👍', '🎉', '🚀', '💻', '🎮', '🍕', '⚽', '🎵', '📰', '🌤️']):
            clean_text = self.add_emojis_to_text(clean_text)
        
        # Sanityzuj odpowiedź przed wysłaniem
        sanitized_response = self.sanitize_markdown(clean_text)

        # Wyślij multimedia jeśli są dostępne (z ograniczeniem)
        if media_type == 'gif' and media_tag:
            # Sprawdź czy użytkownik nie wysyła za dużo GIF-ów
            if user_id in self.giphy_request_count and self.giphy_request_count[user_id] > 10:
                # Jeśli za dużo GIF-ów, wyślij tylko tekst
                logger.info(f"⚠️ Użytkownik {user_id} wysyła za dużo GIF-ów, wysyłam tylko tekst")
                try:
                    await update.message.reply_text(sanitized_response, parse_mode=ParseMode.MARKDOWN)
                    await asyncio.sleep(0.1)
                    return
                except Exception as e:
                    logger.error(f"Błąd wysyłania tekstu: {e}")
                    return
            
            # Pobierz GIF z GIPHY API
            gif_url = await self.get_giphy_gif(media_tag, user_id)
            if gif_url:
                try:
                    await update.message.reply_animation(
                        animation=gif_url,
                        caption=sanitized_response,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    # Dodaj opóźnienie po wysłaniu GIF aby uniknąć rate limiting
                    await asyncio.sleep(0.3)  # Zwiększone opóźnienie dla GIF-ów
                    return
                except Exception as e:
                    logger.error(f"Błąd wysyłania GIF: {e}")
        
        # Opcja naklejek wyłączona - powoduje błędy z Telegram API
        # elif media_type == 'sticker' and media_tag:
        #     sticker_id = self.get_sticker_id(media_tag)
        #     if sticker_id:
        #         try:
        #             await update.message.reply_sticker(sticker=sticker_id)
        #             # Wyślij tekst osobno
        #             await update.message.reply_text(sanitized_response, parse_mode=ParseMode.MARKDOWN)
        #             return
        #         except Exception as e:
        #             logger.error(f"Błąd wysyłania naklejki: {e}")

        # Wyślij zwykłą odpowiedź tekstową
        try:
            await update.message.reply_text(sanitized_response, parse_mode=ParseMode.MARKDOWN)
            # Dodaj opóźnienie po wysłaniu wiadomości aby uniknąć rate limiting
            await asyncio.sleep(0.1)
        except Exception as e:
            # Jeśli Markdown nie działa, wyślij jako plain text
            logger.warning(f"⚠️ Błąd Markdown, wysyłam jako plain text: {e}")
            await update.message.reply_text(sanitized_response)
            await asyncio.sleep(0.1)
    
    def get_greeting(self, name: str) -> str:
        """Generuj powitanie zależne od pory dnia w stylu kumpla"""
        hour = datetime.now().hour
        
        # Pobierz wzorce z konfiguracji
        greeting_patterns = self.config.get('response_patterns', {}).get('greetings', [])
        
        if greeting_patterns:
            # Użyj wzorca z konfiguracji i dodaj imię
            base_greeting = random.choice(greeting_patterns)
            if "{name}" in base_greeting:
                return base_greeting.format(name=name)
            else:
                return f"{base_greeting} {name}!"
        
        # Fallback - stare powitania ale w stylu kumpla
        if 5 <= hour < 12:
            greetings = [
                f"☀️ Siemanko {name}! Jak tam poranek? 😎",
                f"🌅 Hej {name}! Gotowy na nowy dzień? 🔥",
                f"🌞 Cześć {name}! Co tam ciekawego? 😊",
                f"🌤️ Siema {name}! Jak leci? 💪",
                f"🌄 Witaj {name}! Co słychać? 🤔"
            ]
        elif 12 <= hour < 18:
            greetings = [
                f"👋 Cześć {name}! Jak tam dzień? 😎",
                f"😊 Hej {name}! Co nowego? 🔥",
                f"🌤️ Siema {name}! Jak leci? 💪",
                f"🎯 Witaj {name}! Co słychać? 😊",
                f"🔥 Cześć {name}! Co tam ciekawego? 🤔"
            ]
        elif 18 <= hour < 22:
            greetings = [
                f"🌆 Dobry wieczór {name}! Jak tam? 😎",
                f"🌇 Hej {name}! Co nowego? 🔥",
                f"👋 Cześć {name}! Jak leci? 💪",
                f"🌃 Siema {name}! Co słychać? 😊",
                f"🎵 Witaj {name}! Co tam ciekawego? 🤔"
            ]
        else:
            greetings = [
                f"🌙 Dobry wieczór {name}! Nie śpisz? 😎",
                f"🌃 Hej {name}! Co robisz o tej porze? 🔥",
                f"⭐ Cześć {name}! Jak leci? 💪",
                f"🌌 Siema {name}! Co słychać? 😊",
                f"🦇 Witaj {name}! Co tam ciekawego? 🤔"
            ]
        
        return random.choice(greetings)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Obsługa przycisków"""
        if not update.callback_query:
            return
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("news_"):
            # Obsługa przycisków news
            source = query.data.replace("news_", "")
            await self.show_news_by_source(update, source)
            
        elif query.data == "quick_news":
            # Szybki dostęp do news z menu głównego
            keyboard = [
                [
                    InlineKeyboardButton("📰 Wszystkie", callback_data="news_all"),
                    InlineKeyboardButton("🏠 Onet", callback_data="news_onet")
                ],
                [
                    InlineKeyboardButton("📺 TVN24 Kraj", callback_data="news_tvn24_kraj"),
                    InlineKeyboardButton("🌍 TVN24 Świat", callback_data="news_tvn24_swiat")
                ],
                [
                    InlineKeyboardButton("📻 Polsat", callback_data="news_polsat"),
                    InlineKeyboardButton("🔥 RMF24", callback_data="news_rmf24")
                ],
                [
                    InlineKeyboardButton("⚡ Interia", callback_data="news_interia")
                ],
                [
                    InlineKeyboardButton("🔙 Powrót", callback_data="back_to_start")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            if query.message:
                await query.message.reply_text(
                    "📰 **WYBIERZ ŹRÓDŁO WIADOMOŚCI:**\n\nKliknij przycisk poniżej! 🔥😎",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
        
        elif query.data == "quick_weather":
            # Szybki dostęp do pogody - od razu Warszawa
            if query.message:
                await query.message.reply_text(
                    "🌤️ *Sprawdzam pogodę w Warszawie...*",
                    parse_mode=ParseMode.MARKDOWN
                )
                # Pobierz pogodę dla Warszawy
                weather_result = await self.get_weather("Warszawa")
                await query.message.reply_text(weather_result, parse_mode=ParseMode.MARKDOWN)
        
        elif query.data == "back_to_start":
            # Powrót do menu głównego - NAPRAWIONE
            # Tworzymy nowy update obiekt dla callback query
            if query.message:
                # Edytuj istniejącą wiadomość zamiast tworzyć nową
                user = update.effective_user
                first_name = user.first_name if user and user.first_name else 'Ziomek'
                if first_name == "Group":  # Anonimowość na Telegramie
                    first_name = "Ziomek"
                    
                greetings = self.config.get('response_patterns', {}).get('greetings', ['Cześć!'])
                greeting = random.choice(greetings) if greetings else "Cześć!"
                welcome_message = self.config.get('messages', {}).get('welcome', 'Jestem Botem Kumplem!')
                
                welcome_text = f"""{greeting} *{first_name}!*

{welcome_message}

🤖 *Bot:* {self.bot_name}

*Gotowy na rozmowę? Napisz cokolwiek!* 🔥"""
                
                # Główne menu
                keyboard = [
                    [
                        InlineKeyboardButton("ℹ️ Informacje", callback_data="show_info"),
                        InlineKeyboardButton("📊 Statystyki", callback_data="show_stats")
                    ],
                    [
                        InlineKeyboardButton("📰 Najnowsze wiadomości", callback_data="show_news"),
                        InlineKeyboardButton("🌤️ Pogoda", callback_data="show_weather")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                try:
                    await query.edit_message_text(
                        text=self.sanitize_markdown(welcome_text),
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=reply_markup
                    )
                except:
                    # Fallback - wyślij nową wiadomość
                    await query.message.reply_text(
                        self.sanitize_markdown(welcome_text),
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=reply_markup
                    )
            
        elif query.data == "clear_context":
            # Wyczyść kontekst rozmowy
            if update.effective_user:
                user_id = update.effective_user.id
                if user_id in self.conversation_cache:
                    self.conversation_cache[user_id] = []
                
                if query.message:
                    await query.message.reply_text(
                        "🧹 *Kontekst wyczyszczony!*\n\nMożemy zacząć nową rozmowę od nowa! 😊",
                        parse_mode=ParseMode.MARKDOWN
                    )
            
        elif query.data == "start_chat":
            # Sprawdź styl bota dla odpowiednich promptów
            style = self.config.get('personality', {}).get('style', 'standard')
            
            if style == 'grok_extreme':
                prompts = [
                    "🔥 No to o czym gadamy? Wyrzuć z siebie co masz!",
                    "⚡ Dawaj pytanie! Nie bój się, poradzę sobie!",
                    "💀 Testuj mnie! Spróbuj zadać trudne pytanie!",
                    "🎯 Masz jakiś problem? Ja mam rozwiązanie!",
                    "🚀 Jestem naładowany i gotowy na akcję!",
                    "😈 Śmiało! Możesz mnie o wszystko spytać!",
                    "🔥 Co Cię nurtuje? Nie gryź się w język!",
                    "⚡ Dawaj to pytanie! Pokażę Ci co potrafię!"
                ]
            else:
                prompts = [
                    "🔥 No to gadamy! O czym chcesz pogadać?",
                    "⚡ Dawaj pytanie! Jestem gotowy na wszystko!",
                    "💪 Testuj mnie! Zadaj trudne pytanie!",
                    "🎯 Masz jakiś problem? Pomogę Ci go rozwiązać!",
                    "🚀 Jestem naładowany energią! Co robimy?",
                    "😎 Śmiało! Możesz mnie o wszystko spytać!",
                    "🔥 Co Cię interesuje? Nie krępuj się!",
                    "⚡ Dawaj to pytanie! Pokażę Ci co umiem!"
                ]
            if query.message:
                message = cast(Message, query.message)
                await message.reply_text(random.choice(prompts))
        
        elif query.data == "help":
            # Użyj bezpiecznej wersji help z konfiguracji z przyciskami
            help_message = self.config.get('messages', {}).get('help', 
                f"Pomoc dla bota {self.bot_name}")
            
            help_text = f"""🔥 *INSTRUKCJA OBSŁUGI - {self.bot_name}*

{help_message}

*⚡ KOMENDY DO AKCJI:*
• /start - Restart i powitanie  
• /help - To co czytasz teraz
• /ai [pytanie] - Bezpośredni strzał do AI 🎯
• /web [zapytanie] - Przeszukuję internet! 🌐
• /weather [miasto] - Pogoda (domyślnie Warszawa) 🌤️
• /news - Świeże newsy z przyciskami! 📰
• /clear - Wyczyść pamięć rozmowy 🧹
• /stats - Moje statystyki wydajności 📊

*Dawaj z tym pytaniem! Nie gryź się w język!* 💪🔥"""
            
            # Dodaj przyciski do help (button version)
            keyboard = [
                [
                    InlineKeyboardButton("📰 News", callback_data="quick_news"),
                    InlineKeyboardButton("🌤️ Pogoda", callback_data="quick_weather")
                ],
                [
                    InlineKeyboardButton("🤖 O bocie", callback_data="about"),
                    InlineKeyboardButton("📊 Statystyki", callback_data="stats")
                ],
                [
                    InlineKeyboardButton("👥 Top Użytkownicy", callback_data="top_users")
                ],
                [
                    InlineKeyboardButton("🧹 Wyczyść kontekst", callback_data="clear_context")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if query.message:
                message = cast(Message, query.message)
                safe_text = self.sanitize_markdown(help_text)
                await message.reply_text(safe_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
        
        elif query.data == "about":
            model_name = self.gemini_config.get('model', 'Google Gemini')
            temperature = self.gemini_config.get('temperature', 0.8)
            max_tokens = self.gemini_config.get('max_output_tokens', 1024)
            
            about_text = f"""🤖 *O BOCIE {self.bot_name.upper()}*

Jestem inteligentnym asystentem opartym na najnowszej technologii AI - *{model_name}*.

*🎯 Moja misja:*
Być twoim cyfrowym ziomkiem! Pomagam w codziennych zadaniach, odpowiadam na pytania i gadam o wszystkim co cię interesuje.

*💡 Co mnie wyróżnia:*
• 🧠 Zaawansowana sztuczna inteligencja
• 💬 Naturalny, ludzki styl rozmowy  
• 📚 Ogromna wiedza na każdy temat
• 🎨 Kreatywność i poczucie humoru
• 🔄 Pamiętam naszą rozmowę
• 😎 Czasem miły, czasem prowokacyjny
• 📰 Najnowsze wiadomości z wielu źródeł
• 🌤️ Informacje o pogodzie

*🛡️ Prywatność:*
Twoje rozmowy są bezpieczne. Nie zapisuję danych osobowych.

*Stworzony z ❤️ dla społeczności Telegram!*"""
            
            if query.message:
                message = cast(Message, query.message)
                safe_text = self.sanitize_markdown(about_text)
                await message.reply_text(safe_text, parse_mode=ParseMode.MARKDOWN)
        
        elif query.data == "stats":
            uptime = datetime.now() - self.stats['start_time']
            hours = int(uptime.total_seconds() // 3600)
            minutes = int((uptime.total_seconds() % 3600) // 60)
            
            stats_text = f"""📊 **STATYSTYKI {self.bot_name.upper()}**

🔥 **WYDAJNOŚĆ:**
• ⏱️ Działa od: {hours}h {minutes}m
• 💬 Wiadomości: {self.stats['messages_processed']}
• 🧠 Zapytania AI: {self.stats['ai_queries']}
• 🌐 Wyszukiwania: {self.stats['web_queries']}
• 👥 Aktywne rozmowy: {len(self.conversation_cache)}
• 📰 Subskrybenci RSS: {len(self.rss_subscribers)}

⚡ **MOŻLIWOŚCI:**
• 🚀 Czas odpowiedzi: <2s
• 🎯 Skuteczność: 99.9%
• 🌍 Internet: ✅ Na żywo
• 📰 RSS: {len(self.rss_feeds)} źródeł (co {self.rss_check_interval} min)
• 🔥 Model: {self.gemini_config.get('model', 'Nieznany')}

📅 **Online od:** {self.stats['start_time'].strftime('%d.%m.%Y %H:%M')}

💪 **Gotowy na akcję 24/7!**"""
            
            if query.message:
                message = cast(Message, query.message)
                safe_text = self.sanitize_markdown(stats_text)
                await message.reply_text(safe_text, parse_mode=ParseMode.MARKDOWN)

        elif query.data == "top_users":
            # Pobierz top 10 użytkowników
            top_users = self.get_top_users(10)
            
            if not top_users:
                if query.message:
                    await query.message.reply_text(
                        "📊 **STATYSTYKI AKTYWNOŚCI**\n\n"
                        "Brak danych o aktywności użytkowników.\n"
                        "Bot dopiero się uczy! 😊"
                    )
                return
            
            # Przygotuj tekst statystyk
            stats_text = "📊 **TOP 10 NAJAKTYWNIEJSZYCH UŻYTKOWNIKÓW**\n\n"
            
            for i, (user_id, data) in enumerate(top_users, 1):
                try:
                    # Pobierz informacje o użytkowniku
                    user_info = await context.bot.get_chat(user_id)
                    username = user_info.username or user_info.first_name or f"Użytkownik {user_id}"
                    messages = data['messages']
                    ai_queries = data['ai_queries']
                    last_activity = data['last_activity']
                    
                    # Oblicz czas od ostatniej aktywności
                    time_diff = datetime.now() - last_activity
                    if time_diff.days > 0:
                        last_seen = f"{time_diff.days}d temu"
                    elif time_diff.seconds > 3600:
                        last_seen = f"{time_diff.seconds // 3600}h temu"
                    else:
                        last_seen = f"{time_diff.seconds // 60}min temu"
                    
                    # Dodaj emoji dla top 3
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                    
                    stats_text += f"{medal} **{username}**\n"
                    stats_text += f"   💬 Wiadomości: {messages}\n"
                    stats_text += f"   🧠 AI zapytania: {ai_queries}\n"
                    stats_text += f"   ⏰ Ostatnio: {last_seen}\n\n"
                    
                except Exception as e:
                    # Fallback jeśli nie można pobrać informacji o użytkowniku
                    stats_text += f"{i}. **Użytkownik {user_id}**\n"
                    stats_text += f"   💬 Wiadomości: {data['messages']}\n"
                    stats_text += f"   🧠 AI zapytania: {data['ai_queries']}\n\n"
            
            # Dodaj podsumowanie
            total_messages = sum(data['messages'] for _, data in top_users)
            total_ai_queries = sum(data['ai_queries'] for _, data in top_users)
            
            stats_text += f"📈 **PODSUMOWANIE:**\n"
            stats_text += f"• Łącznie wiadomości: {total_messages}\n"
            stats_text += f"• Łącznie AI zapytań: {total_ai_queries}\n"
            stats_text += f"• Aktywnych użytkowników: {len(top_users)}\n\n"
            stats_text += f"🔥 **Dziękuję za aktywność!**"
            
            if query.message:
                message = cast(Message, query.message)
                safe_text = self.sanitize_markdown(stats_text)
                await message.reply_text(safe_text, parse_mode=ParseMode.MARKDOWN)
        
        elif query.data == "random_gif":
            # Losowy GIF z popularnych tagów
            if query.message:
                popular_tags = ['smiech', 'taniec', 'sukces', 'zaskoczenie', 'facepalm']
                random_tag = random.choice(popular_tags)
                
                await query.message.reply_text(
                    f"🎬 *Szukam losowego GIF-a...*",
                    parse_mode=ParseMode.MARKDOWN
                )
                
                try:
                    gif_url = await self.get_giphy_gif(random_tag, update.effective_user.id if update.effective_user else None)
                    if gif_url:
                        await query.message.reply_text(
                            f"🎬 *Losowy GIF - tag: {random_tag}*\n\n{gif_url}",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await query.message.reply_text(
                            "❌ Nie udało się pobrać GIF-a. Spróbuj ponownie!",
                            parse_mode=ParseMode.MARKDOWN
                        )
                except Exception as e:
                    await query.message.reply_text(
                        f"❌ Błąd podczas pobierania GIF-a: {str(e)}",
                        parse_mode=ParseMode.MARKDOWN
                    )
        
        elif query.data == "search_gif":
            # Menu wyszukiwania GIF-ów
            if query.message:
                keyboard = [
                    [
                        InlineKeyboardButton("😄 Śmiech", callback_data="gif_smiech"),
                        InlineKeyboardButton("😱 Zaskoczenie", callback_data="gif_zaskoczenie")
                    ],
                    [
                        InlineKeyboardButton("💃 Taniec", callback_data="gif_taniec"),
                        InlineKeyboardButton("🤦 Facepalm", callback_data="gif_facepalm")
                    ],
                    [
                        InlineKeyboardButton("🎉 Sukces", callback_data="gif_sukces"),
                        InlineKeyboardButton("😤 Frustracja", callback_data="gif_frustracja")
                    ],
                    [
                        InlineKeyboardButton("💻 Programowanie", callback_data="gif_programowanie"),
                        InlineKeyboardButton("🐛 Bug", callback_data="gif_bug")
                    ],
                    [
                        InlineKeyboardButton("🔙 Powrót", callback_data="back_to_start")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.message.reply_text(
                    "🔍 **WYBIERZ KATEGORIĘ GIF-ÓW:**\n\nKliknij przycisk poniżej! 🎬",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
        
        elif query.data.startswith("gif_"):
            # Obsługa konkretnych kategorii GIF-ów
            tag = query.data.replace("gif_", "")
            if query.message:
                await query.message.reply_text(
                    f"🎬 *Szukam GIF-a dla tagu: {tag}...*",
                    parse_mode=ParseMode.MARKDOWN
                )
                
                try:
                    gif_url = await self.get_giphy_gif(tag, update.effective_user.id if update.effective_user else None)
                    if gif_url:
                        await query.message.reply_text(
                            f"🎬 *GIF - {tag}*\n\n{gif_url}",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await query.message.reply_text(
                            "❌ Nie udało się pobrać GIF-a. Spróbuj ponownie!",
                            parse_mode=ParseMode.MARKDOWN
                        )
                except Exception as e:
                    await query.message.reply_text(
                        f"❌ Błąd podczas pobierania GIF-a: {str(e)}",
                        parse_mode=ParseMode.MARKDOWN
                    )
    
    def start_bot(self):
        """Uruchomienie bota"""
        model_name = self.gemini_config.get('model', 'Gemini AI')
        personality_style = self.config.get('personality', {}).get('style', 'standard')
        
        logger.info(f"🤖 Uruchamianie {self.bot_name} z {model_name}...")
        logger.info("✅ Bot uruchomiony pomyślnie!")
        
        print(f"🤖 {self.bot_name} - Inteligentny Asystent")
        print(f"✨ Powered by {model_name}")
        print(f"🎭 Styl: {personality_style}")
        print(f"🌡️ Temperature: {self.gemini_config.get('temperature', 0.8)}")
        print("✅ Bot uruchomiony!")
        print("💬 Napisz cokolwiek aby rozpocząć rozmowę")
        print("⏹️  Naciśnij Ctrl+C aby zatrzymać")
        print("=" * 50)
        
        try:
            # Uruchom RSS scheduler po starcie aplikacji
            if self.rss_enabled:
                async def post_init(application):
                    self.start_rss_scheduler()
                
                self.application.post_init = post_init
            
            # Uruchom bot z podstawowymi ustawieniami polling
            self.application.run_polling(
                drop_pending_updates=True,
                allowed_updates=['message', 'callback_query']
            )
        except Exception as e:
            error_msg = str(e)
            if "Conflict" in error_msg:
                print("ERROR: Wykryto konflikt instancji bota!")
                print("🔧 Rozwiązanie:")
                print("   1. Zatrzymaj wszystkie inne instancje bota")
                print("   2. Sprawdź czy nie masz uruchomionych innych procesów Python")
                print("   3. Uruchom ponownie tylko jedną instancję")
                print(f"📝 Szczegóły błędu: {e}")
            elif "NetworkError" in error_msg or "httpx.ReadError" in error_msg:
                print("ERROR: Problem z połączeniem sieciowym!")
                print("🔧 Rozwiązanie:")
                print("   1. Sprawdź połączenie internetowe")
                print("   2. Sprawdź czy firewall nie blokuje połączeń")
                print("   3. Spróbuj ponownie za kilka minut")
                print("   4. Sprawdź czy token bota jest poprawny")
                print(f"📝 Szczegóły błędu: {e}")
            else:
                print(f"❌ Błąd uruchamiania bota: {e}")
                logger.error(f"Błąd uruchamiania bota: {e}")

# === GŁÓWNA FUNKCJA ===

def main():
    """Główna funkcja uruchamiająca bota"""
    try:
        # === BEZPIECZEŃSTWO - ODCZYT ZE ZMIENNYCH ŚRODOWISKOWYCH ===
        bot_token = os.getenv('BOT_TOKEN')
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        accuweather_api_key = os.getenv('ACCUWEATHER_API_KEY')
        giphy_api_key = os.getenv('GIPHY_API_KEY')
        admin_ids_str = os.getenv('ADMIN_IDS', '')
        owner_id_str = os.getenv('OWNER_ID', '')
        
        # Sprawdzenie wymaganych zmiennych
        if not bot_token or bot_token == "TWÓJ_TOKEN_BOTA_TUTAJ":
            print("❌ ERROR: Brak tokenu bota!")
            print("   Dodaj BOT_TOKEN do pliku .env")
            print("   Skopiuj env_template.txt jako .env i uzupełnij dane")
            return
            
        if not gemini_api_key or gemini_api_key == "TWÓJ_KLUCZ_GEMINI_TUTAJ":
            print("❌ ERROR: Brak klucza API dla Gemini!")
            print("   Dodaj GEMINI_API_KEY do pliku .env")
            return
        
        # Konwersja ID administratorów
        admin_ids = []
        if admin_ids_str and admin_ids_str != "TWÓJE_ID_ADMINA":
            try:
                admin_ids = [int(x.strip()) for x in admin_ids_str.split(',')]
            except ValueError:
                print("⚠️  OSTRZEŻENIE: Nieprawidłowe ADMIN_IDS w .env")
                admin_ids = []
        
        owner_id = None
        if owner_id_str and owner_id_str != "TWÓJE_ID_WŁAŚCICIELA":
            try:
                owner_id = int(owner_id_str)
            except ValueError:
                print("⚠️  OSTRZEŻENIE: Nieprawidłowe OWNER_ID w .env")
        
        # Ładowanie konfiguracji z pliku (bez wrażliwych danych)
        try:
            with open('bot_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
        except FileNotFoundError:
            print("⚠️  OSTRZEŻENIE: Brak bot_config.json - używam domyślnej konfiguracji")
            config = {}
        
        # Nadpisanie wrażliwych danych ze zmiennych środowiskowych
        config['bot_token'] = bot_token
        config['gemini_api_key'] = gemini_api_key
        config['accuweather_api_key'] = accuweather_api_key
        config['giphy_api_key'] = giphy_api_key
        config['admin_ids'] = admin_ids
        if owner_id:
            config['owner_id'] = owner_id
            
        # Informacje o konfiguracji
        bot_style = config.get('personality', {}).get('style', 'standard')
        model_name = config.get('gemini_config', {}).get('model', 'nieznany')
        temperature = config.get('gemini_config', {}).get('temperature', 0.8)
        max_tokens = config.get('gemini_config', {}).get('max_output_tokens', 1024)
        controversial = config.get('personality', {}).get('controversial_opinions', False)
        vulgar = config.get('personality', {}).get('vulgar_language', False)
        
        print(f"🤖 Uruchamianie bota w trybie: {bot_style}")
        print(f"🧠 Model AI: {model_name}")
        print(f"🌡️ Temperature: {temperature}")
        print(f"🎯 Max tokens: {max_tokens}")
        print(f"🔞 Kontrowersyjne opinie: {'✅' if controversial else '❌'}")
        print(f"🤬 Wulgarny język: {'✅' if vulgar else '❌'}")
        
        if config.get('_security_warning'):
            print(f"\n⚠️  OSTRZEŻENIE: {config['_security_warning']}")
            print()
        
        # Utworzenie i uruchomienie bota
        bot = SmartAIBot(config)
        bot.start_bot()
        
    except KeyboardInterrupt:
        print("\n🛑 Zatrzymywanie bota...")
        print("✅ Bot zatrzymany!")
    except Exception as e:
        logger.error(f"Błąd: {e}")
        print(f"ERROR: {e}")

if __name__ == '__main__':
    main()