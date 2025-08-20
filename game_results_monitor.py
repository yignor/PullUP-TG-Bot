#!/usr/bin/env python3
"""
Модуль для автоматического мониторинга результатов игр
"""

import asyncio
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List
import aiohttp
from bs4 import BeautifulSoup
import re

# Импортируем централизованные функции
from datetime_utils import get_moscow_time, is_today

# Константы
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
GAME_MONITOR_HISTORY_FILE = 'game_monitor_history.json'

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

def create_game_monitor_key(game_info: Dict) -> str:
    """Создает уникальный ключ для мониторинга игры"""
    return f"{game_info['date']}_{game_info['time']}_{game_info['team1']}_{game_info['team2']}"

class GameResultsMonitor:
    """Класс для мониторинга результатов игр"""
    
    def __init__(self):
        self.bot = None
        self.monitor_history = load_game_monitor_history()
        
        if BOT_TOKEN:
            from telegram import Bot
            self.bot = Bot(token=BOT_TOKEN)
    
    def should_monitor_game(self, game_info: Dict) -> bool:
        """Проверяет, нужно ли мониторить игру"""
        # Проверяем, что игра сегодня
        if not is_today(game_info['date']):
            print(f"📅 Игра {game_info['date']} не сегодня, пропускаем мониторинг")
            return False
        
        # Создаем уникальный ключ для игры
        game_key = create_game_monitor_key(game_info)
        
        # Проверяем, не мониторим ли мы уже эту игру
        if game_key in self.monitor_history:
            print(f"⏭️ Игра {game_key} уже в мониторинге")
            return False
        
        # Проверяем, есть ли наши команды в игре
        game_text = f"{game_info.get('team1', '')} {game_info.get('team2', '')}"
        if not self.find_target_teams_in_text(game_text):
            print(f"ℹ️ Игра без наших команд: {game_info.get('team1', '')} vs {game_info.get('team2', '')}")
            return False
        
        print(f"✅ Игра {game_info['date']} подходит для мониторинга")
        return True
    
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
    
    async def parse_game_scoreboard(self, game_link: str) -> Optional[Dict]:
        """Парсит табло игры и извлекает информацию"""
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
    
    def determine_winner(self, score1: str, score2: str, team1_name: str, team2_name: str) -> str:
        """Определяет победителя игры"""
        try:
            score1_int = int(score1) if score1 and score1.isdigit() else 0
            score2_int = int(score2) if score2 and score2.isdigit() else 0
            
            if score1_int > score2_int:
                return f"победили {team1_name}"
            elif score2_int > score1_int:
                return f"победили {team2_name}"
            else:
                return "ничья"
        except:
            return "результат не определен"
    
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
            if any(target_team in team1 for target_team in ['Pull Up', 'PullUP']):
                opponent = team2
            elif any(target_team in team2 for target_team in ['Pull Up', 'PullUP']):
                opponent = team1
            
            if not opponent:
                opponent = "соперник"
            
            # Формируем сообщение
            message = f"🏀 Игра против {opponent} закончилась\n"
            message += f"🏆 Счет: {scoreboard_info['team1_name']} {scoreboard_info['score1']} : {scoreboard_info['score2']} {scoreboard_info['team2_name']}\n"
            
            # Убираем определение победителя - это понятно из счета
            # result = self.determine_winner(...)
            # message += f"📊 {result}\n"
            
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
    
    async def monitor_game(self, game_info: Dict, game_link: str):
        """Мониторит игру до завершения"""
        game_key = create_game_monitor_key(game_info)
        
        print(f"🎮 Начинаем мониторинг игры: {game_key}")
        
        # Добавляем в историю мониторинга
        self.monitor_history[game_key] = {
            'game_info': game_info,
            'game_link': game_link,
            'start_time': get_moscow_time().isoformat(),
            'status': 'monitoring'
        }
        save_game_monitor_history(self.monitor_history)
        
        # Определяем время начала мониторинга (близко ко времени игры)
        # Исправляем формат времени (заменяем точку на двоеточие)
        time_str = game_info['time'].replace('.', ':')
        game_time = datetime.strptime(f"{game_info['date']} {time_str}", '%d.%m.%Y %H:%M')
        game_time = game_time.replace(tzinfo=timezone(timedelta(hours=3)))  # МСК
        
        # Начинаем мониторинг за 5 минут до игры
        start_monitoring = game_time - timedelta(minutes=5)
        end_monitoring = game_time + timedelta(hours=3)
        
        now = get_moscow_time()
        
        # Ждем до времени начала мониторинга
        if now < start_monitoring:
            wait_seconds = (start_monitoring - now).total_seconds()
            print(f"⏰ Ждем {wait_seconds:.0f} секунд до начала мониторинга")
            await asyncio.sleep(wait_seconds)
        
        # Мониторим игру каждые 15 минут
        while now < end_monitoring:
            print(f"🔍 Проверяем состояние игры (каждые 15 минут)...")
            
            scoreboard_info = await self.parse_game_scoreboard(game_link)
            
            if scoreboard_info and scoreboard_info['is_game_finished']:
                print(f"🏁 Игра завершена! Отправляем уведомление")
                
                # Отправляем уведомление
                await self.send_game_result_notification(game_info, scoreboard_info, game_link)
                
                # Обновляем статус в истории
                self.monitor_history[game_key]['status'] = 'completed'
                self.monitor_history[game_key]['end_time'] = get_moscow_time().isoformat()
                save_game_monitor_history(self.monitor_history)
                
                return True
            
            # Ждем 15 минут перед следующей проверкой
            await asyncio.sleep(900)  # 15 минут = 900 секунд
            now = get_moscow_time()
        
        print(f"⏰ Время мониторинга истекло (3 часа)")
        
        # Обновляем статус в истории
        self.monitor_history[game_key]['status'] = 'timeout'
        self.monitor_history[game_key]['end_time'] = get_moscow_time().isoformat()
        save_game_monitor_history(self.monitor_history)
        
        return False
    
    async def start_monitoring_for_game(self, game_info: Dict, game_link: str):
        """Запускает мониторинг для конкретной игры"""
        if not self.should_monitor_game(game_info):
            return False
        
        # Запускаем мониторинг в отдельной задаче
        asyncio.create_task(self.monitor_game(game_info, game_link))
        return True

# Функция для запуска мониторинга из других модулей
async def start_game_monitoring(game_info: Dict, game_link: str):
    """Запускает мониторинг игры"""
    monitor = GameResultsMonitor()
    return await monitor.start_monitoring_for_game(game_info, game_link)
