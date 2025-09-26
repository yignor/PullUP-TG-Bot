#!/usr/bin/env python3
"""
Скрипт для проверки наличия API или динамической загрузки данных на fbp.ru
"""

import asyncio
import aiohttp
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class FBPApiChecker:
    """Проверяет наличие API или динамической загрузки на fbp.ru"""
    
    def __init__(self):
        self.base_url = "https://www.fbp.ru"
        self.target_url = "https://www.fbp.ru/turniryi/letnyaya-liga.html"
        self.api_endpoints = []
        self.js_files = []
        self.ajax_calls = []
    
    async def check_for_api(self):
        """Проверяет наличие API endpoints на сайте"""
        print("🔍 Проверка наличия API на fbp.ru...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Загружаем основную страницу
                async with session.get(self.target_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # 1. Ищем скрипты с API вызовами
                        await self._check_scripts(session, soup)
                        
                        # 2. Ищем JSON данные в HTML
                        await self._check_json_data(content)
                        
                        # 3. Ищем AJAX запросы
                        await self._check_ajax_calls(content)
                        
                        # 4. Проверяем Network tab (имитируем)
                        await self._check_network_requests(session)
                        
        except Exception as e:
            print(f"❌ Ошибка проверки API: {e}")
    
    async def _check_scripts(self, session, soup):
        """Проверяет JavaScript файлы на наличие API вызовов"""
        print("📜 Проверка JavaScript файлов...")
        
        scripts = soup.find_all('script', src=True)
        for script in scripts:
            script_url = urljoin(self.base_url, script['src'])
            self.js_files.append(script_url)
            
            try:
                async with session.get(script_url) as response:
                    if response.status == 200:
                        js_content = await response.text()
                        
                        # Ищем API endpoints в JS
                        api_patterns = [
                            r'fetch\(["\']([^"\']+)["\']',
                            r'axios\.get\(["\']([^"\']+)["\']',
                            r'\.get\(["\']([^"\']+)["\']',
                            r'ajax\(["\']([^"\']+)["\']',
                            r'api["\']?\s*:\s*["\']([^"\']+)["\']',
                            r'/api/[^"\']+',
                            r'\.json[^"\']*',
                        ]
                        
                        for pattern in api_patterns:
                            matches = re.findall(pattern, js_content, re.IGNORECASE)
                            for match in matches:
                                if match.startswith('/') or 'api' in match.lower():
                                    self.api_endpoints.append(match)
                                    print(f"   🔗 Найден API endpoint: {match}")
            
            except Exception as e:
                print(f"   ⚠️ Ошибка загрузки скрипта {script_url}: {e}")
    
    async def _check_json_data(self, content):
        """Ищет JSON данные в HTML"""
        print("📄 Поиск JSON данных в HTML...")
        
        # Ищем JSON в script тегах
        json_pattern = r'<script[^>]*>(.*?)</script>'
        scripts = re.findall(json_pattern, content, re.DOTALL)
        
        for script in scripts:
            if 'json' in script.lower() or '{' in script:
                try:
                    # Пытаемся найти JSON объекты
                    json_matches = re.findall(r'\{[^{}]*"[^"]*"[^{}]*\}', script)
                    for json_str in json_matches:
                        try:
                            data = json.loads(json_str)
                            if isinstance(data, dict) and len(data) > 0:
                                print(f"   📊 Найден JSON: {json_str[:100]}...")
                        except:
                            pass
                except:
                    pass
    
    async def _check_ajax_calls(self, content):
        """Ищет AJAX вызовы в коде"""
        print("🔄 Поиск AJAX вызовов...")
        
        ajax_patterns = [
            r'\.ajax\([^)]+\)',
            r'fetch\([^)]+\)',
            r'XMLHttpRequest',
            r'axios\.[a-z]+\([^)]+\)',
        ]
        
        for pattern in ajax_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                self.ajax_calls.append(match)
                print(f"   🔄 Найден AJAX: {match[:50]}...")
    
    async def _check_network_requests(self, session):
        """Проверяет возможные API endpoints"""
        print("🌐 Проверка возможных API endpoints...")
        
        # Список возможных API endpoints
        possible_endpoints = [
            '/api/games',
            '/api/matches',
            '/api/results',
            '/api/teams',
            '/api/schedule',
            '/api/letnyaya-liga',
            '/api/tournaments',
            '/data/games.json',
            '/data/matches.json',
            '/json/games',
            '/json/matches',
        ]
        
        for endpoint in possible_endpoints:
            url = urljoin(self.base_url, endpoint)
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        if 'json' in content_type:
                            print(f"   ✅ Найден JSON API: {url}")
                            try:
                                data = await response.json()
                                print(f"      📊 Данные: {str(data)[:100]}...")
                            except:
                                print(f"      📄 Содержимое: {await response.text()[:100]}...")
                        else:
                            print(f"   📄 Найден endpoint: {url} ({content_type})")
            except:
                pass
    
    def print_results(self):
        """Выводит результаты проверки"""
        print("\n" + "="*50)
        print("📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ FBP.RU")
        print("="*50)
        
        print(f"\n🔗 Найдено API endpoints: {len(self.api_endpoints)}")
        for endpoint in self.api_endpoints:
            print(f"   - {endpoint}")
        
        print(f"\n📜 JavaScript файлов: {len(self.js_files)}")
        for js in self.js_files[:5]:  # Показываем первые 5
            print(f"   - {js}")
        
        print(f"\n🔄 AJAX вызовов: {len(self.ajax_calls)}")
        for ajax in self.ajax_calls[:5]:  # Показываем первые 5
            print(f"   - {ajax}")
        
        print("\n💡 РЕКОМЕНДАЦИИ:")
        if self.api_endpoints:
            print("   ✅ Найдены API endpoints - можно использовать их")
        else:
            print("   ❌ API endpoints не найдены")
            print("   📝 Рекомендуется использовать парсинг HTML")
            print("   🔄 Можно попробовать Selenium для динамического контента")

async def main():
    checker = FBPApiChecker()
    await checker.check_for_api()
    checker.print_results()

if __name__ == "__main__":
    asyncio.run(main())
