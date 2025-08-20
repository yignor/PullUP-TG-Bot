#!/usr/bin/env python3
"""
Единый модуль для управления системой игр PullUP
Выполняет последовательно: парсинг → создание опросов → создание анонсов
"""

import os
import asyncio
import datetime
import json
import re
from typing import Dict, List, Optional
from dotenv import load_dotenv
from datetime_utils import get_moscow_time, get_moscow_date, is_today, log_current_time

load_dotenv()

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GAMES_TOPIC_ID = os.getenv("GAMES_TOPIC_ID", "1282")  # Топик для опросов по играм
TARGET_TEAMS = os.getenv("TARGET_TEAMS", "PullUP,Pull Up-Фарм").split(",")

# Файлы для истории
POLLS_HISTORY_FILE = "game_polls_history.json"
ANNOUNCEMENTS_HISTORY_FILE = "game_announcements.json"

def load_polls_history() -> Dict:
    """Загружает историю созданных опросов"""
    try:
        if os.path.exists(POLLS_HISTORY_FILE):
            with open(POLLS_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Ошибка загрузки истории опросов: {e}")
    return {}

def save_polls_history(history: Dict):
    """Сохраняет историю созданных опросов"""
    try:
        with open(POLLS_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Ошибка сохранения истории опросов: {e}")

def load_announcements_history() -> Dict:
    """Загружает историю отправленных анонсов"""
    try:
        if os.path.exists(ANNOUNCEMENTS_HISTORY_FILE):
            with open(ANNOUNCEMENTS_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Ошибка загрузки истории анонсов: {e}")
    return {}

def save_announcements_history(history: Dict):
    """Сохраняет историю отправленных анонсов"""
    try:
        with open(ANNOUNCEMENTS_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Ошибка сохранения истории анонсов: {e}")

def create_game_key(game_info: Dict) -> str:
    """Создает уникальный ключ для игры"""
    # Включаем время в ключ для уникальности
    return f"{game_info['date']}_{game_info['time']}_{game_info['team1']}_{game_info['team2']}"

def create_announcement_key(game_info: Dict) -> str:
    """Создает уникальный ключ для анонса"""
    return f"{game_info['date']}_{game_info['team1']}_{game_info['team2']}"

def get_day_of_week(date_str: str) -> str:
    """Возвращает день недели на русском языке"""
    try:
        date_obj = datetime.datetime.strptime(date_str, '%d.%m.%Y')
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        return days[date_obj.weekday()]
    except:
        return ""

def get_team_category(team_name: str) -> str:
    """Определяет категорию команды с правильным склонением"""
    if "Фарм" in team_name:
        return "фарм состава"
    else:
        return "первого состава"

class GameSystemManager:
    """Единый класс для управления всей системой игр"""
    
    def __init__(self):
        self.bot = None
        self.polls_history = load_polls_history()
        self.announcements_history = load_announcements_history()
        
        if BOT_TOKEN:
            from telegram import Bot
            self.bot = Bot(token=BOT_TOKEN)
    
    def find_target_teams_in_text(self, text: str) -> List[str]:
        """Находит целевые команды в тексте"""
        found_teams = []
        # Расширенный список команд для поиска
        search_teams = ['PullUP', 'Pull Up', 'Pull Up-Фарм', 'Pull Up-Фарм']
        
        for team in search_teams:
            if team in text:
                found_teams.append(team)
        return found_teams
    
    def parse_schedule_text(self, text: str) -> List[Dict]:
        """Парсит текст расписания и извлекает информацию об играх"""
        games = []
        
        # Разбиваем текст на строки
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Паттерн для игр с датой и временем
            pattern1 = r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})\s+(.+?)\s+vs\s+(.+?)\s+(.+)'
            match1 = re.search(pattern1, line)
            
            if match1:
                date, time, team1, team2, venue = match1.groups()
                games.append({
                    'date': date,
                    'time': time,
                    'team1': team1.strip(),
                    'team2': team2.strip(),
                    'venue': venue.strip(),
                    'full_text': line
                })
                continue
            
            # Паттерн для игр без времени (из табло)
            pattern2 = r'(.+?)\s+vs\s+(.+)'
            match2 = re.search(pattern2, line)
            
            if match2:
                team1, team2 = match2.groups()
                # Проверяем, есть ли наши команды
                game_text = f"{team1} {team2}"
                if self.find_target_teams_in_text(game_text):
                    games.append({
                        'date': get_moscow_time().strftime('%d.%m.%Y'),
                        'time': '20:30',  # Время по умолчанию
                        'team1': team1.strip(),
                        'team2': team2.strip(),
                        'venue': 'ВО СШОР Малый 66',  # Место по умолчанию
                        'full_text': line
                    })
        
        return games
    
    async def fetch_letobasket_schedule(self) -> List[Dict]:
        """Получает расписание игр с сайта letobasket.ru"""
        try:
            import aiohttp
            from bs4 import BeautifulSoup
            
            url = "http://letobasket.ru/"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Получаем весь текст страницы
                        full_text = soup.get_text()
                        
                        # Ищем игры с нашими командами
                        games = []
                        
                        # Паттерн для игр в формате: дата время (место) - команда1 - команда2
                        game_pattern = r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}\.\d{2})\s+\(([^)]+)\)\s*-\s*([^-]+)\s*-\s*([^-]+)'
                        matches = re.findall(game_pattern, full_text)
                        
                        for match in matches:
                            date, time, venue, team1, team2 = match
                            game_text = f"{team1} {team2}"
                            
                            # Проверяем, есть ли наши команды
                            if self.find_target_teams_in_text(game_text):
                                games.append({
                                    'date': date,
                                    'time': time,
                                    'team1': team1.strip(),
                                    'team2': team2.strip(),
                                    'venue': venue.strip(),
                                    'full_text': f"{date} {time} ({venue}) - {team1.strip()} - {team2.strip()}"
                                })
                        
                        if games:
                            print(f"✅ Найдено {len(games)} игр с нашими командами")
                            return games
                        else:
                            print("⚠️ Игры с нашими командами не найдены")
                            return []
                    else:
                        print(f"❌ Ошибка получения страницы: {response.status}")
                        return []
                        
        except Exception as e:
            print(f"❌ Ошибка получения расписания: {e}")
            return []
    
    def is_game_today(self, game_info: Dict) -> bool:
        """Проверяет, происходит ли игра сегодня"""
        try:
            return is_today(game_info['date'])
        except Exception as e:
            print(f"❌ Ошибка проверки даты игры: {e}")
            return False
    
    def should_create_poll(self, game_info: Dict) -> bool:
        """Проверяет, нужно ли создать опрос для игры"""
        # Проверяем время выполнения (расширенное окно)
        if not self._is_correct_time_for_polls():
            return False
        
        # Создаем уникальный ключ для игры
        game_key = create_game_key(game_info)
        print(f"🔍 Проверяем ключ опроса: {game_key}")
        print(f"📋 История опросов содержит {len(self.polls_history)} записей")
        
        # Проверяем, не создавали ли мы уже опрос для этой игры
        if game_key in self.polls_history:
            print(f"⏭️ Опрос для игры {game_key} уже создан")
            return False
        
        # Специальная проверка для уже созданных опросов (временное решение)
        game_text = f"{game_info.get('team1', '')} vs {game_info.get('team2', '')}"
        if any(existing_game in game_text for existing_game in [
            "Кирпичный Завод vs Pull Up",
            "Lion vs Pull Up", 
            "Quasar vs Pull Up"
        ]):
            print(f"⏭️ Опрос для игры {game_text} уже создан ранее (пропускаем)")
            return False
        
        # Проверяем, есть ли наши команды в игре
        game_text = f"{game_info.get('team1', '')} {game_info.get('team2', '')}"
        target_teams = self.find_target_teams_in_text(game_text)
        
        if not target_teams:
            print(f"ℹ️ Игра без наших команд: {game_info.get('team1', '')} vs {game_info.get('team2', '')}")
            return False
        
        print(f"✅ Игра {game_info['date']} подходит для создания опроса")
        return True
    
    def should_send_announcement(self, game_info: Dict) -> bool:
        """Проверяет, нужно ли отправить анонс для игры"""
        # Проверяем время выполнения (расширенное окно)
        if not self._is_correct_time_for_announcements():
            return False
        
        # Создаем уникальный ключ для игры
        announcement_key = create_announcement_key(game_info)
        
        # Проверяем, не отправляли ли мы уже анонс для этой игры
        if announcement_key in self.announcements_history:
            print(f"⏭️ Анонс для игры {announcement_key} уже отправлен")
            return False
        
        # Проверяем, происходит ли игра сегодня
        if not self.is_game_today(game_info):
            print(f"📅 Игра {game_info['date']} не сегодня")
            return False
        
        # Проверяем, есть ли наши команды в игре
        game_text = f"{game_info.get('team1', '')} {game_info.get('team2', '')}"
        target_teams = self.find_target_teams_in_text(game_text)
        
        if not target_teams:
            print(f"ℹ️ Игра без наших команд: {game_info.get('team1', '')} vs {game_info.get('team2', '')}")
            return False
        
        print(f"✅ Игра {game_info['date']} подходит для анонса (сегодня)")
        return True
    
    def _is_correct_time_for_polls(self) -> bool:
        """Проверяет, подходящее ли время для создания опросов"""
        now = get_moscow_time()
        
        # Создаем опросы в 10:00-10:59 МСК (расширенное окно)
        if now.hour == 10:
            print(f"🕐 Время подходящее для создания опросов: {now.strftime('%H:%M')}")
            return True
        
        print(f"⏰ Не время для создания опросов: {now.strftime('%H:%M')} (нужно 10:00-10:59)")
        return False
    
    def _is_correct_time_for_announcements(self) -> bool:
        """Проверяет, подходящее ли время для отправки анонсов"""
        now = get_moscow_time()
        
        # Отправляем анонсы в 10:00-10:59 МСК (расширенное окно)
        if now.hour == 10:
            print(f"🕐 Время подходящее для отправки анонсов: {now.strftime('%H:%M')}")
            return True
        
        print(f"⏰ Не время для отправки анонсов: {now.strftime('%H:%M')} (нужно 10:00-10:59)")
        return False
    

    
    async def create_game_poll(self, game_info: Dict) -> bool:
        """Создает опрос для игры в топике 1282"""
        if not self.bot or not CHAT_ID:
            print("❌ Бот или CHAT_ID не настроены")
            return False
        
        try:
            # Определяем нашу команду и соперника
            team1 = game_info.get('team1', '')
            team2 = game_info.get('team2', '')
            
            # Находим нашу команду
            our_team = None
            opponent = None
            
            for team in TARGET_TEAMS:
                if team.strip() in team1:
                    our_team = team1
                    opponent = team2
                    break
                elif team.strip() in team2:
                    our_team = team2
                    opponent = team1
                    break
            
            if not our_team:
                print(f"❌ Не удалось определить нашу команду в игре")
                return False
            
            # Определяем категорию команды
            team_category = get_team_category(our_team)
            day_of_week = get_day_of_week(game_info['date'])
            
            # Формируем вопрос в правильном формате
            question = f"Летняя лига, {team_category}, {opponent}: {day_of_week} ({game_info['date']}) {game_info['time']}, {game_info['venue']}"
            
            # Правильные варианты ответов
            options = [
                "✅ Готов",
                "❌ Нет", 
                "👨‍🏫 Тренер"
            ]
            
            # Отправляем опрос в топик для игр (1282)
            message_thread_id = int(GAMES_TOPIC_ID) if GAMES_TOPIC_ID else None
            poll_message = await self.bot.send_poll(
                chat_id=int(CHAT_ID),
                question=question,
                options=options,
                is_anonymous=False,
                allows_multiple_answers=False,
                message_thread_id=message_thread_id
            )
            
            # Сохраняем информацию об опросе
            poll_info = {
                'message_id': poll_message.message_id,
                'poll_id': poll_message.poll.id,
                'question': question,
                'options': options,
                'game_info': game_info,
                'our_team': our_team,
                'opponent': opponent,
                'team_category': team_category,
                'day_of_week': day_of_week,
                'date': get_moscow_time().isoformat(),
                'chat_id': CHAT_ID,
                'topic_id': GAMES_TOPIC_ID
            }
            
            # Сохраняем в историю
            game_key = create_game_key(game_info)
            self.polls_history[game_key] = poll_info
            save_polls_history(self.polls_history)
            
            print(f"✅ Опрос для игры создан в топике {GAMES_TOPIC_ID}")
            print(f"📊 ID опроса: {poll_info['poll_id']}")
            print(f"🏀 Формат: {question}")
            print(f"📅 Дата: {game_info['date']}")
            print(f"🕐 Время: {game_info['time']}")
            print(f"📍 Место: {game_info['venue']}")
            print(f"👥 Категория: {team_category}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка создания опроса для игры: {e}")
            return False
    
    async def find_game_link(self, team1: str, team2: str) -> Optional[str]:
        """Ищет ссылку на игру по командам в табло"""
        try:
            import aiohttp
            from bs4 import BeautifulSoup
            
            url = "http://letobasket.ru/"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Ищем все строки с играми и их ссылки
                        game_rows = []
                        game_links = []
                        
                        # Ищем все ссылки с текстом "СТРАНИЦА ИГРЫ"
                        for link in soup.find_all('a', href=True):
                            if "СТРАНИЦА ИГРЫ" in link.get_text():
                                game_links.append(link['href'])
                        
                        # Ищем строки с командами (с учетом разных вариантов написания)
                        for row in soup.find_all(['div', 'tr', 'td']):
                            row_text = row.get_text().strip().upper()
                            team1_upper = team1.upper()
                            team2_upper = team2.upper()
                            
                            # Проверяем разные варианты написания команд
                            team1_found = (team1_upper in row_text or 
                                          team1_upper.replace(' ', '') in row_text or
                                          team1_upper.replace('-', ' ') in row_text)
                            team2_found = (team2_upper in row_text or 
                                          team2_upper.replace(' ', '') in row_text or
                                          team2_upper.replace('-', ' ') in row_text)
                            
                            if team1_found and team2_found:
                                # Находим позицию этой строки среди всех строк с играми
                                all_game_rows = []
                                for game_row in soup.find_all(['div', 'tr', 'td']):
                                    # Расширенный поиск команд с разными вариантами написания
                                    if any(team in game_row.get_text().upper() for team in [
                                        'PULL UP', 'PULLUP', 'PULL UP ФАРМ', 'PULL UP-ФАРМ',
                                        'КИРПИЧНЫЙ ЗАВОД', 'LION', 'QUASAR', 'КОНСТАНТА', 'АТОМПРОЕКТ',
                                        'SETL GROUP', 'МБИ', 'КОРОЛИ СЕВЕРА', 'ТРЕНД', 'БОРДО', 'ВСЁ СМАРТ', 'ГАП', 'ШТУРВАЛ'
                                    ]):
                                        all_game_rows.append(game_row)
                                
                                for i, game_row in enumerate(all_game_rows):
                                    if game_row == row:
                                        game_position = i + 1
                                        print(f"🎯 Найдена игра {team1} vs {team2} на позиции {game_position}")
                                        
                                        if game_position <= len(game_links):
                                            return game_links[game_position - 1]
                                        else:
                                            print(f"⚠️ Ссылка на игру не найдена (позиция {game_position})")
                                            return None
                        
                        print(f"⚠️ Игра {team1} vs {team2} не найдена в табло")
                        return None
                    else:
                        print(f"❌ Ошибка получения страницы: {response.status}")
                        return None
                        
        except Exception as e:
            print(f"❌ Ошибка поиска ссылки на игру: {e}")
            return None
    
    def format_announcement_message(self, game_info: Dict, game_link: Optional[str] = None) -> str:
        """Форматирует сообщение анонса игры"""
        # Определяем нашу команду и соперника
        team1 = game_info.get('team1', '')
        team2 = game_info.get('team2', '')
        
        # Находим нашу команду
        our_team = None
        opponent = None
        
        for team in TARGET_TEAMS:
            if team.strip() in team1:
                our_team = team1
                opponent = team2
                break
            elif team.strip() in team2:
                our_team = team2
                opponent = team1
                break
        
        if not our_team:
            return f"🏀 Сегодня игра против {opponent} в {game_info['venue']}.\n🕐 Время игры: {game_info['time']}."
        
        # Определяем категорию команды с правильным склонением
        team_category = get_team_category(our_team)
        
        # Формируем анонс
        announcement = f"🏀 Сегодня игра {team_category} против {opponent} в {game_info['venue']}.\n"
        announcement += f"🕐 Время игры: {game_info['time']}."
        
        if game_link:
            if game_link.startswith('game.html?'):
                full_url = f"http://letobasket.ru/{game_link}"
            else:
                full_url = game_link
            announcement += f"\n🔗 Ссылка на игру: <a href=\"{full_url}\">тут</a>"
        
        return announcement
    
    async def send_game_announcement(self, game_info: Dict, game_position: int = 1) -> bool:
        """Отправляет анонс игры в основной топик"""
        if not self.bot or not CHAT_ID:
            print("❌ Бот или CHAT_ID не настроены")
            return False
        
        try:
            # Ищем ссылку на игру по командам
            team1 = game_info.get('team1', '')
            team2 = game_info.get('team2', '')
            game_link = await self.find_game_link(team1, team2)
            
            # Формируем сообщение анонса
            announcement_text = self.format_announcement_message(game_info, game_link)
            
            # Отправляем сообщение в основной топик (без указания топика)
            message = await self.bot.send_message(
                chat_id=int(CHAT_ID),
                text=announcement_text,
                parse_mode='HTML'
            )
            
            # Сохраняем информацию об анонсе
            announcement_key = create_announcement_key(game_info)
            announcement_info = {
                'message_id': message.message_id,
                'text': announcement_text,
                'game_info': game_info,
                'game_link': game_link,
                'game_position': game_position,
                'date': get_moscow_time().isoformat(),
                'chat_id': CHAT_ID,
                'topic_id': 'main'  # Основной топик
            }
            
            # Сохраняем в историю
            self.announcements_history[announcement_key] = announcement_info
            save_announcements_history(self.announcements_history)
            
            print(f"✅ Анонс игры отправлен в основной топик")
            print(f"📊 ID сообщения: {message.message_id}")
            print(f"📅 Дата: {game_info['date']}")
            print(f"🕐 Время: {game_info['time']}")
            print(f"📍 Место: {game_info['venue']}")
            print(f"🎯 Позиция в табло: {game_position}")
            if game_link:
                print(f"🔗 Ссылка: {game_link}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка отправки анонса игры: {e}")
            return False
    
    async def run_full_system(self):
        """Запускает полную систему: парсинг → опросы → анонсы"""
        try:
            print("🚀 ЗАПУСК ПОЛНОЙ СИСТЕМЫ УПРАВЛЕНИЯ ИГРАМИ")
            print("=" * 60)
            
            # Используем централизованное логирование времени
            time_info = log_current_time()
            print(f"🕐 Текущее время (Москва): {time_info['formatted_datetime']}")
            print(f"📅 День недели: {time_info['weekday_name']}")
            
            print(f"\n🔧 НАСТРОЙКИ:")
            print(f"   CHAT_ID: {CHAT_ID}")
            print(f"   GAMES_TOPIC_ID: {GAMES_TOPIC_ID}")
            print(f"   TARGET_TEAMS: {TARGET_TEAMS}")
            print(f"   История опросов: {len(self.polls_history)} записей")
            print(f"   История анонсов: {len(self.announcements_history)} записей")
            
            # ШАГ 1: Парсинг расписания
            print(f"\n📊 ШАГ 1: ПАРСИНГ РАСПИСАНИЯ")
            print("-" * 40)
            games = await self.fetch_letobasket_schedule()
            
            if not games:
                print("⚠️ Игры не найдены, завершаем работу")
                return
            
            print(f"✅ Найдено {len(games)} игр")
            for i, game in enumerate(games, 1):
                print(f"   {i}. {game['full_text']}")
            
            # ШАГ 2: Создание опросов
            print(f"\n📊 ШАГ 2: СОЗДАНИЕ ОПРОСОВ")
            print("-" * 40)
            created_polls = 0
            for game in games:
                print(f"\n🏀 Проверка игры: {game.get('team1', '')} vs {game.get('team2', '')}")
                
                if self.should_create_poll(game):
                    print(f"📊 Создаю опрос для игры...")
                    if await self.create_game_poll(game):
                        created_polls += 1
            
            print(f"✅ Создано {created_polls} опросов")
            
            # ШАГ 3: Создание анонсов
            print(f"\n📢 ШАГ 3: СОЗДАНИЕ АНОНСОВ")
            print("-" * 40)
            sent_announcements = 0
            for game in games:
                print(f"\n🏀 Проверка игры: {game.get('team1', '')} vs {game.get('team2', '')}")
                
                if self.should_send_announcement(game):
                    print(f"📢 Отправляю анонс для игры...")
                    if await self.send_game_announcement(game):
                        sent_announcements += 1
            
            print(f"✅ Отправлено {sent_announcements} анонсов")
            
            # Итоги
            print(f"\n📊 ИТОГИ РАБОТЫ:")
            print(f"   📊 Создано опросов: {created_polls}")
            print(f"   📢 Отправлено анонсов: {sent_announcements}")
            print(f"   📋 Всего игр обработано: {len(games)}")
            
        except Exception as e:
            print(f"❌ Ошибка выполнения системы: {e}")

# Глобальный экземпляр
game_system_manager = GameSystemManager()

async def main():
    """Основная функция"""
    await game_system_manager.run_full_system()

if __name__ == "__main__":
    asyncio.run(main())
