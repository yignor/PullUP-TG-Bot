#!/usr/bin/env python3
"""
Скрипт для отладки получения обновлений от Telegram API
"""

import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot

async def debug_updates():
    """Отладка получения обновлений"""
    
    # Загружаем переменные окружения
    load_dotenv()
    
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        print("❌ BOT_TOKEN не найден")
        return
    
    bot = Bot(token=bot_token)
    
    print("🔍 ОТЛАДКА ПОЛУЧЕНИЯ ОБНОВЛЕНИЙ")
    print("=" * 50)
    
    # Пробуем разные offset значения
    offsets = [0, -100, -200, -500, -1000, -2000, -5000, -10000]
    
    for offset in offsets:
        try:
            print(f"\n📊 Пробуем offset: {offset}")
            updates = await bot.get_updates(limit=100, offset=offset, timeout=10)
            print(f"   Получено обновлений: {len(updates)}")
            
            if updates:
                # Анализируем типы обновлений
                poll_answers = 0
                poll_questions = 0
                other = 0
                
                for update in updates:
                    if update.poll_answer:
                        poll_answers += 1
                        print(f"   📊 Poll answer: {update.poll_answer.poll_id} -> {update.poll_answer.option_ids}")
                    elif update.poll:
                        poll_questions += 1
                    else:
                        other += 1
                
                print(f"   Poll answers: {poll_answers}")
                print(f"   Poll questions: {poll_questions}")
                print(f"   Other: {other}")
                
                if poll_answers > 0:
                    print(f"   ✅ Найдены голоса с offset {offset}")
            else:
                print(f"   ❌ Нет обновлений с offset {offset}")
                
        except Exception as e:
            print(f"   ⚠️ Ошибка с offset {offset}: {e}")
    
    # Пробуем получить информацию о боте
    try:
        print(f"\n🤖 Информация о боте:")
        me = await bot.get_me()
        print(f"   Имя: {me.first_name}")
        print(f"   Username: @{me.username}")
        print(f"   ID: {me.id}")
    except Exception as e:
        print(f"   ⚠️ Ошибка получения информации о боте: {e}")

if __name__ == "__main__":
    asyncio.run(debug_updates())
