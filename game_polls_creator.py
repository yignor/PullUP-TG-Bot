#!/usr/bin/env python3
"""
Модуль для создания голосований по играм в топике 1282
"""

import os
import asyncio
import datetime
import json
import re
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GAMES_TOPIC_ID = os.getenv("GAMES_TOPIC_ID", "1282")  # Топик для опросов по играм
TARGET_TEAMS = os.getenv("TARGET_TEAMS", "PullUP,Pull Up-Фарм").split(",")

# Файлы для истории
POLLS_HISTORY_FILE = "game_polls_history.json"

def get_moscow_time():
    """Возвращает текущее время в московском часовом поясе"""
    moscow_tz = datetime.timezone(datetime.timedelta(hours=3))
    return datetime.datetime.now(moscow_tz)

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
    """Определяет категорию команды"""
    if "Фарм" in team_name:
        return "Фарм"
    else:
        return "Первый"

class GamePollsCreator:
    """Класс для создания голосований по играм"""
    
    def __init__(self):
        self.bot = None
        self.polls_history = load_polls_history()
        
        if BOT_TOKEN:
            from telegram import Bot
            self.bot = Bot(token=BOT_TOKEN)
    
    def find_target_teams_in_text(self, text: str) -> List[str]:
        """Находит целевые команды в тексте"""
        found_teams = []
        for team in TARGET_TEAMS:
            if team.strip() in text:
                found_teams.append(team.strip())
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
            
            # Ищем паттерны игр
            # Паттерн 1: "Дата Время Команда1 vs Команда2 Место"
            
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
                        
                        # Ищем блок с расписанием
                        schedule_text = ""
                        
                        # Ищем текст расписания в различных блоках
                        schedule_blocks = soup.find_all(['div', 'p', 'span'], string=re.compile(r'PullUP|Фарм|vs'))
                        
                        for block in schedule_blocks:
                            if block.get_text():
                                schedule_text += block.get_text() + "\n"
                        
                        if schedule_text:
                            return self.parse_schedule_text(schedule_text)
                        else:
                            print("⚠️ Расписание не найдено на странице")
                            return []
                    else:
                        print(f"❌ Ошибка получения страницы: {response.status}")
                        return []
                        
        except Exception as e:
            print(f"❌ Ошибка получения расписания: {e}")
            return []
    
    def should_create_poll(self, game_info: Dict) -> bool:
        """Проверяет, нужно ли создать опрос для игры"""
        # Создаем уникальный ключ для игры
        game_key = create_game_key(game_info)
        
        # Проверяем, не создавали ли мы уже опрос для этой игры
        if game_key in self.polls_history:
            print(f"⏭️ Опрос для игры {game_key} уже создан")
            return False
        
        # Проверяем, есть ли наши команды в игре
        game_text = f"{game_info.get('team1', '')} {game_info.get('team2', '')}"
        target_teams = self.find_target_teams_in_text(game_text)
        
        if not target_teams:
            print(f"ℹ️ Игра без наших команд: {game_info.get('team1', '')} vs {game_info.get('team2', '')}")
            return False
        
        print(f"✅ Игра {game_info['date']} подходит для создания опроса")
        return True
    
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
    
    async def check_and_create_game_polls(self):
        """Проверяет расписание и создает опросы для игр наших команд"""
        try:
            print("🔍 Проверка расписания игр для создания опросов...")
            
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
                
                if self.should_create_poll(game):
                    print(f"📊 Создаю опрос для игры...")
                    if await self.create_game_poll(game):
                        created_polls += 1
            
            print(f"\n📊 ИТОГО: Создано {created_polls} опросов")
            
        except Exception as e:
            print(f"❌ Ошибка проверки расписания игр: {e}")

# Глобальный экземпляр
game_polls_creator = GamePollsCreator()

async def main():
    """Основная функция"""
    print("📊 СОЗДАТЕЛЬ ОПРОСОВ ПО ИГРАМ")
    print("=" * 60)
    
    moscow_tz = datetime.timezone(datetime.timedelta(hours=3))
    now = datetime.datetime.now(moscow_tz)
    print(f"🕐 Текущее время (Москва): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 День недели: {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'][now.weekday()]}")
    
    print(f"\n🔧 НАСТРОЙКИ:")
    print(f"   CHAT_ID: {CHAT_ID}")
    print(f"   GAMES_TOPIC_ID: {GAMES_TOPIC_ID}")
    print(f"   TARGET_TEAMS: {TARGET_TEAMS}")
    print(f"   История опросов: {len(game_polls_creator.polls_history)} записей")
    
    # Запускаем проверку и создание опросов
    await game_polls_creator.check_and_create_game_polls()
    
    print(f"\n📊 ИСТОРИЯ ОПРОСОВ:")
    for key, poll_info in game_polls_creator.polls_history.items():
        print(f"   {key}: {poll_info.get('question', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(main())
