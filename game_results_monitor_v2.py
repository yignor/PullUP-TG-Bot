#!/usr/bin/env python3
"""
Модуль для автоматического мониторинга результатов игр (версия 2)
Прямое сканирование табло без зависимости от GameSystemManager
"""

import asyncio
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List
import aiohttp
from bs4 import BeautifulSoup
import re

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

# Импортируем централизованные функции
from datetime_utils import get_moscow_time, is_today

# Константы
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
GAME_MONITOR_HISTORY_FILE = 'game_monitor_history.json'
DAILY_CHECK_FILE = 'daily_games_check.json'

def load_game_monitor_history() -> Dict:
    """Загружает историю мониторинга игр"""
    try:
        if os.path.exists(GAME_MONITOR_HISTORY_FILE):
            with open(GAME_MONITOR_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Ошибка загрузки истории мониторинга: {e}")
    return {}

def save_game_monitor_history(history: Dict):
    """Сохраняет историю мониторинга игр"""
    try:
        with open(GAME_MONITOR_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Ошибка сохранения истории мониторинга: {e}")

def load_daily_check() -> Dict:
    """Загружает информацию о ежедневной проверке"""
    try:
        if os.path.exists(DAILY_CHECK_FILE):
            with open(DAILY_CHECK_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Ошибка загрузки ежедневной проверки: {e}")
    return {}

def save_daily_check(check_info: Dict):
    """Сохраняет информацию о ежедневной проверке"""
    try:
        with open(DAILY_CHECK_FILE, 'w', encoding='utf-8') as f:
            json.dump(check_info, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Ошибка сохранения ежедневной проверки: {e}")

def create_game_monitor_key(game_info: Dict) -> str:
    """Создает уникальный ключ для мониторинга игры"""
    return f"{game_info['date']}_{game_info['time']}_{game_info['team1']}_{game_info['team2']}"

class GameResultsMonitorV2:
    """Класс для мониторинга результатов игр (версия 2)"""
    
    def __init__(self):
        self.bot = None
        self.monitor_history = load_game_monitor_history()
        self.daily_check = load_daily_check()
        
        if BOT_TOKEN:
            from telegram import Bot
            self.bot = Bot(token=BOT_TOKEN)
    
    def should_continue_today(self) -> bool:
        """Проверяет, нужно ли продолжать проверки сегодня"""
        today = get_moscow_time().strftime('%Y-%m-%d')
        
        if today in self.daily_check:
            check_info = self.daily_check[today]
            if check_info.get('no_games_found', False):
                print(f"📅 Сегодня ({today}) уже проверено - игр не найдено, останавливаемся")
                return False
        
        return True
    
    def mark_no_games_today(self):
        """Отмечает, что сегодня игр не найдено"""
        today = get_moscow_time().strftime('%Y-%m-%d')
        self.daily_check[today] = {
            'no_games_found': True,
            'check_time': get_moscow_time().isoformat()
        }
        save_daily_check(self.daily_check)
        print(f"📅 Отмечено: сегодня ({today}) игр не найдено")
    
    def find_target_teams_in_text(self, text: str) -> List[str]:
        """Находит целевые команды в тексте"""
        found_teams = []
        # Расширенный список команд для поиска (в порядке приоритета)
        search_teams = [
            'Pull Up-Фарм',  # Сначала ищем более специфичные варианты
            'Pull Up Фарм',  # Без дефиса
            'Pull Up',       # Обычный Pull Up
            'PullUP',        # Без пробела
            'PULL UP ФАРМ'   # Верхний регистр
        ]
        
        for team in search_teams:
            if team.upper() in text.upper():
                found_teams.append(team)
                print(f"   ✅ Найдена команда: {team}")
        
        return found_teams
    
    def generate_game_link(self, team1: str, team2: str) -> str:
        """Генерирует ссылку на игру"""
        try:
            # Формируем ссылку на игру
            # Используем базовый URL и добавляем параметры команд
            base_url = "http://letobasket.ru/game.html"
            
            # Определяем, какая из команд наша
            our_team = None
            opponent = None
            
            target_teams = ['Pull Up-Фарм', 'Pull Up Фарм', 'Pull Up', 'PullUP', 'PULL UP ФАРМ']
            
            if any(team.upper() in team1.upper() for team in target_teams):
                our_team = team1
                opponent = team2
            elif any(team.upper() in team2.upper() for team in target_teams):
                our_team = team2
                opponent = team1
            else:
                return ""
            
            # Формируем ссылку
            game_link = f"{base_url}?team1={our_team}&team2={opponent}"
            return game_link
            
        except Exception as e:
            print(f"   ⚠️ Ошибка генерации ссылки: {e}")
            return ""
    
    def extract_scoreboard_section(self, soup) -> tuple:
        """Извлекает раздел 'ТАБЛО ИГР' и ссылки на игры"""
        try:
            # Ищем раздел "ТАБЛО ИГР"
            scoreboard_text = ""
            game_links = []
            
            # Ищем по тексту "ТАБЛО ИГР"
            for element in soup.find_all(text=True):
                if "ТАБЛО ИГР" in element:
                    print(f"   🎯 Найден текст 'ТАБЛО ИГР'")
                    
                    # Получаем весь текст страницы
                    full_text = soup.get_text()
                    
                    # Ищем позицию "ТАБЛО ИГР"
                    start_pos = full_text.find("ТАБЛО ИГР")
                    if start_pos != -1:
                        # Ищем конец раздела (начало "ПОСЛЕДНИЕ РЕЗУЛЬТАТЫ")
                        end_pos = full_text.find("ПОСЛЕДНИЕ РЕЗУЛЬТАТЫ", start_pos)
                        
                        if end_pos != -1:
                            # Извлекаем текст между "ТАБЛО ИГР" и "ПОСЛЕДНИЕ РЕЗУЛЬТАТЫ"
                            scoreboard_text = full_text[start_pos:end_pos]
                        else:
                            # Если "ПОСЛЕДНИЕ РЕЗУЛЬТАТЫ" не найдено, берем до конца
                            scoreboard_text = full_text[start_pos:]
                        
                        # Извлекаем ссылки "СТРАНИЦА ИГРЫ" из всего HTML (как в Game System Manager)
                        game_links = self.extract_game_links(soup)
                        
                        print(f"   📋 Извлечен раздел табло (длина: {len(scoreboard_text)} символов)")
                        print(f"   🔗 Найдено ссылок на игры: {len(game_links)}")
                        
                        # Дополнительно ищем игры в HTML структуре
                        html_games = self.extract_games_from_html(soup)
                        if html_games:
                            print(f"   🎮 Найдено игр в HTML: {len(html_games)}")
                            return scoreboard_text, game_links, html_games
                        
                        return scoreboard_text, game_links, []
            
            print(f"   ❌ Раздел 'ТАБЛО ИГР' не найден")
            return "", [], []
                
        except Exception as e:
            print(f"   ❌ Ошибка извлечения табло: {e}")
            return "", [], []
    
    def extract_game_links(self, soup) -> list:
        """Извлекает ссылки 'СТРАНИЦА ИГРЫ' из раздела табло (адаптировано из Game System Manager)"""
        try:
            game_links = []
            
            # Ищем все ссылки с текстом "СТРАНИЦА ИГРЫ" (как в Game System Manager)
            for link in soup.find_all('a', href=True):
                if "СТРАНИЦА ИГРЫ" in link.get_text():
                    href = link.get('href')
                    if href:
                        # Формируем полную ссылку
                        if href.startswith('game.html'):
                            full_link = f"http://letobasket.ru/{href}"
                        elif href.startswith('/'):
                            full_link = f"http://letobasket.ru{href}"
                        else:
                            full_link = href
                        game_links.append(full_link)
                        print(f"   🔗 Найдена ссылка 'СТРАНИЦА ИГРЫ': {full_link}")
            
            print(f"   📊 Всего найдено ссылок 'СТРАНИЦА ИГРЫ': {len(game_links)}")
            return game_links
                
        except Exception as e:
            print(f"   ❌ Ошибка извлечения ссылок: {e}")
            return []
    
    def extract_recent_results(self, soup) -> List[Dict]:
        """Извлекает завершенные игры из раздела 'ПОСЛЕДНИЕ РЕЗУЛЬТАТЫ'"""
        try:
            games = []
            full_text = soup.get_text()
            
            # Ищем раздел "ПОСЛЕДНИЕ РЕЗУЛЬТАТЫ"
            if "ПОСЛЕДНИЕ РЕЗУЛЬТАТЫ" in full_text:
                start_pos = full_text.find("ПОСЛЕДНИЕ РЕЗУЛЬТАТЫ")
                end_pos = full_text.find("ТАБЛО ИГР", start_pos)
                
                if end_pos == -1:
                    results_text = full_text[start_pos:]
                else:
                    results_text = full_text[start_pos:end_pos]
                
                print(f"   📋 Извлечен раздел результатов (длина: {len(results_text)} символов)")
                
                # Паттерн для завершенных игр
                # Формат: Дата - Команда1 - Команда2 Счет1:Счет2 (периоды)
                result_pattern = r'(\d{2}\.\d{2}\.\d{4})-\s*([^-]+)-\s*([^-]+)\s+(\d+):(\d+)\s*\([^)]+\)'
                result_matches = re.findall(result_pattern, results_text)
                
                for match in result_matches:
                    date, team1, team2, score1, score2 = match
                    game_text = f"{team1.strip()} {team2.strip()}"
                    
                    # Проверяем, есть ли наши команды в этой игре
                    if self.find_target_teams_in_text(game_text):
                        # Определяем нашу команду и соперника
                        our_team = None
                        opponent = None
                        team_type = None
                        
                        if any(target_team in team1 for target_team in ['Pull Up', 'PullUP']):
                            our_team = team1.strip()
                            opponent = team2.strip()
                        elif any(target_team in team2 for target_team in ['Pull Up', 'PullUP']):
                            our_team = team2.strip()
                            opponent = team1.strip()
                        
                        if our_team:
                            # Определяем тип команды
                            if 'фарм' in our_team.lower():
                                team_type = 'состава развития'
                            else:
                                team_type = 'первого состава'
                            
                            games.append({
                                'team1': team1.strip(),
                                'team2': team2.strip(),
                                'score1': score1,
                                'score2': score2,
                                'period': '4',  # Завершенные игры
                                'time': '0:00',  # Завершенные игры
                                'is_finished': True,
                                'date': date,
                                'current_time': get_moscow_time().strftime('%H:%M'),
                                'game_link': '',  # Для завершенных игр ссылка не нужна
                                'our_team': our_team,
                                'team_type': team_type
                            })
                            print(f"   🏀 Найдена завершенная игра: {team1.strip()} vs {team2.strip()} ({score1}:{score2})")
                            print(f"      Дата: {date}, Тип команды: {team_type}")
            
            return games
                
        except Exception as e:
            print(f"   ❌ Ошибка извлечения результатов: {e}")
            return []
    
    def extract_games_from_html(self, soup) -> List[Dict]:
        """Извлекает игры из HTML структуры табло"""
        try:
            games = []
            
            # Ищем все элементы с текстом команд
            target_teams = ['QUASAR', 'PULL UP', 'HSE', 'TAURUS', 'IT BASKET', 'КУДРОВО']
            
            for element in soup.find_all(text=True):
                text = element.strip()
                if any(team in text for team in target_teams):
                    parent = element.parent
                    if parent:
                        # Ищем соседние элементы со счетом и статусом
                        container = parent.parent
                        if container:
                            # Ищем счет и статус в соседних элементах
                            score_elements = container.find_all(text=True)
                            score_text = ' '.join([el.strip() for el in score_elements if el.strip()])
                            
                            # Паттерн для игры: Команда1 Счет1 Счет2 Команда2 Период Время
                            game_pattern = r'([A-ZА-Я\s]+)\s+(\d+)\s+(\d+)\s+([A-ZА-Я\s]+)\s+(\d+)\s+(\d+:\d+)'
                            matches = re.findall(game_pattern, score_text)
                            
                            for match in matches:
                                team1, score1, score2, team2, period, time = match
                                game_text = f"{team1.strip()} {team2.strip()}"
                                
                                # Проверяем, есть ли наши команды в этой игре
                                if self.find_target_teams_in_text(game_text):
                                    # Проверяем, завершена ли игра (период 4 и время 0:00)
                                    is_finished = period == '4' and time == '0:00'
                                    
                                    # Определяем нашу команду и тип
                                    our_team = None
                                    opponent = None
                                    team_type = None
                                    
                                    if any(target_team in team1 for target_team in ['Pull Up', 'PullUP']):
                                        our_team = team1.strip()
                                        opponent = team2.strip()
                                    elif any(target_team in team2 for target_team in ['Pull Up', 'PullUP']):
                                        our_team = team2.strip()
                                        opponent = team1.strip()
                                    
                                    if our_team:
                                        # Определяем тип команды
                                        if 'фарм' in our_team.lower():
                                            team_type = 'состава развития'
                                        else:
                                            team_type = 'первого состава'
                                        
                                        games.append({
                                            'team1': team1.strip(),
                                            'team2': team2.strip(),
                                            'score1': score1,
                                            'score2': score2,
                                            'period': period,
                                            'time': time,
                                            'is_finished': is_finished,
                                            'date': get_moscow_time().strftime('%d.%m.%Y'),
                                            'current_time': get_moscow_time().strftime('%H:%M'),
                                            'game_link': '',  # Будет добавлена позже
                                            'our_team': our_team,
                                            'team_type': team_type
                                        })
                                        print(f"   🏀 Найдена игра в HTML: {team1.strip()} vs {team2.strip()} ({score1}:{score2})")
                                        print(f"      Период: {period}, Время: {time}, Завершена: {is_finished}")
            
            return games
                
        except Exception as e:
            print(f"   ❌ Ошибка извлечения игр из HTML: {e}")
            return []
    
    async def scan_scoreboard(self) -> List[Dict]:
        """Сканирует табло и находит игры с нашими командами (включая завершенные)"""
        try:
            print("🔍 Сканируем табло letobasket.ru...")
            
            url = "http://letobasket.ru/"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Ищем табло игр
                        games = []
                        
                        # Извлекаем раздел "ТАБЛО ИГР" и ссылки на игры
                        scoreboard_text, game_links, html_games = self.extract_scoreboard_section(soup)
                        
                        # Также проверяем раздел "ПОСЛЕДНИЕ РЕЗУЛЬТАТЫ"
                        recent_results = self.extract_recent_results(soup)
                        
                        if scoreboard_text:
                            print("   ✅ Найдено табло игр")
                            
                            # Сначала ищем все команды в тексте
                            all_teams = []
                            
                            # Ищем команды по названиям (без учета счета)
                            for team in ['Pull Up-Фарм', 'Pull Up Фарм', 'Pull Up', 'PullUP', 'PULL UP ФАРМ']:
                                if team.upper() in scoreboard_text.upper():
                                    all_teams.append(team)
                                    print(f"   🎯 Найдена команда в табло: {team}")
                            
                            if all_teams:
                                print(f"   ✅ Найдено {len(all_teams)} наших команд в табло")
                                
                                # Теперь ищем только текущие игры в табло
                                games_found = []
                                
                                # Паттерн для текущих игр (ТАБЛО ИГР)
                                # Формат: Команда1 Счет1 Счет2 Команда2 Период Время
                                live_pattern = r'(.+?)\s+(\d+)\s+(\d+)\s+(.+?)\s+(\d+)\s+(\d+:\d+)'
                                live_matches = re.findall(live_pattern, scoreboard_text)
                                
                                for i, match in enumerate(live_matches):
                                    team1, score1, score2, team2, period, time = match
                                    game_text = f"{team1.strip()} {team2.strip()}"
                                    
                                    # Проверяем, есть ли наши команды в этой игре
                                    if self.find_target_teams_in_text(game_text):
                                        # Проверяем, завершена ли игра (период 4 и время 0:00)
                                        is_finished = period == '4' and time == '0:00'
                                        
                                        # Получаем ссылку на игру по порядковому номеру
                                        game_link = ""
                                        if i < len(game_links):
                                            game_link = game_links[i]
                                            print(f"   🔗 Используем ссылку #{i+1}: {game_link}")
                                        else:
                                            print(f"   ⚠️ Ссылка для игры #{i+1} не найдена")
                                        
                                        games_found.append({
                                            'team1': team1.strip(),
                                            'team2': team2.strip(),
                                            'score1': score1,
                                            'score2': score2,
                                            'period': period,
                                            'time': time,
                                            'is_finished': is_finished,
                                            'date': get_moscow_time().strftime('%d.%m.%Y'),
                                            'current_time': get_moscow_time().strftime('%H:%M'),
                                            'game_link': game_link
                                        })
                                        print(f"   🏀 Найдена игра (табло): {team1.strip()} vs {team2.strip()} ({score1}:{score2})")
                                        print(f"      Период: {period}, Время: {time}, Завершена: {is_finished}")
                                        if game_link:
                                            print(f"      🔗 Ссылка: {game_link}")
                                
                                games.extend(games_found)
                            else:
                                print(f"   ℹ️ Наших команд не найдено в табло")
                        
                        # Добавляем игры из HTML структуры
                        if html_games:
                            print(f"   ✅ Найдено {len(html_games)} игр в HTML структуре")
                            games.extend(html_games)
                        else:
                            print(f"   ℹ️ Игр в HTML структуре не найдено")
                        
                        # Проверяем завершенные игры в результатах
                        if recent_results:
                            print(f"   ✅ Найдено {len(recent_results)} завершенных игр с нашими командами")
                            games.extend(recent_results)
                        else:
                            print(f"   ℹ️ Завершенных игр с нашими командами не найдено")
                        
                        if games:
                            print(f"   ✅ Всего найдено {len(games)} игр с нашими командами")
                        else:
                            print(f"   ℹ️ Игр с нашими командами не найдено")
                        
                        return games
                    else:
                        print(f"   ❌ Ошибка получения страницы: {response.status}")
                        return []
                        
        except Exception as e:
            print(f"   ❌ Ошибка сканирования табло: {e}")
            return []
    
    async def parse_game_scoreboard(self, game_link: str) -> Optional[Dict]:
        """Парсит табло конкретной игры и извлекает информацию"""
        try:
            # Формируем полный URL
            if game_link.startswith('game.html?'):
                full_url = f"http://letobasket.ru/{game_link}"
            else:
                full_url = game_link
            
            print(f"🔍 Парсим табло: {full_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(full_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Ищем iframe с игрой
                        iframe = soup.find('iframe', src=True)
                        if not iframe:
                            print("   ❌ iframe не найден")
                            return None
                        
                        # Получаем содержимое iframe
                        iframe_src = iframe['src']
                        if not iframe_src.startswith('http'):
                            iframe_src = f"http://ig.russiabasket.ru{iframe_src}"
                        
                        print(f"   🔗 iframe URL: {iframe_src}")
                        
                        async with session.get(iframe_src) as iframe_response:
                            if iframe_response.status == 200:
                                iframe_content = await iframe_response.text()
                                
                                # Парсим информацию из iframe
                                return self.parse_iframe_content(iframe_content)
                            else:
                                print(f"   ❌ Ошибка загрузки iframe: {iframe_response.status}")
                                return None
                    else:
                        print(f"   ❌ Ошибка загрузки страницы: {response.status}")
                        return None
                        
        except Exception as e:
            print(f"   ❌ Ошибка парсинга табло: {e}")
            return None
    
    def parse_iframe_content(self, iframe_content: str) -> Optional[Dict]:
        """Парсит содержимое iframe и извлекает игровую информацию"""
        try:
            soup = BeautifulSoup(iframe_content, 'html.parser')
            
            # Ищем период и время
            period_span = soup.find('span', id='js-period')
            timer_span = soup.find('span', id='js-timer')
            
            period = period_span.get_text().strip() if period_span else None
            timer = timer_span.get_text().strip() if timer_span else None
            
            print(f"   📊 Период: {period}, Время: {timer}")
            
            # Ищем команды и счет
            team1_span = soup.find('span', id='js-score-team1')
            team2_span = soup.find('span', id='js-score-team2')
            
            score1 = team1_span.get_text().strip() if team1_span else None
            score2 = team2_span.get_text().strip() if team2_span else None
            
            print(f"   🏀 Счет: {score1} : {score2}")
            
            # Ищем названия команд
            team_names = self.extract_team_names(iframe_content)
            
            return {
                'period': period,
                'timer': timer,
                'score1': score1,
                'score2': score2,
                'team1_name': team_names.get('team1'),
                'team2_name': team_names.get('team2'),
                'is_game_finished': period == '4' and timer == '0:00'
            }
            
        except Exception as e:
            print(f"   ❌ Ошибка парсинга iframe: {e}")
            return None
    
    def extract_team_names(self, iframe_content: str) -> Dict[str, str]:
        """Извлекает названия команд из iframe"""
        try:
            # Ищем команды в заголовке или других элементах
            soup = BeautifulSoup(iframe_content, 'html.parser')
            
            # Попробуем найти в заголовке
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                # Паттерн: "КОМАНДА1 - КОМАНДА2"
                match = re.search(r'([^-]+)\s*-\s*([^-]+)', title_text)
                if match:
                    return {
                        'team1': match.group(1).strip(),
                        'team2': match.group(2).strip()
                    }
            
            # Если не нашли в заголовке, ищем в других местах
            # Здесь можно добавить дополнительную логику поиска команд
            
            return {'team1': 'Команда 1', 'team2': 'Команда 2'}
            
        except Exception as e:
            print(f"   ❌ Ошибка извлечения названий команд: {e}")
            return {'team1': 'Команда 1', 'team2': 'Команда 2'}
    
    async def send_game_result_notification(self, game_info: Dict, scoreboard_info: Dict, game_link: str):
        """Отправляет уведомление о результате игры"""
        if not self.bot or not CHAT_ID:
            print("❌ Бот или CHAT_ID не настроены")
            return False
        
        try:
            # Определяем соперника
            team1 = game_info.get('team1', '')
            team2 = game_info.get('team2', '')
            
            # Находим нашу команду и соперника
            opponent = None
            team_type = "первого состава"  # По умолчанию
            
            # Используем те же варианты команд, что и в find_target_teams_in_text
            target_teams = ['Pull Up-Фарм', 'Pull Up Фарм', 'Pull Up', 'PullUP']
            
            if any(target_team in team1 for target_team in target_teams):
                opponent = team2
                # Определяем тип команды
                if any(farm_team in team1 for farm_team in ['Pull Up-Фарм', 'Pull Up Фарм']):
                    team_type = "состава развития"
            elif any(target_team in team2 for target_team in target_teams):
                opponent = team1
                # Определяем тип команды
                if any(farm_team in team2 for farm_team in ['Pull Up-Фарм', 'Pull Up Фарм']):
                    team_type = "состава развития"
            
            if not opponent:
                opponent = "соперник"
            
            # Формируем сообщение
            message = f"🏀 Игра {team_type} против {opponent} закончилась\n"
            message += f"🏆 Счет: {scoreboard_info['team1_name']} {scoreboard_info['score1']} : {scoreboard_info['score2']} {scoreboard_info['team2_name']}\n"
            
            # Добавляем ссылку на протокол
            if game_link.startswith('game.html?'):
                full_url = f"http://letobasket.ru/{game_link}"
            else:
                full_url = game_link
            message += f"📊 Ссылка на протокол: <a href=\"{full_url}\">тут</a>"
            
            # Отправляем сообщение
            await self.bot.send_message(
                chat_id=int(CHAT_ID),
                text=message,
                parse_mode='HTML'
            )
            
            print(f"✅ Уведомление о результате отправлено")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка отправки уведомления: {e}")
            return False
    
    async def monitor_games(self):
        """Основная функция мониторинга игр"""
        print("🎮 ЗАПУСК МОНИТОРИНГА ИГР (версия 2)")
        print("=" * 60)
        
        # Проверяем, нужно ли продолжать сегодня
        if not self.should_continue_today():
            return
        
        # Сканируем табло
        active_games = await self.scan_scoreboard()
        
        if not active_games:
            print("📅 Игр с нашими командами не найдено")
            self.mark_no_games_today()
            return
        
        print(f"🏀 Найдено {len(active_games)} игр с нашими командами")
        
        # Проверяем каждую игру
        for i, game in enumerate(active_games, 1):
            print(f"\n🎮 ИГРА {i}/{len(active_games)}: {game['team1']} vs {game['team2']}")
            print(f"   📊 Счет: {game['score1']} : {game['score2']}")
            print(f"   📅 Период: {game['period']}, Время: {game['time']}")
            
            # Создаем game_info для истории
            game_info = {
                'team1': game['team1'],
                'team2': game['team2'],
                'date': game['date'],
                'time': game['current_time']
            }
            game_key = create_game_monitor_key(game_info)
            
            if game['is_finished']:
                print(f"   🏁 Игра завершена!")
                
                # Проверяем, было ли уже отправлено уведомление для этой игры
                if game_key in self.monitor_history:
                    existing_status = self.monitor_history[game_key].get('status', '')
                    if existing_status == 'completed':
                        print(f"   📋 Уведомление уже было отправлено ранее, пропускаем")
                        continue
                    else:
                        print(f"   📋 Найдена запись в истории со статусом: {existing_status}")
                else:
                    print(f"   📋 Записи в истории нет, отправляем уведомление")
                
                print(f"   📤 Отправляем уведомление...")
                
                # Создаем scoreboard_info для уведомления
                scoreboard_info = {
                    'team1_name': game['team1'],
                    'team2_name': game['team2'],
                    'score1': game['score1'],
                    'score2': game['score2']
                }
                
                # Отправляем уведомление с ссылкой на игру
                game_link = game.get('game_link', '')
                await self.send_game_result_notification(game_info, scoreboard_info, game_link)
                
                # Обновляем историю
                self.monitor_history[game_key] = {
                    'game_info': game_info,
                    'status': 'completed',
                    'end_time': get_moscow_time().isoformat()
                }
                save_game_monitor_history(self.monitor_history)
                print(f"   📋 Статус обновлен на 'completed'")
                
            else:
                print(f"   ⏳ Игра еще идет, продолжаем мониторинг")
                
                # Обновляем или создаем запись в истории
                if game_key not in self.monitor_history:
                    self.monitor_history[game_key] = {
                        'game_info': game_info,
                        'status': 'monitoring',
                        'start_time': get_moscow_time().isoformat()
                    }
                    save_game_monitor_history(self.monitor_history)
                    print(f"   📋 Создана запись в истории со статусом 'monitoring'")
                else:
                    print(f"   📋 Запись уже существует в истории")
        
        print(f"\n✅ Мониторинг завершен")

# Функция для запуска мониторинга
async def run_game_results_monitor_v2():
    """Запускает мониторинг результатов игр (версия 2)"""
    monitor = GameResultsMonitorV2()
    await monitor.monitor_games()

if __name__ == "__main__":
    asyncio.run(run_game_results_monitor_v2())
