#!/usr/bin/env python3
"""
Тестовый скрипт для проверки системы мониторинга результатов игр
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Добавляем корневую папку в путь для импорта
sys.path.append('..')

# Загружаем переменные окружения
load_dotenv()

async def test_game_results_monitor():
    """Тестирует систему мониторинга результатов игр"""
    print("🧪 ТЕСТ СИСТЕМЫ МОНИТОРИНГА РЕЗУЛЬТАТОВ ИГР")
    print("=" * 60)
    
    try:
        # Импортируем монитор результатов
        import sys
        sys.path.append('..')
        from game_results_monitor import GameResultsMonitor
        
        print("✅ Модуль game_results_monitor импортирован")
        
        # Проверяем настройки
        bot_token = os.getenv('BOT_TOKEN')
        chat_id = os.getenv('CHAT_ID')
        
        print(f"✅ BOT_TOKEN: {'*' * 10}{bot_token[-4:] if bot_token else 'Не настроен'}")
        print(f"✅ CHAT_ID: {chat_id if chat_id else 'Не настроен'}")
        print()
        
        if not bot_token or not chat_id:
            print("❌ BOT_TOKEN или CHAT_ID не настроены")
            return False
        
        # Создаем экземпляр монитора
        monitor = GameResultsMonitor()
        
        # Получаем свежий контент
        print("📡 Получение данных с сайта...")
        html_content = await monitor.get_fresh_page_content()
        
        # Извлекаем текущую дату
        current_date = monitor.extract_current_date(html_content)
        if not current_date:
            print("❌ Не удалось извлечь текущую дату")
            return False
        
        print(f"📅 Текущая дата: {current_date}")
        
        # Проверяем завершенные игры
        print("\n🔍 Поиск завершенных игр PullUP...")
        finished_games = monitor.check_finished_games(html_content, current_date)
        
        print(f"📊 Найдено завершенных игр: {len(finished_games)}")
        
        if finished_games:
            print("\n🏀 ЗАВЕРШЕННЫЕ ИГРЫ:")
            for i, game in enumerate(finished_games, 1):
                print(f"\n{i}. {game['pullup_team']} vs {game['opponent_team']}")
                print(f"   Счет: {game['pullup_score']} : {game['opponent_score']}")
                print(f"   Дата: {game['date']}")
                
                # Определяем результат
                if game['pullup_score'] > game['opponent_score']:
                    result = "🏆 Победа"
                elif game['pullup_score'] < game['opponent_score']:
                    result = "😔 Поражение"
                else:
                    result = "🤝 Ничья"
                print(f"   Результат: {result}")
                
                # Проверяем наличие голосования
                print(f"   🔍 Поиск результатов голосования...")
                poll_results = await monitor.get_poll_results_for_game(
                    game['opponent_team'], 
                    game['date']
                )
                
                if poll_results:
                    votes = poll_results.get('votes', {})
                    ready_count = votes.get('ready', 0)
                    not_ready_count = votes.get('not_ready', 0)
                    coach_count = votes.get('coach', 0)
                    total_votes = votes.get('total', 0)
                    
                    print(f"   📊 Статистика голосования:")
                    print(f"      ✅ Готовы: {ready_count}")
                    print(f"      ❌ Не готовы: {not_ready_count}")
                    print(f"      👨‍🏫 Тренер: {coach_count}")
                    print(f"      📈 Всего: {total_votes}")
                    
                    # Анализ посещаемости
                    if ready_count > 0 and total_votes > 0:
                        attendance_rate = (ready_count / total_votes * 100)
                        if attendance_rate >= 80:
                            analysis = f"🎯 Отличная готовность! ({attendance_rate:.1f}%)"
                        elif attendance_rate >= 60:
                            analysis = f"👍 Хорошая готовность ({attendance_rate:.1f}%)"
                        elif attendance_rate >= 40:
                            analysis = f"⚠️ Средняя готовность ({attendance_rate:.1f}%)"
                        else:
                            analysis = f"😕 Низкая готовность ({attendance_rate:.1f}%)"
                        print(f"      📈 Анализ: {analysis}")
                else:
                    print(f"   📊 Статистика голосования: Не найдена")
        else:
            print("📊 Завершенных игр PullUP не найдено")
        
        # Тестируем отправку уведомления (только для демонстрации)
        print(f"\n🧪 ТЕСТИРОВАНИЕ ОТПРАВКИ УВЕДОМЛЕНИЙ:")
        print("(В реальной работе уведомления отправляются автоматически)")
        
        if finished_games:
            test_game = finished_games[0]
            print(f"   Тестовая игра: {test_game['pullup_team']} vs {test_game['opponent_team']}")
            
            # Получаем результаты голосования для тестовой игры
            poll_results = await monitor.get_poll_results_for_game(
                test_game['opponent_team'], 
                test_game['date']
            )
            
            # Показываем, как будет выглядеть уведомление
            print(f"   📝 Пример уведомления:")
            
            if test_game['pullup_score'] > test_game['opponent_score']:
                result_emoji = "🏆"
                result_text = "победили"
            elif test_game['pullup_score'] < test_game['opponent_score']:
                result_emoji = "😔"
                result_text = "проиграли"
            else:
                result_emoji = "🤝"
                result_text = "сыграли вничью"
            
            print(f"   🏀 Игра против {test_game['opponent_team']} закончилась")
            print(f"   {result_emoji} Счет: {test_game['pullup_team']} {test_game['pullup_score']} : {test_game['opponent_score']} {test_game['opponent_team']} ({result_text})")
            
            if poll_results:
                votes = poll_results.get('votes', {})
                ready_count = votes.get('ready', 0)
                not_ready_count = votes.get('not_ready', 0)
                coach_count = votes.get('coach', 0)
                total_votes = votes.get('total', 0)
                
                print(f"   📊 Статистика голосования:")
                print(f"      ✅ Готовы: {ready_count}")
                print(f"      ❌ Не готовы: {not_ready_count}")
                print(f"      👨‍🏫 Тренер: {coach_count}")
                print(f"      📈 Всего проголосовало: {total_votes}")
            else:
                print(f"   📊 Статистика голосования: Недоступна")
        else:
            print("   Нет завершенных игр для тестирования")
        
        print("\n✅ ТЕСТ ЗАВЕРШЕН УСПЕШНО")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_game_results_monitor())
