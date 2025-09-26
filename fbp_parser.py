#!/usr/bin/env python3
"""
Парсер для сайта fbp.ru - извлекает данные из competition-profile виджетов
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from typing import List, Dict, Optional

class FBPParser:
    def __init__(self):
        self.base_url = "https://www.fbp.ru/turniryi/letnyaya-liga.html"
        self.target_teams = ["Pull Up", "PULL UP", "Атлант", "АТЛАНТ"]
        
    async def fetch_page(self) -> str:
        """Загружает страницу fbp.ru"""
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    raise Exception(f"Ошибка загрузки страницы: {response.status}")
    
    def extract_competition_widgets(self, html_content: str) -> List[Dict]:
        """Извлекает данные о competition-profile виджетах"""
        soup = BeautifulSoup(html_content, 'html.parser')
        widgets = []
        
        # Ищем все competition-profile элементы
        competition_elements = soup.find_all('competition-profile')
        
        for element in competition_elements:
            api_url = element.get('api-url')
            competition_id = element.get('competition-id')
            
            # Если API URL asb.infobasket.su, заменяем на reg.infobasket.su
            if api_url == 'https://asb.infobasket.su':
                api_url = 'https://reg.infobasket.su'
            
            widget_data = {
                'api_url': api_url,
                'competition_id': competition_id,
                'competition_tag': element.get('competition-tag'),
                'lang': element.get('lang'),
                'container_id': element.parent.get('id') if element.parent else None
            }
            widgets.append(widget_data)
        
        return widgets
    
    async def fetch_competition_data(self, api_url: str, competition_id: str) -> Dict:
        """Загружает данные о соревновании через API"""
        url = f"{api_url}/Widget/CompIssue/{competition_id}?format=json"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        print(f"❌ Ошибка API для {competition_id}: {response.status}")
                        return {}
            except Exception as e:
                print(f"❌ Исключение при загрузке {competition_id}: {e}")
                return {}
    
    async def fetch_sub_competitions(self, api_url: str, competition_id: str) -> List[Dict]:
        """Загружает данные о под-соревнованиях"""
        main_data = await self.fetch_competition_data(api_url, competition_id)
        
        if not main_data or 'Comps' not in main_data:
            return []
        
        sub_competitions = []
        comps = main_data['Comps']
        
        print(f"🔍 Найдено под-соревнований: {len(comps)}")
        
        async with aiohttp.ClientSession() as session:
            for comp in comps:
                comp_id = comp.get('CompID')
                comp_name = comp.get('CompShortNameRu', 'Без названия')
                
                if comp_id:
                    print(f"  🔍 Проверяем: {comp_name} (ID: {comp_id})")
                    
                    # Загружаем данные под-соревнования
                    sub_url = f"{api_url}/Widget/CompIssue/{comp_id}?format=json"
                    try:
                        async with session.get(sub_url) as response:
                            if response.status == 200:
                                sub_data = await response.json()
                                if sub_data:
                                    sub_competitions.append({
                                        'id': comp_id,
                                        'name': comp_name,
                                        'data': sub_data
                                    })
                                    print(f"    ✅ Данные загружены")
                                else:
                                    print(f"    ❌ Пустые данные")
                            else:
                                print(f"    ❌ Ошибка: {response.status}")
                    except Exception as e:
                        print(f"    ❌ Исключение: {e}")
        
        return sub_competitions
    
    def find_games_in_data(self, data: Dict, competition_id: str) -> List[Dict]:
        """Ищет игры в данных API"""
        games = []
        
        def search_games(obj, path=''):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f'{path}.{key}' if path else key
                    
                    # Ищем игры по ключевым словам
                    if key.lower() in ['games', 'game', 'matches', 'match'] and isinstance(value, list):
                        for game in value:
                            if isinstance(game, dict):
                                games.append({
                                    'competition_id': competition_id,
                                    'path': current_path,
                                    'data': game
                                })
                    
                    # Ищем любые массивы, которые могут содержать игры
                    if isinstance(value, list) and len(value) > 0:
                        # Проверяем, содержит ли массив объекты с игровыми данными
                        for item in value:
                            if isinstance(item, dict):
                                # Ищем признаки игры
                                game_indicators = ['team', 'teams', 'home', 'away', 'opponent', 'date', 'time', 'score', 'result']
                                if any(indicator in str(item).lower() for indicator in game_indicators):
                                    games.append({
                                        'competition_id': competition_id,
                                        'path': current_path,
                                        'data': item
                                    })
                    
                    # Рекурсивно ищем в подобъектах
                    if isinstance(value, (dict, list)):
                        search_games(value, current_path)
                        
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    current_path = f'{path}[{i}]'
                    if isinstance(item, (dict, list)):
                        search_games(item, current_path)
        
        search_games(data)
        return games
    
    def filter_games_by_teams(self, games: List[Dict]) -> List[Dict]:
        """Фильтрует игры по нашим командам"""
        filtered_games = []
        
        for game in games:
            game_data = game.get('data', {})
            
            # Ищем упоминания наших команд в данных игры
            def contains_our_teams(obj):
                if isinstance(obj, str):
                    return any(team.lower() in obj.lower() for team in self.target_teams)
                elif isinstance(obj, dict):
                    return any(contains_our_teams(value) for value in obj.values())
                elif isinstance(obj, list):
                    return any(contains_our_teams(item) for item in obj)
                return False
            
            if contains_our_teams(game_data):
                filtered_games.append(game)
        
        return filtered_games
    
    def normalize_game_data(self, game: Dict) -> Dict:
        """Нормализует данные игры в стандартный формат"""
        game_data = game.get('data', {})
        
        # Извлекаем основную информацию
        normalized = {
            'competition_id': game.get('competition_id'),
            'raw_data': game_data,
            'teams': [],
            'date': None,
            'time': None,
            'venue': None,
            'status': 'unknown'
        }
        
        # Ищем команды, дату, время в данных
        def extract_info(obj, path=''):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f'{path}.{key}' if path else key
                    
                    # Ищем команды
                    if key.lower() in ['team', 'teams', 'home', 'away', 'opponent']:
                        if isinstance(value, str):
                            normalized['teams'].append(value)
                        elif isinstance(value, dict) and 'name' in value:
                            normalized['teams'].append(value['name'])
                    
                    # Ищем дату
                    if key.lower() in ['date', 'datetime', 'start_date']:
                        if isinstance(value, str):
                            normalized['date'] = value
                    
                    # Ищем время
                    if key.lower() in ['time', 'start_time']:
                        if isinstance(value, str):
                            normalized['time'] = value
                    
                    # Ищем место
                    if key.lower() in ['venue', 'place', 'location', 'arena']:
                        if isinstance(value, str):
                            normalized['venue'] = value
                    
                    # Рекурсивно ищем в подобъектах
                    if isinstance(value, (dict, list)):
                        extract_info(value, current_path)
                        
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    current_path = f'{path}[{i}]'
                    if isinstance(item, (dict, list)):
                        extract_info(item, current_path)
        
        extract_info(game_data)
        return normalized
    
    async def get_schedule(self) -> List[Dict]:
        """Получает расписание игр с fbp.ru"""
        print("🔍 Загрузка страницы fbp.ru...")
        html_content = await self.fetch_page()
        
        print("🔍 Извлечение виджетов...")
        widgets = self.extract_competition_widgets(html_content)
        print(f"📊 Найдено виджетов: {len(widgets)}")
        
        all_games = []
        
        for widget in widgets:
            print(f"\\n🔍 Обработка виджета: {widget['competition_id']} ({widget['competition_tag']})")
            
            # Загружаем под-соревнования
            sub_competitions = await self.fetch_sub_competitions(
                widget['api_url'], 
                widget['competition_id']
            )
            
            if sub_competitions:
                print(f"✅ Найдено под-соревнований: {len(sub_competitions)}")
                
                for sub_comp in sub_competitions:
                    print(f"\\n  🔍 Анализ: {sub_comp['name']} (ID: {sub_comp['id']})")
                    
                    # Сохраняем данные для анализа
                    filename = f"fbp_sub_{sub_comp['id']}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(sub_comp['data'], f, ensure_ascii=False, indent=2)
                    print(f"  💾 Данные сохранены в {filename}")
                    
                    # Показываем структуру данных
                    print(f"  📊 Ключи в данных: {list(sub_comp['data'].keys())}")
                    
                    # Ищем игры в данных
                    games = self.find_games_in_data(sub_comp['data'], sub_comp['id'])
                    print(f"  🎮 Найдено игр: {len(games)}")
                    
                    # Фильтруем по нашим командам
                    filtered_games = self.filter_games_by_teams(games)
                    print(f"  🏀 Игр с нашими командами: {len(filtered_games)}")
                    
                    # Нормализуем данные
                    for game in filtered_games:
                        normalized = self.normalize_game_data(game)
                        all_games.append(normalized)
            else:
                print(f"❌ Нет под-соревнований для {widget['competition_id']}")
        
        print(f"\\n📊 Всего найдено игр: {len(all_games)}")
        return all_games

async def main():
    """Тестирование парсера"""
    parser = FBPParser()
    
    try:
        games = await parser.get_schedule()
        
        if games:
            print("\\n🎮 НАЙДЕННЫЕ ИГРЫ:")
            for i, game in enumerate(games, 1):
                print(f"\\n--- Игра {i} ---")
                print(f"Соревнование: {game['competition_id']}")
                print(f"Команды: {game['teams']}")
                print(f"Дата: {game['date']}")
                print(f"Время: {game['time']}")
                print(f"Место: {game['venue']}")
                print(f"Статус: {game['status']}")
        else:
            print("\\n❌ Игры не найдены")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
