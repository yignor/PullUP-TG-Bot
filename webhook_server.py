#!/usr/bin/env python3
"""
Автоматический webhook сервер для получения всех обновлений
"""

import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters
from training_polls_enhanced import TrainingPollsManager

class WebhookServer:
    """Webhook сервер для получения обновлений"""
    
    def __init__(self):
        self.bot = None
        self.training_manager = None
        self.poll_data = {}  # Хранилище данных опросов
        
    async def initialize(self):
        """Инициализация"""
        load_dotenv()
        
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            print("❌ BOT_TOKEN не найден")
            return False
        
        self.bot = Bot(token=bot_token)
        self.training_manager = TrainingPollsManager()
        
        return True
    
    async def handle_poll_answer(self, update: Update, context):
        """Обработка голосов в опросах"""
        
        poll_answer = update.poll_answer
        user = update.effective_user
        
        print(f"📊 Получен голос: {user.first_name} -> {poll_answer.option_ids}")
        
        # Сохраняем голос
        poll_id = poll_answer.poll_id
        if poll_id not in self.poll_data:
            self.poll_data[poll_id] = {
                'votes': {},
                'last_updated': datetime.now()
            }
        
        # Обновляем голос пользователя (перезаписываем предыдущий)
        self.poll_data[poll_id]['votes'][user.id] = {
            'user_name': f"{user.first_name} {user.last_name or ''}".strip(),
            'username': user.username,
            'option_ids': list(poll_answer.option_ids),
            'timestamp': datetime.now().isoformat()
        }
        
        self.poll_data[poll_id]['last_updated'] = datetime.now()
        
        # Сохраняем в файл
        await self.save_poll_data()
        
        print(f"✅ Голос сохранен для опроса {poll_id}")
    
    async def handle_poll(self, update: Update, context):
        """Обработка создания опросов"""
        
        poll = update.poll
        print(f"📊 Создан опрос: {poll.question}")
        
        # Сохраняем информацию об опросе
        poll_id = poll.id
        if poll_id not in self.poll_data:
            self.poll_data[poll_id] = {
                'question': poll.question,
                'options': [option.text for option in poll.options],
                'votes': {},
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now()
            }
        
        await self.save_poll_data()
        print(f"✅ Информация об опросе сохранена")
    
    async def save_poll_data(self):
        """Сохранение данных опросов в файл"""
        try:
            with open('webhook_poll_data.json', 'w', encoding='utf-8') as f:
                json.dump(self.poll_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ Ошибка сохранения данных: {e}")
    
    async def load_poll_data(self):
        """Загрузка данных опросов из файла"""
        try:
            with open('webhook_poll_data.json', 'r', encoding='utf-8') as f:
                self.poll_data = json.load(f)
            print(f"✅ Загружены данные {len(self.poll_data)} опросов")
        except FileNotFoundError:
            self.poll_data = {}
            print("📄 Файл данных не найден, создаем новый")
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
            self.poll_data = {}
    
    async def get_poll_results(self, poll_id):
        """Получение результатов опроса"""
        
        if poll_id not in self.poll_data:
            return None
        
        poll_info = self.poll_data[poll_id]
        votes = poll_info['votes']
        
        # Анализируем голоса
        tuesday_voters = []
        friday_voters = []
        trainer_voters = []
        no_voters = []
        
        for user_id, vote_data in votes.items():
            user_name = vote_data['user_name']
            option_ids = vote_data['option_ids']
            
            if 0 in option_ids:  # Вторник
                tuesday_voters.append(user_name)
            if 1 in option_ids:  # Пятница
                friday_voters.append(user_name)
            if 2 in option_ids:  # Тренер
                trainer_voters.append(user_name)
            if 3 in option_ids:  # Нет
                no_voters.append(user_name)
        
        return {
            'poll_id': poll_id,
            'question': poll_info.get('question', ''),
            'tuesday_voters': tuesday_voters,
            'friday_voters': friday_voters,
            'trainer_voters': trainer_voters,
            'no_voters': no_voters,
            'total_votes': len(votes),
            'last_updated': poll_info['last_updated']
        }

async def setup_webhook_server():
    """Настройка webhook сервера"""
    
    print("🔧 НАСТРОЙКА WEBHOOK СЕРВЕРА")
    print("=" * 50)
    
    server = WebhookServer()
    
    if not await server.initialize():
        return
    
    # Загружаем существующие данные
    await server.load_poll_data()
    
    # Создаем приложение
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    
    # Добавляем обработчики
    application.add_handler(MessageHandler(filters.POLL, server.handle_poll))
    application.add_handler(MessageHandler(filters.POLL_ANSWER, server.handle_poll_answer))
    
    print("✅ Webhook сервер настроен")
    print("📋 Для запуска используйте:")
    print("   python webhook_server.py --port 8080")
    print("   или")
    print("   uvicorn webhook_server:app --host 0.0.0.0 --port 8080")

if __name__ == "__main__":
    asyncio.run(setup_webhook_server())
