#!/usr/bin/env python3
"""
Скрипт для запуска мониторинга результатов игр в GitHub Actions
"""

import asyncio
import json
import os
from datetime import datetime, timezone, timedelta
from game_results_monitor import GameResultsMonitor, load_game_monitor_history, save_game_monitor_history
from datetime_utils import get_moscow_time, is_today
from game_system_manager import GameSystemManager

async def check_games_for_monitoring() -> list:
    """Проверяет игры, которые должны начаться в ближайшие 5 минут или уже мониторятся"""
    try:
        print("🔍 Проверяем игры для мониторинга...")
        
        # Создаем экземпляр GameSystemManager для парсинга расписания
        game_manager = GameSystemManager()
        
        # Парсим расписание
        schedule = await game_manager.fetch_letobasket_schedule()
        
        if not schedule:
            print("   📅 Расписание не найдено")
            return []
        
        # Загружаем историю мониторинга
        monitor_history = load_game_monitor_history()
        
        # Проверяем игры сегодня
        now = get_moscow_time()
        games_to_monitor = []
        
        # Сначала проверяем активные мониторинги
        active_monitors = []
        for game_key, monitor_info in monitor_history.items():
            status = monitor_info.get('status', 'unknown')
            if status == 'monitoring':
                game_info = monitor_info.get('game_info', {})
                if game_info and is_today(game_info.get('date', '')):
                    active_monitors.append(game_info)
                    print(f"   🎮 Найден активный мониторинг: {game_info.get('team1', '')} vs {game_info.get('team2', '')}")
        
        # Добавляем активные мониторинги в список для проверки
        games_to_monitor.extend(active_monitors)
        
        # Теперь проверяем новые игры для запуска мониторинга
        for game in schedule:
            if not is_today(game['date']):
                continue
                
            try:
                # Парсим время игры
                time_str = game['time'].replace('.', ':')
                game_time = datetime.strptime(f"{game['date']} {time_str}", '%d.%m.%Y %H:%M')
                game_time = game_time.replace(tzinfo=timezone(timedelta(hours=3)))  # МСК
                
                # Проверяем, начинается ли игра в ближайшие 5 минут
                time_diff = (game_time - now).total_seconds()
                
                if 0 <= time_diff <= 300:  # От 0 до 5 минут (300 секунд)
                    # Проверяем, не мониторим ли уже эту игру
                    game_key = f"{game['date']}_{game['time']}_{game['team1']}_{game['team2']}"
                    if game_key not in monitor_history:
                        games_to_monitor.append(game)
                        print(f"   🏀 Новая игра для мониторинга: {game['team1']} vs {game['team2']} начинается через {time_diff/60:.1f} минут")
                    else:
                        print(f"   ⏭️ Игра уже в мониторинге: {game['team1']} vs {game['team2']}")
                    
            except Exception as e:
                print(f"   ⚠️ Ошибка парсинга времени игры: {e}")
                continue
        
        if games_to_monitor:
            print(f"   ✅ Найдено {len(games_to_monitor)} игр для мониторинга")
        else:
            print(f"   ℹ️ Нет игр для мониторинга")
            
        return games_to_monitor
        
    except Exception as e:
        print(f"   ❌ Ошибка проверки игр: {e}")
        return []

async def run_game_results_monitor():
    """Запускает мониторинг результатов игр"""
    print("🏀 ЗАПУСК МОНИТОРИНГА РЕЗУЛЬТАТОВ ИГР")
    print("=" * 60)
    
    # Используем централизованное логирование времени
    now = get_moscow_time()
    print(f"🕐 Текущее время (Москва): {now.strftime('%d.%m.%Y %H:%M:%S')}")
    
    # Проверяем игры для мониторинга
    games_to_monitor = await check_games_for_monitoring()
    
    if not games_to_monitor:
        print("📅 Нет игр для мониторинга, завершаем работу")
        return
    
    try:
        # Загружаем историю мониторинга
        monitor_history = load_game_monitor_history()
        print(f"📋 История мониторинга содержит {len(monitor_history)} записей")
        
        # Создаем экземпляр монитора
        monitor = GameResultsMonitor()
        
        # Проверяем и запускаем мониторинг для каждой игры
        for game in games_to_monitor:
            print(f"\n🎮 Проверяем игру: {game['team1']} vs {game['team2']}")
            
            # Проверяем, есть ли ссылка на игру в истории
            game_key = f"{game['date']}_{game['time']}_{game['team1']}_{game['team2']}"
            game_link = ""
            
            if game_key in monitor_history:
                game_link = monitor_history[game_key].get('game_link', '')
                print(f"   🔗 Найдена ссылка в истории: {game_link}")
            
            # Если ссылки нет, пытаемся найти её
            if not game_link:
                print(f"   🔍 Ищем ссылку на игру...")
                # Здесь можно добавить логику поиска ссылки, если нужно
            
            # Запускаем мониторинг
            success = await monitor.start_monitoring_for_game(game, game_link)
            
            if success:
                print(f"   ✅ Игра завершена, уведомление отправлено")
            else:
                print(f"   ⏳ Игра еще идет или мониторинг не требуется")
        
        # Сохраняем обновленную историю
        save_game_monitor_history(monitor_history)
        
        print(f"\n📋 ИТОГИ МОНИТОРИНГА:")
        print(f"   Обработано игр: {len(games_to_monitor)}")
        print(f"   Всего записей в истории: {len(monitor_history)}")
        
        print(f"\n✅ Мониторинг результатов завершен")
        
    except Exception as e:
        print(f"❌ Ошибка мониторинга: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_game_results_monitor())
