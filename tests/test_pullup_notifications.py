#!/usr/bin/env python3
"""
Тестовая версия pullup_notifications для отправки в тестовый канал
"""

import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot

# Загружаем переменные окружения
load_dotenv()

class TestPullUPNotificationManager:
    """Тестовая версия менеджера уведомлений для тестового канала"""
    
    def __init__(self):
        self.bot = Bot(token=os.getenv('BOT_TOKEN')) if os.getenv('BOT_TOKEN') else None
        self.test_chat_id = os.getenv('TEST_CHAT_ID')
    
    async def send_test_morning_notification(self, games, html_content):
        """Отправляет тестовое утреннее уведомление в тестовый канал"""
        if not games:
            print("❌ Нет игр для уведомления")
            return
        
        if not self.test_chat_id:
            print("❌ TEST_CHAT_ID не настроен")
            return
        
        lines = []
        lines.append("🧪 ТЕСТОВОЕ УТРЕННЕЕ УВЕДОМЛЕНИЕ")
        lines.append("")
        
        for game in games:
            lines.append(f"🏀 Сегодня игра против **{game['opponent']}**")
            lines.append(f"⏰ Время игры: **{game['time']}**")
            lines.append("🔗 Ссылка на игру: [тут](http://letobasket.ru/)")
            lines.append("")  # Пустая строка между играми
        
        message = "\n".join(lines)
        
        if self.bot:
            try:
                await self.bot.send_message(
                    chat_id=self.test_chat_id, 
                    text=message, 
                    parse_mode='Markdown'
                )
                print("✅ Тестовое утреннее уведомление отправлено в тестовый канал")
            except Exception as e:
                print(f"❌ Ошибка отправки: {e}")
        else:
            print(f"[DRY_RUN] Тестовое утреннее уведомление: {message}")
    
    async def send_test_finish_notification(self, finished_game):
        """Отправляет тестовое уведомление о завершении игры в тестовый канал"""
        if not self.test_chat_id:
            print("❌ TEST_CHAT_ID не настроен")
            return
        
        # Определяем победителя
        if finished_game['pullup_score'] > finished_game['opponent_score']:
            result_emoji = "🏆"
            result_text = "победили"
        elif finished_game['pullup_score'] < finished_game['opponent_score']:
            result_emoji = "😔"
            result_text = "проиграли"
        else:
            result_emoji = "🤝"
            result_text = "сыграли вничью"
        
        message = "🧪 ТЕСТОВОЕ УВЕДОМЛЕНИЕ О ЗАВЕРШЕНИИ ИГРЫ\n\n"
        message += f"🏀 Игра против **{finished_game['opponent_team']}** закончилась\n"
        message += f"{result_emoji} Счет: **{finished_game['pullup_team']} {finished_game['pullup_score']} : {finished_game['opponent_score']} {finished_game['opponent_team']}** ({result_text})\n"
        message += f"📊 Ссылка на протокол: [тут](http://letobasket.ru/)"
        
        if self.bot:
            try:
                await self.bot.send_message(
                    chat_id=self.test_chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
                print("✅ Тестовое уведомление о завершении игры отправлено в тестовый канал")
            except Exception as e:
                print(f"❌ Ошибка отправки: {e}")
        else:
            print(f"[DRY_RUN] Тестовое уведомление о завершении: {message}")

async def test_pullup_notifications():
    """Тестирует уведомления PullUP в тестовом канале"""
    print("🧪 ТЕСТ УВЕДОМЛЕНИЙ PULLUP В ТЕСТОВОМ КАНАЛЕ")
    print("=" * 50)
    
    # Проверяем настройки
    bot_token = os.getenv('BOT_TOKEN')
    test_chat_id = os.getenv('TEST_CHAT_ID')
    
    if not bot_token:
        print("❌ BOT_TOKEN не настроен")
        return
    
    if not test_chat_id:
        print("❌ TEST_CHAT_ID не настроен")
        print("📝 Добавьте TEST_CHAT_ID в .env для тестирования")
        return
    
    print(f"✅ BOT_TOKEN: {'*' * 10}{bot_token[-4:]}")
    print(f"✅ TEST_CHAT_ID: {test_chat_id}")
    print("🧪 Отправка в ТЕСТОВЫЙ канал")
    print()
    
    manager = TestPullUPNotificationManager()
    
    # Тест 1: Утреннее уведомление о предстоящих играх
    print("1. Отправка тестового утреннего уведомления:")
    
    test_games = [
        {
            'team': 'Pull Up',
            'opponent': 'IT Basket',
            'time': '12.30',
            'order': 2
        },
        {
            'team': 'Pull Up',
            'opponent': 'Маиле Карго',
            'time': '14.00',
            'order': 3
        }
    ]
    
    test_html = "<html><a href='test_link'>Test Link</a></html>"
    
    await manager.send_test_morning_notification(test_games, test_html)
    
    print()
    
    # Тест 2: Уведомление о завершении игры
    print("2. Отправка тестового уведомления о завершении игры:")
    
    test_finished_game = {
        'pullup_team': 'Pull Up',
        'opponent_team': 'IT Basket',
        'pullup_score': 85,
        'opponent_score': 72,
        'date': '16.08.2025'
    }
    
    await manager.send_test_finish_notification(test_finished_game)
    
    print()
    print("🧪 ТЕСТОВЫЕ УВЕДОМЛЕНИЯ ОТПРАВЛЕНЫ В ТЕСТОВЫЙ КАНАЛ")

if __name__ == "__main__":
    asyncio.run(test_pullup_notifications())
