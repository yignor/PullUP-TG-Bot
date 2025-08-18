#!/usr/bin/env python3
"""
Исправленный мониторинг расписания игр
"""

import os
import asyncio
import datetime
import json
import aiohttp
import re
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from telegram import Bot
from bs4 import BeautifulSoup

# Загружаем переменные окружения
load_dotenv()

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ANNOUNCEMENTS_TOPIC_ID = os.getenv("ANNOUNCEMENTS_TOPIC_ID", "1282")
TARGET_TEAMS = os.getenv("TARGET_TEAMS", "PullUP,Pull Up-Фарм")

# Файл для хранения созданных опросов
POLLS_HISTORY_FILE = "game_polls_history.json"

def get_moscow_time():
    """Возвращает текущее время в часовом поясе Москвы"""
    moscow_tz = datetime.timezone(datetime.timedelta(hours=3))
    return datetime.datetime.now(moscow_tz)

def get_day_of_week(date_str: str) -> str:
    """Получает день недели из даты"""
    try:
        date_obj = datetime.datetime.strptime(date_str, '%d.%m.%Y')
        days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        return days[date_obj.weekday()]
    except:
        return "Неизвестно"

def get_team_category(team_name: str) -> str:
    """Определяет категорию команды"""
    if "фарм" in team_name.lower():
        return "развитие"
    else:
        return "первый состав"

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

def create_game_key(game_info: Dict) -> str:
    """Создает уникальный ключ для игры"""
    return f"{game_info['date']}_{game_info['time']}_{game_info['team1']}_{game_info['team2']}"

