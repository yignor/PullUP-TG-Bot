#!/usr/bin/env python3
"""
Детальная проверка fbp.ru на наличие реальных API для баскетбольных данных
"""

import asyncio
import aiohttp
import json
import re
from bs4 import BeautifulSoup

class DetailedFBPChecker:
    """Детальная проверка API на fbp.ru"""
    
    def __init__(self):
        self.base_url = "https://www.fbp.ru"
        self.target_url = "https://www.fbp.ru/turniryi/letnyaya-liga.html"
        self.found_apis = []
    
    async def check_specific_apis(self):
        """Проверяет специфические API для баскетбольных данных"""
        print("🏀 Проверка специфических API для баскетбола...")
        
        # Список возможных API endpoints для баскетбола
        basketball_apis = [
            '/api/letnyaya-liga',
            '/api/summer-league',
            '/api/tournaments',
            '/api/games',
            '/api/matches',
            '/api/results',
            '/api/schedule',
            '/api/teams',
            '/api/standings',
            '/api/statistics',
            '/data/letnyaya-liga.json',
            '/data/summer-league.json',
            '/data/tournaments.json',
            '/data/games.json',
            '/data/matches.json',
            '/data/results.json',
            '/data/schedule.json',
            '/json/letnyaya-liga',
            '/json/summer-league',
            '/json/tournaments',
            '/json/games',
            '/json/matches',
            '/json/results',
            '/json/schedule',
            '/v1/letnyaya-liga',
            '/v1/summer-league',
            '/v1/tournaments',
            '/v1/games',
            '/v1/matches',
            '/v1/results',
            '/v1/schedule',
        ]
        
        async with aiohttp.ClientSession() as session:
            for api in basketball_apis:
                url = f"{self.base_url}{api}"
                try:
                    async with session.get(url, timeout=5) as response:
                        if response.status == 200:
                            content_type = response.headers.get('content-type', '')
                            content = await response.text()
                            
                            # Проверяем, что это действительно API
                            if self._is_valid_api_response(content, content_type):
                                self.found_apis.append({
                                    'url': url,
                                    'status': response.status,
                                    'content_type': content_type,
                                    'content': content[:200] + '...' if len(content) > 200 else content
                                })
                                print(f"   ✅ Найден API: {url}")
                                print(f"      📊 Тип: {content_type}")
                                print(f"      📄 Данные: {content[:100]}...")
                
                except Exception as e:
                    pass  # Игнорируем ошибки для несуществующих endpoints
    
    def _is_valid_api_response(self, content, content_type):
        """Проверяет, является ли ответ валидным API"""
        # Проверяем JSON
        if 'json' in content_type:
            try:
                data = json.loads(content)
                return isinstance(data, (dict, list)) and len(str(data)) > 10
            except:
                pass
        
        # Проверяем XML
        if 'xml' in content_type:
            return '<' in content and '>' in content
        
        # Проверяем на баскетбольные данные
        basketball_keywords = [
            'game', 'match', 'team', 'score', 'result',
            'игра', 'матч', 'команда', 'счет', 'результат',
            'letnyaya', 'liga', 'summer', 'league'
        ]
        
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in basketball_keywords)
    
    async def check_dynamic_content(self):
        """Проверяет динамическую загрузку контента"""
        print("🔄 Проверка динамической загрузки контента...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.target_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Ищем элементы, которые могут загружаться динамически
                        dynamic_elements = soup.find_all(['div', 'table', 'ul'], {
                            'class': re.compile(r'(ajax|dynamic|load|content|data)', re.I)
                        })
                        
                        if dynamic_elements:
                            print(f"   🔄 Найдено {len(dynamic_elements)} элементов с динамической загрузкой")
                            for element in dynamic_elements[:3]:  # Показываем первые 3
                                print(f"      - {element.name}: {element.get('class', [])}")
                        
                        # Ищем data-атрибуты
                        data_attrs = soup.find_all(attrs={'data-url': True})
                        if data_attrs:
                            print(f"   📊 Найдено {len(data_attrs)} элементов с data-url")
                            for attr in data_attrs[:3]:
                                print(f"      - {attr.name}: {attr.get('data-url')}")
        
        except Exception as e:
            print(f"   ❌ Ошибка проверки динамического контента: {e}")
    
    async def check_network_requests(self):
        """Проверяет возможные сетевые запросы"""
        print("🌐 Проверка сетевых запросов...")
        
        # Проверяем возможные endpoints для данных
        possible_endpoints = [
            '/api/tournaments/letnyaya-liga',
            '/api/tournaments/summer-league',
            '/api/competitions/letnyaya-liga',
            '/api/competitions/summer-league',
            '/api/leagues/letnyaya-liga',
            '/api/leagues/summer-league',
            '/api/events/letnyaya-liga',
            '/api/events/summer-league',
            '/api/sports/basketball/letnyaya-liga',
            '/api/sports/basketball/summer-league',
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint in possible_endpoints:
                url = f"{self.base_url}{endpoint}"
                try:
                    async with session.get(url, timeout=3) as response:
                        if response.status == 200:
                            content_type = response.headers.get('content-type', '')
                            if 'json' in content_type or 'xml' in content_type:
                                print(f"   ✅ Найден endpoint: {url}")
                                print(f"      📊 Тип: {content_type}")
                except:
                    pass
    
    def print_results(self):
        """Выводит результаты проверки"""
        print("\n" + "="*60)
        print("🏀 РЕЗУЛЬТАТЫ ДЕТАЛЬНОЙ ПРОВЕРКИ FBP.RU")
        print("="*60)
        
        if self.found_apis:
            print(f"\n✅ Найдено {len(self.found_apis)} API endpoints:")
            for api in self.found_apis:
                print(f"   🔗 {api['url']}")
                print(f"      📊 Статус: {api['status']}")
                print(f"      📄 Тип: {api['content_type']}")
                print(f"      📝 Данные: {api['content']}")
                print()
        else:
            print("\n❌ API endpoints не найдены")
        
        print("\n💡 РЕКОМЕНДАЦИИ:")
        if self.found_apis:
            print("   ✅ Используйте найденные API endpoints")
            print("   📊 Они предоставляют структурированные данные")
            print("   🚀 Это будет намного проще, чем парсинг HTML")
        else:
            print("   ❌ API не найдены - используйте парсинг HTML")
            print("   📝 Рекомендуется остаться с letobasket.ru")
            print("   🔄 Можно добавить fbp.ru как резервный источник")

async def main():
    checker = DetailedFBPChecker()
    await checker.check_specific_apis()
    await checker.check_dynamic_content()
    await checker.check_network_requests()
    checker.print_results()

if __name__ == "__main__":
    asyncio.run(main())
