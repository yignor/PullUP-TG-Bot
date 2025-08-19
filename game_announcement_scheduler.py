#!/usr/bin/env python3
"""
Система планирования анонсов игр
- Создает задачи на анонс в день игры
- Интегрируется с системой мониторинга расписания
"""

import os
import asyncio
import datetime
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv
from telegram import Bot

# Загружаем переменные окружения
load_dotenv()

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GAMES_TOPIC_ID = os.getenv("GAMES_TOPIC_ID", "1282")
ANNOUNCEMENTS_TOPIC_ID = os.getenv("ANNOUNCEMENTS_TOPIC_ID", "26")

# Файлы для хранения данных
GAME_ANNOUNCEMENTS_FILE = "game_announcements.json"
GAME_POLLS_HISTORY_FILE = "game_polls_history.json"

def get_moscow_time():
    """Возвращает текущее время в часовом поясе Москвы"""
    moscow_tz = datetime.timezone(datetime.timedelta(hours=3))
    return datetime.datetime.now(moscow_tz)

def load_game_polls_history() -> Dict:
    """Загружает историю созданных опросов"""
    try:
        if os.path.exists(GAME_POLLS_HISTORY_FILE):
            with open(GAME_POLLS_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Ошибка загрузки истории опросов: {e}")
    return {}

def load_game_announcements() -> Dict:
    """Загружает запланированные анонсы игр"""
    try:
        if os.path.exists(GAME_ANNOUNCEMENTS_FILE):
            with open(GAME_ANNOUNCEMENTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Ошибка загрузки анонсов игр: {e}")
    return {}

def save_game_announcements(announcements: Dict):
    """Сохраняет запланированные анонсы игр"""
    try:
        with open(GAME_ANNOUNCEMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(announcements, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Ошибка сохранения анонсов игр: {e}")

def create_announcement_key(game_info: Dict) -> str:
    """Создает уникальный ключ для анонса игры"""
    return f"{game_info['date']}_{game_info['team1']}_{game_info['team2']}"

class GameAnnouncementScheduler:
    """Планировщик анонсов игр"""
    
    def __init__(self):
        self.bot = None
        self.game_polls = load_game_polls_history()
        self.announcements = load_game_announcements()
        self._init_bot()
    
    def _init_bot(self):
        """Инициализация бота"""
        if BOT_TOKEN:
            self.bot = Bot(token=BOT_TOKEN)
            print("✅ Бот инициализирован")
        else:
            print("❌ BOT_TOKEN не настроен")
    
    def should_create_announcement_task(self, game_info: Dict) -> bool:
        """Проверяет, нужно ли создать задачу на анонс"""
        announcement_key = create_announcement_key(game_info)
        
        # Проверяем, не создавали ли мы уже задачу для этой игры
        if announcement_key in self.announcements:
            print(f"⏭️ Задача на анонс для игры {announcement_key} уже создана")
            return False
        
        # Проверяем дату игры
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
            
            print(f"✅ Игра {game_info['date']} подходит для создания задачи на анонс (через {days_until_game} дней)")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка проверки даты игры: {e}")
            return False
    
    async def create_announcement_task(self, game_info: Dict) -> bool:
        """Создает задачу на анонс игры"""
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
            
            # Получаем день недели
            game_date = datetime.datetime.strptime(game_info['date'], '%d.%m.%Y')
            days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
            day_of_week = days[game_date.weekday()]
            
            # Формируем сообщение-задачу
            task_message = f"""🏀 ЗАДАЧА НА АНОНС ИГРЫ

📅 Дата: {game_info['date']} ({day_of_week})
🕐 Время: {game_info['time'].split()[1]}
📍 Место: {game_info['venue']}
👥 Наша команда: {our_team}
⚔️ Соперник: {opponent}

�� Что нужно сделать:
1. Создать анонс игры в топике анонсов
2. Указать время и место сбора
3. Напомнить о форме и экипировке
4. Добавить мотивационное сообщение

⏰ Задача на: {game_info['date']} в 09:00 МСК"""
            
            # Отправляем задачу в топик анонсов
            message_thread_id = int(ANNOUNCEMENTS_TOPIC_ID) if ANNOUNCEMENTS_TOPIC_ID else None
            
            sent_message = await self.bot.send_message(
                chat_id=int(CHAT_ID),
                text=task_message,
                message_thread_id=message_thread_id
            )
            
            # Сохраняем информацию о задаче
            announcement_info = {
                'message_id': sent_message.message_id,
                'game_info': game_info,
                'our_team': our_team,
                'opponent': opponent,
                'day_of_week': day_of_week,
                'task_date': game_info['date'],
                'created_date': get_moscow_time().isoformat(),
                'chat_id': CHAT_ID,
                'topic_id': ANNOUNCEMENTS_TOPIC_ID,
                'status': 'scheduled'
            }
            
            # Сохраняем в историю
            announcement_key = create_announcement_key(game_info)
            self.announcements[announcement_key] = announcement_info
            save_game_announcements(self.announcements)
            
            print(f"✅ Задача на анонс игры создана")
            print(f"📊 ID сообщения: {announcement_info['message_id']}")
            print(f"🏀 Игра: {our_team} vs {opponent}")
            print(f"📅 Дата: {game_info['date']}")
            print(f"🕐 Время: {game_info['time'].split()[1]}")
            print(f"�� Место: {game_info['venue']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка создания задачи на анонс: {e}")
            return False
    
    def process_new_games(self):
        """Обрабатывает новые игры и создает задачи на анонс"""
        print("🔍 Проверка новых игр для создания задач на анонс...")
        
        created_tasks = 0
        
        for game_key, poll_info in self.game_polls.items():
            game_info = poll_info.get('game_info', {})
            
            if not game_info:
                continue
            
            print(f"\n🏀 Проверка игры: {game_info.get('team1', '')} vs {game_info.get('team2', '')}")
            
            if self.should_create_announcement_task(game_info):
                print(f"📋 Создаю задачу на анонс для игры...")
                # Создаем задачу асинхронно
                asyncio.create_task(self.create_announcement_task(game_info))
                created_tasks += 1
        
        print(f"\n📊 ИТОГО: Создано {created_tasks} новых задач на анонс")
        return created_tasks
    
    def should_send_reminder(self) -> bool:
        """Проверяет, нужно ли отправить напоминание об анонсах"""
        now = get_moscow_time()
        
        # Отправляем напоминание каждый день в 09:00 МСК
        if now.hour == 9 and now.minute == 0:
            return True
        
        return False
    
    async def send_announcement_reminders(self):
        """Отправляет напоминания об анонсах на сегодня"""
        if not self.bot or not CHAT_ID:
            return
        
        try:
            today = get_moscow_time().date()
            today_str = today.strftime('%d.%m.%Y')
            
            # Ищем игры на сегодня
            today_games = []
            for announcement_key, announcement_info in self.announcements.items():
                if announcement_info.get('task_date') == today_str:
                    today_games.append(announcement_info)
            
            if today_games:
                reminder_message = f"🔔 НАПОМИНАНИЕ: АНОНСЫ ИГР НА СЕГОДНЯ ({today_str})\n\n"
                
                for i, game in enumerate(today_games, 1):
                    game_info = game.get('game_info', {})
                    reminder_message += f"{i}. 🏀 {game.get('our_team', '')} vs {game.get('opponent', '')}\n"
                    reminder_message += f"   🕐 {game_info.get('time', '').split()[1]}\n"
                    reminder_message += f"   📍 {game_info.get('venue', '')}\n\n"
                
                reminder_message += "📋 Не забудьте создать анонсы в топике анонсов!"
                
                # Отправляем напоминание в топик анонсов
                message_thread_id = int(ANNOUNCEMENTS_TOPIC_ID) if ANNOUNCEMENTS_TOPIC_ID else None
                
                await self.bot.send_message(
                    chat_id=int(CHAT_ID),
                    text=reminder_message,
                    message_thread_id=message_thread_id
                )
                
                print(f"✅ Отправлено напоминание об {len(today_games)} анонсах на сегодня")
            
        except Exception as e:
            print(f"❌ Ошибка отправки напоминаний: {e}")

# Глобальный экземпляр
announcement_scheduler = GameAnnouncementScheduler()

async def main():
    """Основная функция"""
    print("🏀 ПЛАНИРОВЩИК АНОНСОВ ИГР")
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
    print(f"GAMES_TOPIC_ID: {GAMES_TOPIC_ID}")
    print(f"ANNOUNCEMENTS_TOPIC_ID: {ANNOUNCEMENTS_TOPIC_ID}")
    
    if not all([bot_token, chat_id]):
        print("❌ Не все переменные окружения настроены")
        return
    
    print(f"✅ CHAT_ID: {chat_id}")
    
    # Показываем статистику
    print(f"\n📊 СТАТИСТИКА:")
    print(f"   📋 Созданных опросов: {len(announcement_scheduler.game_polls)}")
    print(f"   📝 Запланированных анонсов: {len(announcement_scheduler.announcements)}")
    
    # Показываем запланированные анонсы
    if announcement_scheduler.announcements:
        print(f"\n📋 ЗАПЛАНИРОВАННЫЕ АНОНСЫ:")
        for announcement_key, announcement_info in announcement_scheduler.announcements.items():
            print(f"   🏀 {announcement_key}")
            print(f"      📅 Дата: {announcement_info.get('task_date', 'N/A')}")
            print(f"      👥 Игра: {announcement_info.get('our_team', 'N/A')} vs {announcement_info.get('opponent', 'N/A')}")
            print(f"      📊 Статус: {announcement_info.get('status', 'N/A')}")
    else:
        print("   📝 Запланированных анонсов нет")
    
    # Обрабатываем новые игры
    print("\n🔄 Обработка новых игр...")
    announcement_scheduler.process_new_games()
    
    # Проверяем напоминания
    if announcement_scheduler.should_send_reminder():
        print("\n🔔 Отправка напоминаний об анонсах...")
        await announcement_scheduler.send_announcement_reminders()
    else:
        print("\n⏰ Не время для отправки напоминаний")
        print("📅 Напоминания отправляются каждый день в 09:00 МСК")

if __name__ == "__main__":
    asyncio.run(main())

