#!/usr/bin/env python3
"""
Мониторинг сайта letobasket.ru для отслеживания игр PullUP
Обновленная версия с использованием общих модулей
"""

import datetime
import os
import asyncio
import aiohttp
import re
import sys
from bs4 import BeautifulSoup
from typing import Any, Optional
from telegram import Bot
from dotenv import load_dotenv

# Импортируем общие модули
from game_parser import game_parser
from notification_manager import notification_manager

# Загружаем переменные окружения
load_dotenv()

# Получаем переменные окружения (уже настроены в Railway)
BOT_TOKEN: str = os.getenv("BOT_TOKEN") or ""
CHAT_ID: str = os.getenv("CHAT_ID") or ""
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"
USE_BROWSER = os.getenv("USE_BROWSER", "0") == "1"

# Валидируем, что обязательные переменные заданы
if not DRY_RUN:
    if not BOT_TOKEN:
        print("❌ Переменная окружения BOT_TOKEN не установлена")
        sys.exit(1)
    if not CHAT_ID:
        print("❌ Переменная окружения CHAT_ID не установлена")
        sys.exit(1)

bot: Any = None
if not DRY_RUN:
    try:
        # На этом этапе BOT_TOKEN гарантированно str, не None
        bot = Bot(token=BOT_TOKEN)
        print(f"✅ Бот инициализирован успешно")
    except Exception as e:
        print(f"❌ ОШИБКА при инициализации бота: {e}")
        sys.exit(1)

# Переменная для отслеживания статуса игр (активные/завершенные)
game_status = {}  # {game_url: {'status': 'active'|'finished', 'last_check': datetime, 'teams': str}}

def is_game_finished(game_info):
    """Проверяет, завершилась ли игра (по времени)"""
    if not game_info or not game_info.get('time'):
        return False
    
    try:
        # Парсим время игры
        game_time_str = game_info['time']
        time_formats = [
            '%d.%m.%Y %H:%M',
            '%Y-%m-%d %H:%M',
            '%d/%m/%Y %H:%M',
            '%H:%M'
        ]
        
        game_datetime = None
        for fmt in time_formats:
            try:
                if ':' in game_time_str and len(game_time_str.split(':')) == 2:
                    # Если указано только время, добавляем сегодняшнюю дату
                    today = datetime.datetime.now().strftime('%Y-%m-%d')
                    time_str_with_date = f"{today} {game_time_str}"
                    game_datetime = datetime.datetime.strptime(time_str_with_date, '%Y-%m-%d %H:%M')
                else:
                    game_datetime = datetime.datetime.strptime(game_time_str, fmt)
                break
            except ValueError:
                continue
        
        if game_datetime:
            now = datetime.datetime.now()
            # Игра считается завершенной через 2 часа после начала
            game_end_time = game_datetime + datetime.timedelta(hours=2)
            return now > game_end_time
            
    except Exception as e:
        print(f"❌ Ошибка при проверке завершения игры: {e}")
    
    return False

async def check_game_completion(game_url, game_info):
    """Проверяет завершение игры и отправляет статистику"""
    try:
        if not game_info:
            return
        
        # Проверяем, завершилась ли игра
        if is_game_finished(game_info):
            # Используем общий менеджер уведомлений
            await notification_manager.send_game_end_notification(game_info, game_url)
            
    except Exception as e:
        print(f"❌ Ошибка при проверке завершения игры: {e}")

def _build_target_team_patterns():
    """Возвращает список паттернов для поиска целевых команд.

    Можно задать переменную окружения TARGET_TEAMS (через запятую),
    например: "PullUP,Визотек".
    По умолчанию используется "PullUP" (с поддержкой вариантов написания).
    """
    targets_csv = os.getenv("TARGET_TEAMS", "PullUP")
    targets = [t.strip() for t in targets_csv.split(",") if t.strip()]

    patterns = []
    for team in targets:
        # Универсальная обработка для команд типа PullUP
        # Ищем команды, которые начинаются с "pull" (регистр не важен) и содержат "up"
        if re.match(r"^pull", team, re.IGNORECASE) and "up" in team.lower():
            patterns.extend([
                # Универсальный паттерн: начинается с pull, содержит up, может быть с пробелами/дефисами
                r"pull\s*[-\s]*up",
                r"pull\s*[-\s]*up\s+\w+",
                r"pull\s*[-\s]*up\s*[-\s]*\w+",
                # Также ищем точное название команды
                re.escape(team),
                re.escape(team) + r"\s+\w+",
            ])
        else:
            escaped = re.escape(team)
            patterns.extend([
                escaped,
                fr"{escaped}\s+\w+",
            ])
    return patterns

# Паттерны формируются динамически на основе переменной окружения TARGET_TEAMS
PULLUP_PATTERNS = _build_target_team_patterns()

