#!/usr/bin/env python3
"""
Получение необработанных обновлений из webhook
"""

import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot

async def get_pending_updates():
    """Получаем необработанные обновления"""
    
    # Загружаем переменные окружения
    load_dotenv()
    
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        print("❌ BOT_TOKEN не найден")
        return
    
    bot = Bot(token=bot_token)
    
    print("🔍 ПОЛУЧЕНИЕ НЕОБРАБОТАННЫХ ОБНОВЛЕНИЙ")
    print("=" * 50)
    
    # Получаем информацию о webhook
    webhook_info = await bot.get_webhook_info()
    print(f"📊 Необработанных обновлений: {webhook_info.pending_update_count}")
    
    if webhook_info.pending_update_count > 0:
        print("🔄 Получаем необработанные обновления...")
        
        # Пробуем получить все необработанные обновления
        try:
            # Используем очень большой лимит
            updates = await bot.get_updates(limit=1000, timeout=30)
            print(f"📊 Получено обновлений: {len(updates)}")
            
            # Анализируем обновления
            poll_answers = []
            poll_questions = []
            other_updates = []
            
            for update in updates:
                if update.poll_answer:
                    poll_answers.append(update)
                elif update.poll:
                    poll_questions.append(update)
                else:
                    other_updates.append(update)
            
            print(f"📊 Poll answers: {len(poll_answers)}")
            print(f"📊 Poll questions: {len(poll_questions)}")
            print(f"📊 Other updates: {len(other_updates)}")
            
            # Анализируем голоса
            if poll_answers:
                print("\n🔍 АНАЛИЗ ГОЛОСОВ:")
                poll_ids = {}
                for update in poll_answers:
                    poll_id = update.poll_answer.poll_id
                    user_id = update.effective_user.id
                    user_name = f"{update.effective_user.first_name} {update.effective_user.last_name or ''}".strip()
                    option_ids = update.poll_answer.option_ids
                    
                    if poll_id not in poll_ids:
                        poll_ids[poll_id] = []
                    
                    poll_ids[poll_id].append({
                        'user_id': user_id,
                        'user_name': user_name,
                        'option_ids': option_ids,
                        'update_id': update.update_id
                    })
                
                for poll_id, votes in poll_ids.items():
                    print(f"\n📊 Опрос {poll_id}:")
                    print(f"   Количество голосов: {len(votes)}")
                    for vote in votes:
                        print(f"   - {vote['user_name']} (ID: {vote['user_id']}) -> {vote['option_ids']}")
            
            # Проверяем, есть ли обновления с нашим опросом
            target_poll_id = "5326045405962572819"
            target_votes = []
            for update in poll_answers:
                if update.poll_answer.poll_id == target_poll_id:
                    target_votes.append(update)
            
            print(f"\n🎯 ГОЛОСА ДЛЯ ЦЕЛЕВОГО ОПРОСА {target_poll_id}:")
            print(f"   Найдено голосов: {len(target_votes)}")
            
            if target_votes:
                for update in target_votes:
                    user = update.effective_user
                    user_name = f"{user.first_name} {user.last_name or ''}".strip()
                    option_ids = update.poll_answer.option_ids
                    print(f"   - {user_name} -> {option_ids}")
            else:
                print("   ❌ Голоса для целевого опроса не найдены")
                
        except Exception as e:
            print(f"❌ Ошибка получения обновлений: {e}")
    else:
        print("✅ Нет необработанных обновлений")

if __name__ == "__main__":
    asyncio.run(get_pending_updates())