class GameScheduleMonitorFixed:
    """Исправленный мониторинг расписания игр"""
    
    def __init__(self):
        self.bot = None
        self.polls_history = load_polls_history()
        self._init_bot()
    
    def _init_bot(self):
        """Инициализация бота"""
        if BOT_TOKEN:
            self.bot = Bot(token=BOT_TOKEN)
            print("✅ Бот инициализирован")
        else:
            print("❌ BOT_TOKEN не настроен")
    
    def get_target_team_names(self) -> List[str]:
        """Получает список целевых команд"""
        return [team.strip() for team in TARGET_TEAMS.split(",") if team.strip()]
    
    def find_target_teams_in_text(self, text_block: str) -> List[str]:
        """Ищет целевые команды в тексте"""
        found = []
        target_teams = self.get_target_team_names()
        
        for team in target_teams:
            # Универсальная проверка для PullUP-подобных команд
            if re.match(r"^pull", team, re.IGNORECASE) and "up" in team.lower():
                pattern = r"pull\s*[-\s]*up"
                if re.search(pattern, text_block, re.IGNORECASE):
                    found.append(team)
            else:
                # Обычная проверка для других команд
                pattern = re.escape(team)
                if re.search(pattern, text_block, re.IGNORECASE):
                    found.append(team)
        
        # Удаляем дубликаты
        seen = set()
        unique_found = []
        for team in found:
            if team.lower() not in seen:
                unique_found.append(team)
                seen.add(team.lower())
        
        return unique_found
    
    def parse_schedule_text(self, text: str) -> List[Dict]:
        """Парсит расписание из текста"""
        games = []
        
        # Паттерн для поиска игр: дата время (место) - команда1 - команда2
        # Пример: 20.08.2025 20.30 (ВО СШОР Малый 66) - Кирпичный Завод - Pull Up-Фарм
        pattern = r'(\d{1,2}\.\d{2}\.\d{4})\s+(\d{1,2}\.\d{2})\s+\(([^)]+)\)\s+-\s+([^-]+)\s+-\s+([^-]+)'
        
        matches = re.findall(pattern, text)
        
        for match in matches:
            date_str, time_str, venue, team1, team2 = match
            
            # Формируем полное время
            full_time = f"{date_str} {time_str}"
            
            # Очищаем названия команд
            team1 = team1.strip()
            team2 = team2.strip()
            
            game_info = {
                'date': date_str,
                'time': full_time,
                'venue': venue.strip(),
                'team1': team1,
                'team2': team2,
                'full_text': f"{full_time} ({venue}) - {team1} - {team2}"
            }
            
            games.append(game_info)
        
        return games
    
    async def fetch_letobasket_schedule(self) -> List[Dict]:
        """Получает расписание игр с сайта letobasket.ru"""
        try:
            url = "http://letobasket.ru"
            
            print(f"🌐 Получение данных с {url}...")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        print(f"❌ Ошибка получения страницы: {response.status}")
                        return []
                    
                    html = await response.text()
                    print(f"✅ Страница получена, размер: {len(html)} символов")
            
            # Парсим HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Ищем таблицы с расписанием
            tables = soup.find_all('table')
            
            all_games = []
            
            for table in tables:
                # Получаем весь текст таблицы
                table_text = table.get_text()
                
                # Парсим игры из текста таблицы
                games = self.parse_schedule_text(table_text)
                
                if games:
                    print(f"📊 Найдено {len(games)} игр в таблице")
                    all_games.extend(games)
            
            # Удаляем дубликаты
            unique_games = []
            seen_games = set()
            
            for game in all_games:
                game_key = create_game_key(game)
                if game_key not in seen_games:
                    unique_games.append(game)
                    seen_games.add(game_key)
            
            print(f"📊 Всего найдено {len(unique_games)} уникальных игр")
            return unique_games
            
        except Exception as e:
            print(f"❌ Ошибка получения расписания: {e}")
            return []
    
    def should_create_poll_for_game(self, game_info: Dict) -> bool:
        """Проверяет, нужно ли создать опрос для игры"""
        # Создаем уникальный ключ для игры
        game_key = create_game_key(game_info)
        
        # Проверяем, не создавали ли мы уже опрос для этой игры
        if game_key in self.polls_history:
            print(f"⏭️ Опрос для игры {game_key} уже создан ранее")
            return False
        
        # Проверяем, есть ли наши команды в игре
        game_text = f"{game_info.get('team1', '')} {game_info.get('team2', '')}"
        target_teams = self.find_target_teams_in_text(game_text)
        
        if not target_teams:
            print(f"ℹ️ Игра без наших команд: {game_info.get('team1', '')} vs {game_info.get('team2', '')}")
            return False
        
        # Проверяем дату игры (создаем опрос для игр в ближайшие 30 дней)
        try:
            game_date = datetime.datetime.strptime(game_info['date'], '%d.%m.%Y').date()
            now = get_moscow_time().date()
            days_until_game = (game_date - now).days
            
            if days_until_game < 0:
                print(f"⏰ Игра {game_info['date']} уже прошла")
                return False
            elif days_until_game > 30:
                print(f"⏰ Игра {game_info['date']} слишком далеко (через {days_until_game} дней)")
                return False
            
            print(f"✅ Игра {game_info['date']} подходит для создания опроса (через {days_until_game} дней)")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка проверки даты игры: {e}")
            return False
    
    async def create_game_poll(self, game_info: Dict) -> bool:
        """Создает опрос для игры в правильном формате"""
        if not self.bot or not CHAT_ID:
            print("❌ Бот или CHAT_ID не настроены")
            return False
        
        try:
            # Определяем нашу команду и соперника
            team1 = game_info.get('team1', '')
            team2 = game_info.get('team2', '')
            
            if "pull" in team1.lower() and "up" in team1.lower():
                our_team = team1
                opponent = team2
            elif "pull" in team2.lower() and "up" in team2.lower():
                our_team = team2
                opponent = team1
            else:
                print("❌ Не найдена команда PullUP в игре")
                return False
            
            # Определяем категорию команды
            team_category = get_team_category(our_team)
            
            # Получаем день недели
            day_of_week = get_day_of_week(game_info['date'])
            
            # Формируем вопрос в правильном формате
            question = f"Летняя лига, {team_category}, {opponent}: {day_of_week} ({game_info['date']}) {game_info['time'].split()[1]}, {game_info['venue']}"
            
            # Правильные варианты ответов
            options = [
                "✅ Готов",
                "❌ Нет", 
                "👨‍🏫 Тренер"
            ]
            
            # Отправляем опрос (пока без топика для тестирования)
            poll_message = await self.bot.send_poll(
                chat_id=int(CHAT_ID),
                question=question,
                options=options,
                is_anonymous=False,
                allows_multiple_answers=False
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
                'chat_id': CHAT_ID
            }
            
            # Сохраняем в историю
            game_key = create_game_key(game_info)
            self.polls_history[game_key] = poll_info
            save_polls_history(self.polls_history)
            
            print(f"✅ Опрос для игры создан")
            print(f"📊 ID опроса: {poll_info['poll_id']}")
            print(f"🏀 Формат: {question}")
            print(f"📅 Дата: {game_info['date']}")
            print(f"🕐 Время: {game_info['time'].split()[1]}")
            print(f"📍 Место: {game_info['venue']}")
            print(f"👥 Категория: {team_category}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка создания опроса для игры: {e}")
            return False
    
    async def check_and_create_game_polls(self):
        """Проверяет расписание и создает опросы для игр"""
        try:
            print("🔍 Проверка расписания игр...")
            
            # Получаем расписание
            games = await self.fetch_letobasket_schedule()
            
            if not games:
                print("⚠️ Игры не найдены")
                return
            
            # Показываем все найденные игры
            print(f"\n📊 НАЙДЕННЫЕ ИГРЫ:")
            for i, game in enumerate(games, 1):
                print(f"   {i}. {game['full_text']}")
            
            # Проверяем каждую игру
            created_polls = 0
            for game in games:
                print(f"\n🏀 Проверка игры: {game.get('team1', '')} vs {game.get('team2', '')}")
                
                if self.should_create_poll_for_game(game):
                    print(f"📊 Создаю опрос для игры...")
                    if await self.create_game_poll(game):
                        created_polls += 1
            
            print(f"\n📊 ИТОГО: Создано {created_polls} новых опросов")
            
        except Exception as e:
            print(f"❌ Ошибка проверки расписания игр: {e}")