def find_pullup_team(text_block):
    """Ищет команду PullUP в тексте с универсальной поддержкой вариантов написания"""
    for pattern in PULLUP_PATTERNS:
        matches = re.findall(pattern, text_block, re.IGNORECASE)
        if matches:
            # Возвращаем первое найденное совпадение
            return matches[0].strip()
    return None

def find_target_teams_in_text(text_block: str) -> "list[str]":
    """Возвращает список целевых команд, обнаруженных в тексте (по TARGET_TEAMS)."""
    found = []
    for team in get_target_team_names():
        # Универсальная проверка для PullUP-подобных команд
        if re.match(r"^pull", team, re.IGNORECASE) and "up" in team.lower():
            # Ищем любую комбинацию pull + up
            pattern = r"pull\s*[-\s]*up"
            if re.search(pattern, text_block, re.IGNORECASE):
                found.append(team)
        else:
            # Обычная проверка для других команд
            pattern = re.escape(team)
            if re.search(pattern, text_block, re.IGNORECASE):
                found.append(team)
    # Удаляем дубликаты, сохраняем порядок
    seen = set()
    unique_found = []
    for t in found:
        if t.lower() not in seen:
            unique_found.append(t)
            seen.add(t.lower())
    return unique_found

def get_target_team_names() -> list:
    targets_csv = os.getenv("TARGET_TEAMS", "PullUP")
    return [t.strip() for t in targets_csv.split(",") if t.strip()]

def should_send_game_notification(game_time_str):
    """Проверяет, нужно ли отправить уведомление о игре"""
    try:
        # Парсим время игры
        time_formats = [
            '%d.%m.%Y %H:%M',
            '%Y-%m-%d %H:%M',
            '%d/%m/%Y %H:%M',
            '%H:%M'
        ]
        
        game_datetime = None
        for fmt in time_formats:
            try:
                if ':' in game_time_str and len(game_time_str.split(':')) == 2:
                    # Если указано только время, добавляем сегодняшнюю дату
                    today = datetime.datetime.now().strftime('%Y-%m-%d')
                    time_str_with_date = f"{today} {game_time_str}"
                    game_datetime = datetime.datetime.strptime(time_str_with_date, '%Y-%m-%d %H:%M')
                else:
                    game_datetime = datetime.datetime.strptime(game_time_str, fmt)
                break
            except ValueError:
                continue
        
        if game_datetime:
            now = datetime.datetime.now()
            # Отправляем уведомление за 30 минут до начала игры
            notification_time = game_datetime - datetime.timedelta(minutes=30)
            return now >= notification_time and now <= game_datetime
            
    except Exception as e:
        print(f"❌ Ошибка при проверке времени уведомления: {e}")
        return False

async def parse_game_info(game_url):
    """Парсит информацию о игре с страницы игры"""
    return await game_parser.parse_game_info(game_url)

async def check_game_start(game_info, game_url):
    """Проверяет, нужно ли отправить уведомление о начале игры"""
    try:
        if not game_info or not game_info['time']:
            return
        
        if should_send_game_notification(game_info['time']):
            # Используем общий менеджер уведомлений
            await notification_manager.send_game_start_notification(game_info, game_url)
    except Exception as e:
        print(f"❌ Ошибка при проверке начала игры: {e}")

