#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render Manager - Moduł do zarządzania usługami Render przez bota
"""

import os
import json
import aiohttp
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RenderManager:
    """Klasa do zarządzania usługami Render"""
    
    def __init__(self, api_key: str = None):
        """Inicjalizacja Render Manager"""
        self.api_key = api_key or os.getenv('RENDER_API_KEY')
        self.base_url = "https://api.render.com/v1"
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
    async def check_api_key(self) -> bool:
        """Sprawdź czy API key jest poprawny"""
        if not self.api_key:
            return False
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/services",
                    headers=self.headers
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Błąd sprawdzania API key: {e}")
            return False
    
    async def get_services(self) -> List[Dict]:
        """Pobierz listę wszystkich usług"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/services",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        logger.error(f"Błąd pobierania usług: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Błąd pobierania usług: {e}")
            return []
    
    async def get_service_by_name(self, service_name: str) -> Optional[Dict]:
        """Znajdź usługę po nazwie"""
        services = await self.get_services()
        for service in services:
            if service.get('service', {}).get('name') == service_name:
                return service
        return None
    
    async def get_service_status(self, service_id: str) -> str:
        """Pobierz status usługi"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/services/{service_id}",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('service', {}).get('status', 'unknown')
                    else:
                        return 'error'
        except Exception as e:
            logger.error(f"Błąd pobierania statusu: {e}")
            return 'error'
    
    async def restart_service(self, service_id: str) -> bool:
        """Restartuj usługę"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/services/{service_id}/deploys",
                    headers=self.headers,
                    json={}
                ) as response:
                    return response.status == 201
        except Exception as e:
            logger.error(f"Błąd restartowania usługi: {e}")
            return False
    
    async def get_service_logs(self, service_id: str, limit: int = 100) -> List[str]:
        """Pobierz logi usługi"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/services/{service_id}/logs",
                    headers=self.headers,
                    params={'limit': limit}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('logs', [])
                    else:
                        return []
        except Exception as e:
            logger.error(f"Błąd pobierania logów: {e}")
            return []
    
    async def create_service(self, service_config: Dict) -> Optional[str]:
        """Utwórz nową usługę"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/services",
                    headers=self.headers,
                    json=service_config
                ) as response:
                    if response.status == 201:
                        data = await response.json()
                        return data.get('service', {}).get('id')
                    else:
                        logger.error(f"Błąd tworzenia usługi: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Błąd tworzenia usługi: {e}")
            return None
    
    async def delete_service(self, service_id: str) -> bool:
        """Usuń usługę"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    f"{self.base_url}/services/{service_id}",
                    headers=self.headers
                ) as response:
                    return response.status == 204
        except Exception as e:
            logger.error(f"Błąd usuwania usługi: {e}")
            return False
    
    def format_service_info(self, service: Dict) -> str:
        """Sformatuj informacje o usłudze"""
        service_data = service.get('service', {})
        name = service_data.get('name', 'Unknown')
        status = service_data.get('status', 'unknown')
        created_at = service_data.get('createdAt', '')
        updated_at = service_data.get('updatedAt', '')
        
        # Konwertuj daty
        if created_at:
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
        if updated_at:
            updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
        
        status_emoji = {
            'live': '🟢',
            'suspended': '🔴',
            'building': '🟡',
            'deploying': '🟡',
            'error': '🔴',
            'unknown': '⚪'
        }.get(status, '⚪')
        
        return f"""
🤖 **Usługa: {name}**
{status_emoji} **Status**: {status.upper()}
📅 **Utworzona**: {created_at}
🔄 **Ostatnia aktualizacja**: {updated_at}
"""
    
    async def get_bot_services(self) -> List[Dict]:
        """Pobierz usługi związane z botami"""
        services = await self.get_services()
        bot_services = []
        
        bot_keywords = ['bot', 'silver', 'grok', 'kumpel', 'telegram']
        
        for service in services:
            service_name = service.get('service', {}).get('name', '').lower()
            if any(keyword in service_name for keyword in bot_keywords):
                bot_services.append(service)
        
        return bot_services

# Funkcje pomocnicze
async def check_render_health(api_key: str) -> Dict:
    """Sprawdź zdrowie usług Render"""
    manager = RenderManager(api_key)
    
    if not await manager.check_api_key():
        return {
            'status': 'error',
            'message': 'Nieprawidłowy API key Render'
        }
    
    services = await manager.get_bot_services()
    
    return {
        'status': 'ok',
        'services_count': len(services),
        'services': services
    }

async def get_service_summary(api_key: str) -> str:
    """Pobierz podsumowanie usług"""
    manager = RenderManager(api_key)
    
    if not await manager.check_api_key():
        return "❌ **Błąd**: Nieprawidłowy API key Render"
    
    services = await manager.get_bot_services()
    
    if not services:
        return "📭 **Brak usług botów** na Render"
    
    summary = f"🤖 **Usługi botów na Render** ({len(services)}):\n\n"
    
    for service in services:
        summary += manager.format_service_info(service) + "\n"
    
    return summary 