# Глобальный экземпляр
game_monitor = GameScheduleMonitorFixed()

async def main():
    """Основная функция"""
    print("🏀 ИСПРАВЛЕННЫЙ МОНИТОРИНГ РАСПИСАНИЯ ИГР")
    print("=" * 60)
    
    moscow_tz = datetime.timezone(datetime.timedelta(hours=3))
    now = datetime.datetime.now(moscow_tz)
    print(f"🕐 Текущее время (Москва): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 День недели: {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'][now.weekday()]}")
    
    # Проверяем переменные окружения
    bot_token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    
    print("🔧 ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ:")
    print(f"BOT_TOKEN: {'✅' if bot_token else '❌'}")
    print(f"CHAT_ID: {'✅' if chat_id else '❌'}")
    print(f"ANNOUNCEMENTS_TOPIC_ID: {ANNOUNCEMENTS_TOPIC_ID}")
    print(f"TARGET_TEAMS: {TARGET_TEAMS}")
    
    if not all([bot_token, chat_id]):
        print("❌ Не все переменные окружения настроены")
        return
    
    print(f"✅ CHAT_ID: {chat_id}")
    
    # Показываем историю опросов
    print(f"\n📋 ИСТОРИЯ СОЗДАННЫХ ОПРОСОВ:")
    if game_monitor.polls_history:
        for game_key, poll_info in game_monitor.polls_history.items():
            print(f"   🏀 {game_key}")
            print(f"      📊 ID: {poll_info.get('poll_id', 'N/A')}")
            print(f"      📅 Дата создания: {poll_info.get('date', 'N/A')}")
    else:
        print("   📝 История пуста")
    
    # Запускаем проверку
    print("\n🔄 Запуск проверки расписания игр...")
    await game_monitor.check_and_create_game_polls()

if __name__ == "__main__":
    asyncio.run(main())