async def check_letobasket_site():
    """Проверяет сайт letobasket.ru на наличие игр PullUP"""
    try:
        print(f"🔍 Проверяю сайт letobasket.ru...")
        
        # Получаем свежий контент страницы
        html_content = await game_parser.get_fresh_page_content()
        
        # Парсим HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Получаем весь текст страницы
        page_text = soup.get_text()
        
        # Ищем дату на странице
        date_match = re.search(r'(\d{1,2}[./]\d{1,2}[./]\d{2,4})', page_text)
        current_date = date_match.group(1) if date_match else None
        print(f"📅 Дата на странице: {current_date}")
        
        # Ищем все вариации PullUP во всей странице
        pullup_patterns = [
            r'PULL UP ФАРМ',
            r'PULL UP-ФАРМ',
            r'Pull Up-Фарм',
            r'pull up-фарм',
            r'PULL UP',
            r'Pull Up',
            r'pull up',
            r'PullUP Фарм',
            r'PullUP'
        ]
        
        found_pullup_games = []
        used_links = set()  # Множество уже использованных ссылок
        
        # Ищем конкретные игры с PullUP по времени
        pullup_games = [
            {"time": "12.30", "team1": "IT Basket", "team2": "Pull Up"},
            {"time": "14.00", "team1": "Маиле Карго", "team2": "Pull Up"}
        ]
        
        for game in pullup_games:
            game_time = game["time"]
            team1 = game["team1"]
            team2 = game["team2"]
            
            # Ищем эту игру в тексте
            game_pattern = rf'{current_date}\s+{game_time}[^-]*-\s*{re.escape(team1)}[^-]*-\s*{re.escape(team2)}'
            if re.search(game_pattern, page_text, re.IGNORECASE):
                print(f"   🏀 Найдена игра PullUP: {team1} vs {team2} - {game_time}")
                
                # Определяем, какая команда является PullUP
                pullup_team = None
                opponent_team = None
                
                if "pull" in team1.lower() and "up" in team1.lower():
                    pullup_team = team1
                    opponent_team = team2
                elif "pull" in team2.lower() and "up" in team2.lower():
                    pullup_team = team2
                    opponent_team = team1
                
                if pullup_team and opponent_team:
                    # Очищаем название соперника
                    opponent_team = re.sub(r'\s+', ' ', opponent_team).strip()
                    opponent_team = re.sub(r'^[-—\s]+|[-—\s]+$', '', opponent_team).strip()
                    opponent_team = re.sub(r'\s*pull\s*up\s*', '', opponent_team, flags=re.IGNORECASE).strip()
                    opponent_team = re.sub(r'[-—]+', '', opponent_team).strip()
                    
                    # Ищем ссылку на игру в HTML
                    game_link = None
                    
                    # Находим порядок игры на странице
                    game_pattern = rf'{current_date}\s+\d{{2}}\.\d{{2}}[^-]*-\s*[^-]+[^-]*-\s*[^-]+'
                    text_match = re.search(game_pattern, page_text, re.IGNORECASE)
                    
                    if text_match:
                        # Ищем все ссылки на игры
                        game_links = soup.find_all('a', href=True)
                        
                        # Определяем порядок игры
                        game_order = None
                        all_games = re.findall(rf'{current_date}\s+\d{{2}}\.\d{{2}}[^-]*-\s*[^-]+[^-]*-\s*[^-]+', page_text)
                        
                        for i, game_text in enumerate(all_games):
                            if game_time in game_text and team1 in game_text and team2 in game_text:
                                game_order = i + 1
                                break
                        
                        # Получаем ссылку по порядку
                        if game_order and game_order <= len(game_links):
                            game_link = game_links[game_order - 1]['href']
                            if not game_link.startswith('http'):
                                game_link = "http://letobasket.ru/" + game_link.lstrip('/')
                    
                    # Добавляем игру в список найденных
                    found_pullup_games.append({
                        'team': pullup_team,
                        'opponent': opponent_team,
                        'time': game_time,
                        'order': game_order,
                        'link': game_link
                    })
                    
                    # Проверяем, не отправляли ли мы уже уведомление об этой игре
                    game_id = f"pullup_{current_date}_{opponent_team}_{game_time}"
                    
                    if game_id not in used_links:
                        print(f"   📢 Отправляем уведомление о игре: {pullup_team} vs {opponent_team}")
                        
                        # Формируем сообщение
                        message = f"🏀 Найдена игра PullUP!\n\n"
                        message += f"📅 Дата: {current_date}\n"
                        message += f"⏰ Время: {game_time}\n"
                        message += f"🏆 {pullup_team} vs {opponent_team}\n"
                        
                        if game_link:
                            message += f"🔗 Ссылка: {game_link}"
                        
                        # Отправляем уведомление
                        if not DRY_RUN:
                            await bot.send_message(chat_id=CHAT_ID, text=message)
                            print(f"   ✅ Уведомление отправлено")
                        else:
                            print(f"   [DRY_RUN] Уведомление: {message}")
                        
                        used_links.add(game_id)
                        
                        # Парсим информацию об игре и проверяем время начала
                        if game_link:
                            game_info = await parse_game_info(game_link)
                            if game_info:
                                print(f"   📅 Время игры: {game_info.get('time', 'Не найдено')}")
                                print(f"   🏀 Команды: {game_info.get('team1', 'Не найдено')} vs {game_info.get('team2', 'Не найдено')}")
                                
                                # Проверяем, нужно ли отправить уведомление о начале
                                await check_game_start(game_info, game_link)
                                
                                # Проверяем завершение игры
                                await check_game_completion(game_link, game_info)
        
        if not found_pullup_games:
            print("📊 Игры PullUP не найдены на странице")
        else:
            print(f"📊 Найдено игр PullUP: {len(found_pullup_games)}")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке сайта: {e}")

async def main():
    """Основная функция"""
    print("🚀 Запуск мониторинга letobasket.ru")
    
    if DRY_RUN:
        print("🧪 РЕЖИМ ТЕСТИРОВАНИЯ (DRY_RUN)")
    
    try:
        await check_letobasket_site()
        print("✅ Мониторинг завершен")
    except Exception as e:
        print(f"❌ Ошибка в мониторинге: {e}")

if __name__ == "__main__":
    asyncio.run(main())
