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
            'PullUP'         # Без пробела
        ]
        
        for team in search_teams:
            if team in text:
                found_teams.append(team)
                print(f"   ✅ Найдена команда: {team}")
        
        return found_teams
    
    async def scan_scoreboard(self) -> List[Dict]:
        """Сканирует табло и находит игры с нашими командами"""
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
                        
                        # Получаем весь текст страницы
                        scoreboard_text = soup.get_text()
                        
                        if "ТАБЛО ИГР" in scoreboard_text:
                            print("   ✅ Найдено табло игр")
                            
                            # Сначала ищем все команды в тексте
                            all_teams = []
                            
                            # Ищем команды по названиям (без учета счета)
                            for team in ['Pull Up-Фарм', 'Pull Up Фарм', 'Pull Up', 'PullUP']:
                                if team in scoreboard_text:
                                    all_teams.append(team)
                                    print(f"   🎯 Найдена команда в табло: {team}")
                            
                            if all_teams:
                                print(f"   ✅ Найдено {len(all_teams)} наших команд в табло")
                                
                                # Теперь ищем игры с этими командами
                                # Паттерн для результатов игр: дата- команда1 - команда2 счет1:счет2
                                game_pattern = r'(\d{2}\.\d{2}\.\d{4})-\s*([^-]+)-\s*([^-]+)\s+(\d+):(\d+)'
                                matches = re.findall(game_pattern, scoreboard_text)
                                
                                for match in matches:
                                    date, team1, team2, score1, score2 = match
                                    game_text = f"{team1.strip()} {team2.strip()}"
                                    
                                    # Проверяем, есть ли наши команды в этой игре
                                    if self.find_target_teams_in_text(game_text):
                                        # Для результатов игр считаем, что игра завершена (есть счет)
                                        is_finished = True
                                        
                                        games.append({
                                            'team1': team1.strip(),
                                            'team2': team2.strip(),
                                            'score1': score1,
                                            'score2': score2,
                                            'period': '4',  # Результат означает завершенную игру
                                            'time': '0:00',  # Результат означает завершенную игру
                                            'is_finished': is_finished,
                                            'date': date,
                                            'current_time': get_moscow_time().strftime('%H:%M')
                                        })
                                        print(f"   🏀 Найдена завершенная игра: {team1.strip()} vs {team2.strip()} ({score1}:{score2})")
                                        print(f"      Дата: {date}, Завершена: {is_finished}")
                            else:
                                print(f"   ℹ️ Наших команд не найдено в табло")
                        else:
                            print(f"   ℹ️ Табло игр не найдено на странице")
                        
                        if games:
                            print(f"   ✅ Найдено {len(games)} игр с нашими командами")
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
                print(f"   🏁 Игра завершена! Отправляем уведомление")
                
                # Создаем scoreboard_info для уведомления
                scoreboard_info = {
                    'team1_name': game['team1'],
                    'team2_name': game['team2'],
                    'score1': game['score1'],
                    'score2': game['score2']
                }
                
                # Отправляем уведомление
                await self.send_game_result_notification(game_info, scoreboard_info, "")
                
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
