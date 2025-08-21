#!/usr/bin/env python3
"""
Скрипт для запуска мониторинга результатов игр в GitHub Actions
"""

import asyncio
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from game_results_monitor import GameResultsMonitor, load_game_monitor_history, save_game_monitor_history
from datetime_utils import get_moscow_time, is_today
from game_system_manager import GameSystemManager

async def check_games_for_monitoring() -> list:
    """Проверяет игры от GameSystemManager, которые должны начаться в ближайшие 15 минут или уже мониторятся"""
    try:
        print("🔍 ПРОВЕРКА ИГР ОТ GAMESYSTEMMANAGER")
        print("=" * 50)
        
        # Загружаем историю мониторинга
        monitor_history = load_game_monitor_history()
        print(f"📋 Загружена история мониторинга: {len(monitor_history)} записей")
        
        # Получаем информацию от GameSystemManager
        games_to_monitor = []
        now = get_moscow_time()
        print(f"🕐 Текущее время: {now.strftime('%d.%m.%Y %H:%M:%S')}")
        
        # Сначала проверяем активные мониторинги
        print("\n🎮 ПРОВЕРКА АКТИВНЫХ МОНИТОРИНГОВ:")
        active_monitors = []
        for game_key, monitor_info in monitor_history.items():
            status = monitor_info.get('status', 'unknown')
            if status == 'monitoring':
                game_info = monitor_info.get('game_info', {})
                if game_info and is_today(game_info.get('date', '')):
                    active_monitors.append(game_info)
                    start_time = monitor_info.get('start_time', 'неизвестно')
                    print(f"   ✅ Активный мониторинг: {game_info.get('team1', '')} vs {game_info.get('team2', '')}")
                    print(f"      📅 Дата: {game_info.get('date', '')}")
                    print(f"      🕐 Время: {game_info.get('time', '')}")
                    print(f"      🚀 Начало мониторинга: {start_time}")
        
        # Добавляем активные мониторинги в список для проверки
        games_to_monitor.extend(active_monitors)
        if active_monitors:
            print(f"   📊 Всего активных мониторингов: {len(active_monitors)}")
        else:
            print("   ℹ️ Активных мониторингов не найдено")
        
        # Теперь получаем информацию от GameSystemManager
        print("\n📅 ПОЛУЧЕНИЕ РАСПИСАНИЯ ОТ GAMESYSTEMMANAGER:")
        try:
            # Создаем экземпляр GameSystemManager для получения информации об играх
            game_manager = GameSystemManager()
            print("   🔧 Создан экземпляр GameSystemManager")
            
            # Получаем расписание игр
            schedule = await game_manager.fetch_letobasket_schedule()
            
            if schedule:
                print(f"   ✅ Получено расписание: {len(schedule)} игр")
                
                # Показываем все игры сегодня
                today_games = [game for game in schedule if is_today(game['date'])]
                print(f"   📅 Игр сегодня: {len(today_games)}")
                
                for i, game in enumerate(today_games, 1):
                    print(f"      {i}. {game['team1']} vs {game['team2']} - {game['date']} {game['time']}")
                
                # Проверяем игры сегодня
                print(f"\n🔍 АНАЛИЗ ИГР ДЛЯ МОНИТОРИНГА:")
                for game in schedule:
                    if not is_today(game['date']):
                        continue
                        
                    try:
                        # Парсим время игры
                        time_str = game['time'].replace('.', ':')
                        game_time = datetime.strptime(f"{game['date']} {time_str}", '%d.%m.%Y %H:%M')
                        game_time = game_time.replace(tzinfo=timezone(timedelta(hours=3)))  # МСК
                        
                        # Проверяем, начинается ли игра в ближайшие 15 минут
                        time_diff = (game_time - now).total_seconds()
                        
                        print(f"   🏀 {game['team1']} vs {game['team2']}")
                        print(f"      📅 Дата: {game['date']}")
                        print(f"      🕐 Время: {game['time']}")
                        print(f"      ⏰ До начала: {time_diff/60:.1f} минут")
                        
                        # Проверяем окно мониторинга (15 минут до начала)
                        monitoring_start = game_time - timedelta(minutes=15)
                        monitoring_end = game_time + timedelta(hours=3)
                        
                        print(f"      🚀 Мониторинг с: {monitoring_start.strftime('%H:%M')}")
                        print(f"      🛑 Мониторинг до: {monitoring_end.strftime('%H:%M')}")
                        
                        if 0 <= time_diff <= 900:  # От 0 до 15 минут (900 секунд)
                            print(f"      ✅ В окне мониторинга!")
                            
                            # Проверяем, есть ли наши команды в игре
                            if has_pull_up_team(game):
                                print(f"      🎯 Наша команда найдена!")
                                
                                # Проверяем, не мониторим ли уже эту игру
                                game_key = f"{game['date']}_{game['time']}_{game['team1']}_{game['team2']}"
                                if game_key not in monitor_history:
                                    games_to_monitor.append(game)
                                    print(f"      ✅ Добавлена для мониторинга")
                                else:
                                    print(f"      ⏭️ Уже в мониторинге")
                            else:
                                print(f"      ❌ Наша команда не найдена")
                        else:
                            if time_diff < 0:
                                print(f"      ⏰ Игра уже началась")
                            else:
                                print(f"      ⏰ Слишком рано для мониторинга")
                            
                    except Exception as e:
                        print(f"   ⚠️ Ошибка парсинга времени игры: {e}")
                        continue
            else:
                print("   ❌ Расписание не найдено в GameSystemManager")
                        
        except Exception as e:
            print(f"   ❌ Ошибка получения данных от GameSystemManager: {e}")
        
        # Итоговая сводка
        print(f"\n📊 ИТОГОВАЯ СВОДКА:")
        if games_to_monitor:
            print(f"   ✅ Найдено {len(games_to_monitor)} игр для мониторинга:")
            for i, game in enumerate(games_to_monitor, 1):
                print(f"      {i}. {game['team1']} vs {game['team2']} - {game['date']} {game['time']}")
        else:
            print(f"   ℹ️ Нет игр для мониторинга в ближайшие 15 минут")
        
        print("=" * 50)
        return games_to_monitor
        
    except Exception as e:
        print(f"   ❌ Ошибка проверки игр: {e}")
        return []



