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
    """Проверяет игры на табло letobasket.ru, которые должны начаться в ближайшие 15 минут или уже мониторятся"""
    try:
        print("🔍 Проверяем игры на табло letobasket.ru...")
        
        # Загружаем историю мониторинга
        monitor_history = load_game_monitor_history()
        
        # Парсим табло letobasket.ru в реальном времени
        games_to_monitor = []
        now = get_moscow_time()
        
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
        
        # Теперь парсим табло letobasket.ru
        try:
            import aiohttp
            from bs4 import BeautifulSoup
            
            url = "http://letobasket.ru/"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Ищем секцию с табло игр
                        scoreboard_section = soup.find('div', class_='scoreboard') or soup.find('div', id='scoreboard')
                        
                        if scoreboard_section:
                            print("   📊 Найдена секция табло")
                            print(f"   🔍 Тип секции: {type(scoreboard_section)}")
                            
                            # Проверяем, что это Tag, а не NavigableString
                            from bs4 import Tag
                            if isinstance(scoreboard_section, Tag):
                                # Ищем игры с нашими командами
                                game_elements = scoreboard_section.find_all(['div', 'tr'])
                            else:
                                print("   ⚠️ Секция табло не является Tag элементом")
                                game_elements = []
                            
                            for game_element in game_elements:
                                try:
                                    # Извлекаем информацию об игре
                                    game_info = await parse_game_from_scoreboard(game_element, now)
                                    
                                    if game_info:
                                        # Проверяем, есть ли наши команды
                                        if has_pull_up_team(game_info):
                                            # Проверяем время начала
                                            time_diff = (game_info['game_time'] - now).total_seconds()
                                            
                                            if 0 <= time_diff <= 900:  # От 0 до 15 минут
                                                # Проверяем, не мониторим ли уже эту игру
                                                game_key = f"{game_info['date']}_{game_info['time']}_{game_info['team1']}_{game_info['team2']}"
                                                if game_key not in monitor_history:
                                                    games_to_monitor.append(game_info)
                                                    print(f"   🏀 Новая игра для мониторинга: {game_info['team1']} vs {game_info['team2']} начинается через {time_diff/60:.1f} минут")
                                                else:
                                                    print(f"   ⏭️ Игра уже в мониторинге: {game_info['team1']} vs {game_info['team2']}")
                                            
                                except Exception as e:
                                    print(f"   ⚠️ Ошибка парсинга игры: {e}")
                                    continue
                        else:
                            print("   ⚠️ Секция табло не найдена на странице")
                    else:
                        print(f"   ❌ Ошибка загрузки страницы: {response.status}")
                        
        except Exception as e:
            print(f"   ❌ Ошибка парсинга табло: {e}")
        
        if games_to_monitor:
            print(f"   ✅ Найдено {len(games_to_monitor)} игр для мониторинга")
        else:
            print(f"   ℹ️ Нет игр для мониторинга в ближайшие 15 минут")
            
        return games_to_monitor
        
    except Exception as e:
        print(f"   ❌ Ошибка проверки игр: {e}")
        return []

async def parse_game_from_scoreboard(game_element, now) -> Optional[Dict]:
    """Парсит информацию об игре из элемента табло"""
    try:
        # Ищем команды
        team_elements = game_element.find_all(['td', 'div'], class_=['team', 'team-name'])
        if len(team_elements) < 2:
            return None
            
        team1 = team_elements[0].get_text(strip=True)
        team2 = team_elements[1].get_text(strip=True)
        
        # Ищем время игры
        time_element = game_element.find(['td', 'div', 'span'], class_=['time', 'game-time', 'start-time'])
        if not time_element:
            return None
            
        time_text = time_element.get_text(strip=True)
        
        # Парсим время (формат может быть разным: "20:30", "20.30", "20-30")
        time_str = time_text.replace('.', ':').replace('-', ':')
        
        # Создаем время игры на сегодня
        game_time = datetime.strptime(f"{now.strftime('%d.%m.%Y')} {time_str}", '%d.%m.%Y %H:%M')
        game_time = game_time.replace(tzinfo=timezone(timedelta(hours=3)))  # МСК
        
        # Ищем ссылку на игру
        link_element = game_element.find('a', href=True)
        game_link = link_element['href'] if link_element else ""
        
        return {
            'date': now.strftime('%d.%m.%Y'),
            'time': time_str,
            'team1': team1,
            'team2': team2,
            'game_time': game_time,
            'game_link': game_link,
            'venue': 'ВО СШОР Малый 66'  # По умолчанию
        }
        
    except Exception as e:
        print(f"   ⚠️ Ошибка парсинга элемента игры: {e}")
        return None

def has_pull_up_team(game_info: dict) -> bool:
    """Проверяет, есть ли команда Pull Up в игре"""
    team1 = game_info.get('team1', '').lower()
    team2 = game_info.get('team2', '').lower()
    
    pull_up_variants = ['pull up', 'pullup', 'pull up-фарм', 'pull up фарм']
    
    for variant in pull_up_variants:
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
