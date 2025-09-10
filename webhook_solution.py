#!/usr/bin/env python3
"""
Решение проблемы с получением всех голосов через webhook
"""

import asyncio
import os
import json
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError

async def setup_webhook_solution():
    """Настройка webhook для получения всех обновлений"""
    
    # Загружаем переменные окружения
    load_dotenv()
    
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        print("❌ BOT_TOKEN не найден")
        return
    
    bot = Bot(token=bot_token)
    
    print("🔧 НАСТРОЙКА WEBHOOK РЕШЕНИЯ")
    print("=" * 50)
    
    # Получаем текущую информацию о webhook
    webhook_info = await bot.get_webhook_info()
    print(f"📊 Текущий webhook URL: {webhook_info.url}")
    print(f"📊 Необработанных обновлений: {webhook_info.pending_update_count}")
    
    if webhook_info.pending_update_count > 0:
        print("⚠️ Есть необработанные обновления!")
        print("🔄 Получаем все необработанные обновления...")
        
        try:
            # Получаем все необработанные обновления
            updates = await bot.get_updates(limit=1000, timeout=30)
            print(f"📊 Получено обновлений: {len(updates)}")
            
            # Сохраняем обновления в файл для анализа
            updates_data = []
            for update in updates:
                update_dict = {
                    'update_id': update.update_id,
                    'poll_answer': None,
                    'poll': None,
                    'message': None
                }
                
                if update.poll_answer:
                    update_dict['poll_answer'] = {
                        'poll_id': update.poll_answer.poll_id,
                        'user': {
                            'id': update.effective_user.id,
                            'first_name': update.effective_user.first_name,
                            'last_name': update.effective_user.last_name,
                            'username': update.effective_user.username
                        },
                        'option_ids': list(update.poll_answer.option_ids)
                    }
                
                if update.poll:
                    update_dict['poll'] = {
                        'id': update.poll.id,
                        'question': update.poll.question,
                        'options': [option.text for option in update.poll.options]
                    }
                
                updates_data.append(update_dict)
            
            # Сохраняем в файл
            with open('all_updates.json', 'w', encoding='utf-8') as f:
                json.dump(updates_data, f, ensure_ascii=False, indent=2)
            
            print("✅ Все обновления сохранены в all_updates.json")
            
            # Анализируем голоса
            poll_answers = [u for u in updates_data if u['poll_answer']]
            print(f"📊 Найдено голосов: {len(poll_answers)}")
            
            # Группируем по опросам
            polls = {}
            for update in poll_answers:
                poll_id = update['poll_answer']['poll_id']
                if poll_id not in polls:
                    polls[poll_id] = []
                polls[poll_id].append(update['poll_answer'])
            
            print(f"📊 Найдено опросов: {len(polls)}")
            
            for poll_id, votes in polls.items():
                print(f"\n📊 Опрос {poll_id}:")
                print(f"   Количество голосов: {len(votes)}")
                for vote in votes:
                    user_name = f"{vote['user']['first_name']} {vote['user']['last_name'] or ''}".strip()
                    print(f"   - {user_name} -> {vote['option_ids']}")
            
            # Проверяем целевой опрос
            target_poll_id = "5326045405962572819"
            if target_poll_id in polls:
                target_votes = polls[target_poll_id]
                print(f"\n🎯 ЦЕЛЕВОЙ ОПРОС {target_poll_id}:")
                print(f"   Найдено голосов: {len(target_votes)}")
                
                # Анализируем голоса
                tuesday_voters = []
                friday_voters = []
                trainer_voters = []
                no_voters = []
                
                for vote in target_votes:
                    user_name = f"{vote['user']['first_name']} {vote['user']['last_name'] or ''}".strip()
                    option_ids = vote['option_ids']
                    
                    if 0 in option_ids:
                        tuesday_voters.append(user_name)
                    if 1 in option_ids:
                        friday_voters.append(user_name)
                    if 2 in option_ids:
                        trainer_voters.append(user_name)
                    if 3 in option_ids:
                        no_voters.append(user_name)
                
                print(f"   Вторник: {len(tuesday_voters)} участников")
                print(f"   Пятница: {len(friday_voters)} участников")
                print(f"   Тренер: {len(trainer_voters)} участников")
                print(f"   Нет: {len(no_voters)} участников")
                
                if tuesday_voters:
                    print(f"   Участники вторника: {', '.join(tuesday_voters)}")
                if friday_voters:
                    print(f"   Участники пятницы: {', '.join(friday_voters)}")
                
                # Сохраняем результаты
                results = {
                    'poll_id': target_poll_id,
                    'tuesday_voters': tuesday_voters,
                    'friday_voters': friday_voters,
                    'trainer_voters': trainer_voters,
                    'no_voters': no_voters,
                    'total_votes': len(target_votes)
                }
                
                with open('poll_results_complete.json', 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                print("✅ Полные результаты сохранены в poll_results_complete.json")
                
            else:
                print(f"❌ Целевой опрос {target_poll_id} не найден в обновлениях")
                
        except Exception as e:
            print(f"❌ Ошибка получения обновлений: {e}")
    else:
        print("✅ Нет необработанных обновлений")

if __name__ == "__main__":
    asyncio.run(setup_webhook_solution())