def has_pull_up_team(game_info: dict) -> bool:
    """Проверяет, есть ли команда Pull Up в игре"""
    team1 = game_info.get('team1', '')
    team2 = game_info.get('team2', '')
    
    # Используем те же варианты команд, что и в game_results_monitor.py
    target_teams = ['Pull Up-Фарм', 'Pull Up Фарм', 'Pull Up', 'PullUP']
    
    for variant in target_teams:
        if variant in team1 or variant in team2:
            return True
    
    return False

async def run_game_results_monitor():
    """Запускает мониторинг результатов игр"""
    print("🏀 ЗАПУСК МОНИТОРИНГА РЕЗУЛЬТАТОВ ИГР")
    print("=" * 60)
    
    # Используем централизованное логирование времени
    now = get_moscow_time()
    print(f"🕐 Текущее время (Москва): {now.strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"🔄 Workflow запущен: {now.strftime('%H:%M:%S')}")
    
    # Проверяем игры для мониторинга
    games_to_monitor = await check_games_for_monitoring()
    
    if not games_to_monitor:
        print("\n📅 Нет игр для мониторинга, завершаем работу")
        print("=" * 60)
        return
    
    try:
        print(f"\n🎮 ЗАПУСК МОНИТОРИНГА ИГР:")
        print("=" * 50)
        
        # Загружаем историю мониторинга
        monitor_history = load_game_monitor_history()
        print(f"📋 История мониторинга содержит {len(monitor_history)} записей")
        
        # Создаем экземпляр монитора
        monitor = GameResultsMonitor()
        print("🔧 Создан экземпляр GameResultsMonitor")
        
        # Проверяем и запускаем мониторинг для каждой игры
        for i, game in enumerate(games_to_monitor, 1):
            print(f"\n🎮 ИГРА {i}/{len(games_to_monitor)}: {game['team1']} vs {game['team2']}")
            print(f"   📅 Дата: {game['date']}")
            print(f"   🕐 Время: {game['time']}")
            
            # Проверяем, есть ли ссылка на игру в истории
            game_key = f"{game['date']}_{game['time']}_{game['team1']}_{game['team2']}"
            game_link = ""
            
            if game_key in monitor_history:
                game_link = monitor_history[game_key].get('game_link', '')
                status = monitor_history[game_key].get('status', 'unknown')
                start_time = monitor_history[game_key].get('start_time', 'неизвестно')
                print(f"   📋 Статус в истории: {status}")
                print(f"   🚀 Начало мониторинга: {start_time}")
                print(f"   🔗 Ссылка: {game_link}")
            else:
                print(f"   📋 Статус в истории: новая игра")
                print(f"   🔗 Ссылка: не найдена")
            
            # Если ссылки нет, пытаемся найти её
            if not game_link:
                print(f"   🔍 Ищем ссылку на игру...")
                # Здесь можно добавить логику поиска ссылки, если нужно
            
            # Запускаем мониторинг
            print(f"   🔄 Запускаем мониторинг...")
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
        
        # Показываем время завершения
        end_time = get_moscow_time()
        print(f"   🕐 Время завершения: {end_time.strftime('%H:%M:%S')}")
        print(f"   ⏱️ Длительность: {(end_time - now).total_seconds():.1f} секунд")
        
        print(f"\n✅ Мониторинг результатов завершен")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Ошибка мониторинга: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_game_results_monitor())
