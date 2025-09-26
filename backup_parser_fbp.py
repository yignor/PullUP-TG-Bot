#!/usr/bin/env python3
"""
Резервный парсер для fbp.ru (Федерация Баскетбола Санкт-Петербурга)
Используется как дополнительный источник данных о играх
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from datetime import datetime
from typing import List, Dict, Optional

class FBPBackupParser:
    """Парсер официального сайта Федерации Баскетбола СПб"""
    
    def __init__(self):
        self.base_url = "https://www.fbp.ru/turniryi/letnyaya-liga.html"
    
    async def fetch_games_data(self) -> List[Dict]:
        """Получает данные об играх с fbp.ru"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Ищем таблицы с результатами
                        games = []
                        
                        # Ищем все таблицы на странице
                        tables = soup.find_all('table')
                        
                        for table in tables:
                            rows = table.find_all('tr')
                            for row in rows:
                                cells = row.find_all(['td', 'th'])
                                if len(cells) >= 3:
                                    # Пытаемся извлечь информацию об игре
                                    game_data = self._parse_table_row(cells)
                                    if game_data:
                                        games.append(game_data)
                        
                        print(f"🔍 FBP: Найдено {len(games)} игр")
                        return games
                    else:
                        print(f"❌ FBP: Ошибка загрузки страницы: {response.status}")
                        return []
                        
        except Exception as e:
            print(f"❌ FBP: Ошибка парсинга: {e}")
            return []
    
    def _parse_table_row(self, cells) -> Optional[Dict]:
        """Парсит строку таблицы в данные игры"""
        try:
            # Ищем паттерны с датами и командами
            text_content = ' '.join([cell.get_text(strip=True) for cell in cells])
            
            # Паттерн для поиска дат
            date_pattern = r'(\d{1,2}\.\d{1,2}\.\d{4})'
            date_match = re.search(date_pattern, text_content)
            
            if date_match:
                date = date_match.group(1)
                
                # Ищем команды Pull Up
                if any(team in text_content for team in ['Pull Up', 'PullUP', 'Pull-Up']):
                    return {
                        'date': date,
                        'source': 'fbp.ru',
                        'raw_text': text_content,
                        'parsed': True
                    }
            
            return None
            
        except Exception as e:
            print(f"⚠️ FBP: Ошибка парсинга строки: {e}")
            return None
    
    async def get_backup_games(self) -> List[Dict]:
        """Получает резервные данные об играх"""
        games = await self.fetch_games_data()
        
        # Фильтруем только игры с нашими командами
        target_games = []
        for game in games:
            if game.get('parsed'):
                target_games.append(game)
        
        return target_games

# Пример использования
async def main():
    parser = FBPBackupParser()
    games = await parser.get_backup_games()
    
    print(f"📊 Резервный парсер FBP нашел {len(games)} игр:")
    for game in games:
        print(f"   {game['date']}: {game['raw_text'][:50]}...")

if __name__ == "__main__":
    asyncio.run(main())
