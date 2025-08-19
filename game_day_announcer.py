#!/usr/bin/env python3
"""
Модуль для анонса игр в день игр
- Проверяет расписание игр
- Отправляет анонсы для игр, которые происходят сегодня
- Интегрируется с существующей системой мониторинга
"""

import os
import asyncio
import datetime
import json
import aiohttp
import re
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from telegram import Bot
from bs4 import BeautifulSoup

# Загружаем переменные окружения
load_dotenv()

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GAMES_TOPIC_ID = os.getenv("GAMES_TOPIC_ID", "1282")
ANNOUNCEMENTS_TOPIC_ID = os.getenv("ANNOUNCEMENTS_TOPIC_ID", "26")
TARGET_TEAMS = os.getenv("TARGET_TEAMS", "PullUP,Pull Up-Фарм")

# Файл для хранения отправленных анонсов
ANNOUNCEMENTS_HISTORY_FILE = "game_day_announcements.json"

def get_moscow_time():
    """Возвращает текущее время в часовом поясе Москвы"""
    moscow_tz = datetime.timezone(datetime.timedelta(hours=3))
    return datetime.datetime.now(moscow_tz)

def load_announcements_history() -> Dict:
    """Загружает историю отправленных анонсов"""
    try:
        if os.path.exists(ANNOUNCEMENTS_HISTORY_FILE):
            with open(ANNOUNCEMENTS_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Ошибка загрузки истории анонсов: {e}")
    return {}

def save_announcements_history(history: Dict):
    """Сохраняет историю отправленных анонсов"""
    try:
        with open(ANNOUNCEMENTS_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Ошибка сохранения истории анонсов: {e}")

def create_announcement_key(game_info: Dict) -> str:
    """Создает уникальный ключ для анонса игры"""
    return f"{game_info['date']}_{game_info['time']}_{game_info['team1']}_{game_info['team2']}"

def get_team_category(team_name: str) -> str:
    """Определяет категорию команды с правильным склонением"""
    if "фарм" in team_name.lower():
        return "фарм состава"
    else:
        return "первого состава"

class GameDayAnnouncer:
    """Анонсер игр в день игр"""
    
    def __init__(self):
        self.bot = None
        self.announcements_history = load_announcements_history()
        self._init_bot()
    
    def _init_bot(self):
        """Инициализация бота"""
        if BOT_TOKEN:
            self.bot = Bot(token=BOT_TOKEN)
            print("✅ Бот инициализирован")
        else:
            print("❌ BOT_TOKEN не настроен")
    
    def get_target_team_names(self) -> List[str]:
        """Получает список целевых команд"""
        return [team.strip() for team in TARGET_TEAMS.split(",") if team.strip()]
    
    def find_target_teams_in_text(self, text_block: str) -> List[str]:
        """Ищет целевые команды в тексте"""
        found = []
        target_teams = self.get_target_team_names()
        
        for team in target_teams:
            # Универсальная проверка для PullUP-подобных команд
            if re.match(r"^pull", team, re.IGNORECASE) and "up" in team.lower():
                pattern = r"pull\s*[-\s]*up"
                if re.search(pattern, text_block, re.IGNORECASE):
                    found.append(team)
            else:
                # Обычная проверка для других команд
                pattern = re.escape(team)
                if re.search(pattern, text_block, re.IGNORECASE):
                    found.append(team)
        
        # Удаляем дубликаты
        seen = set()
        unique_found = []
        for team in found:
            if team.lower() not in seen:
                unique_found.append(team)
                seen.add(team.lower())
        
        return unique_found
    
    def parse_schedule_text(self, text: str) -> List[Dict]:
        """Парсит расписание из текста"""
        games = []
        
        # Паттерн для поиска игр: дата время (место) - команда1 - команда2
        # Пример: 19.08.2025 20.30 (MarvelHall) - Визотек - Old Stars
        pattern = r'(\d{1,2}\.\d{2}\.\d{4})\s+(\d{1,2}\.\d{2})\s+\(([^)]+)\)\s+-\s+([^-]+)\s+-\s+([^-]+)'
        
        matches = re.findall(pattern, text)
        
        for match in matches:
            date_str, time_str, venue, team1, team2 = match
            
            # Формируем полное время
            full_time = f"{date_str} {time_str}"
            
            # Очищаем названия команд
            team1 = team1.strip()
            team2 = team2.strip()
            
            game_info = {
                'date': date_str,
                'time': time_str,  # Только время без даты
                'venue': venue.strip(),
                'team1': team1,
                'team2': team2,
                'full_text': f"{full_time} ({venue}) - {team1} - {team2}"
            }
            
            games.append(game_info)
        
        # Также ищем игры в формате табло (если есть)
        # Паттерн для табло: команда1 vs команда2
        scoreboard_pattern = r'([А-ЯЁA-Z\s-]+)\s+vs\s+([А-ЯЁA-Z\s-]+)'
        scoreboard_matches = re.findall(scoreboard_pattern, text)
        
        for match in scoreboard_matches:
            team1, team2 = match
            team1 = team1.strip()
            team2 = team2.strip()
            
            # Если это не дубликат уже найденной игры
            if not any(g['team1'] == team1 and g['team2'] == team2 for g in games):
                game_info = {
                    'date': datetime.datetime.now().strftime('%d.%m.%Y'),
                    'time': '20.30',  # Время по умолчанию
                    'venue': 'MarvelHall',  # Место по умолчанию
                    'team1': team1,
                    'team2': team2,
                    'full_text': f"Табло: {team1} vs {team2}"
                }
                games.append(game_info)
        
        return games
    
    async def fetch_letobasket_schedule(self) -> List[Dict]:
        """Получает расписание игр с сайта letobasket.ru"""
        try:
            url = "http://letobasket.ru"
            
            print(f"🌐 Получение данных с {url}...")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        print(f"❌ Ошибка получения страницы: {response.status}")
                        return []
                    
                    html = await response.text()
                    print(f"✅ Страница получена, размер: {len(html)} символов")
            
            # Парсим HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Ищем таблицы с расписанием
            tables = soup.find_all('table')
            
            all_games = []
            
            for table in tables:
                # Получаем весь текст таблицы
                table_text = table.get_text()
                
                # Парсим игры из текста таблицы
                games = self.parse_schedule_text(table_text)
                
                if games:
                    print(f"📊 Найдено {len(games)} игр в таблице")
                    all_games.extend(games)
            
            # Удаляем дубликаты
            unique_games = []
            seen_games = set()
            
            for game in all_games:
                game_key = create_announcement_key(game)
                if game_key not in seen_games:
                    unique_games.append(game)
                    seen_games.add(game_key)
            
            print(f"📊 Всего найдено {len(unique_games)} уникальных игр")
            return unique_games
            
        except Exception as e:
            print(f"❌ Ошибка получения расписания: {e}")
            return []
    
    async def find_game_link(self, team1: str, team2: str, game_position: int = 1) -> Optional[str]:
        """Находит ссылку на игру по позиции в табло"""
        try:
            url = "http://letobasket.ru"
            
            print(f"🔍 Поиск ссылки на игру: {team1} vs {team2} (позиция {game_position})")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        print(f"❌ Ошибка получения страницы: {response.status}")
                        return None
                    
                    html = await response.text()
            
            # Парсим HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Ищем все ссылки на странице
            all_links = soup.find_all('a', href=True)
            
            print(f"🔍 Анализируем {len(all_links)} ссылок на странице...")
            
            # Ищем ссылки "СТРАНИЦА ИГРЫ" в порядке их появления на странице
            game_page_links = []
            for link in all_links:
                href = link.get('href', '')
                link_text = link.get_text().strip()
                link_text_lower = link_text.lower()
                
                if 'страница игры' in link_text_lower and href:
                    game_page_links.append({
                        'href': href,
                        'text': link_text,
                        'position': len(game_page_links) + 1
                    })
                    print(f"🔗 Найдена ссылка 'СТРАНИЦА ИГРЫ' #{len(game_page_links)}: {link_text} -> {href}")
            
            # Возвращаем ссылку по позиции (если позиция указана и существует)
            if game_position <= len(game_page_links):
                selected_link = game_page_links[game_position - 1]
                print(f"✅ Выбрана ссылка 'СТРАНИЦА ИГРЫ' #{game_position}: {selected_link['href']}")
                return selected_link['href']
            elif game_page_links:
                # Если позиция не указана или неверная, возвращаем первую
                first_link = game_page_links[0]
                print(f"✅ Возвращена первая ссылка 'СТРАНИЦА ИГРЫ': {first_link['href']}")
                return first_link['href']
            else:
                print("❌ Ссылки 'СТРАНИЦА ИГРЫ' не найдены")
                return None
                
        except Exception as e:
            print(f"❌ Ошибка поиска ссылки на игру: {e}")
            return None
    
    def is_game_today(self, game_info: Dict) -> bool:
        """Проверяет, происходит ли игра сегодня"""
        try:
            game_date = datetime.datetime.strptime(game_info['date'], '%d.%m.%Y').date()
            today = get_moscow_time().date()
            return game_date == today
        except Exception as e:
            print(f"❌ Ошибка проверки даты игры: {e}")
            return False
    
    def should_send_announcement(self, game_info: Dict) -> bool:
        """Проверяет, нужно ли отправить анонс для игры"""
        # Создаем уникальный ключ для игры
        announcement_key = create_announcement_key(game_info)
        
        # Проверяем, не отправляли ли мы уже анонс для этой игры
        if announcement_key in self.announcements_history:
            print(f"⏭️ Анонс для игры {announcement_key} уже отправлен")
            return False
        
        # Проверяем, происходит ли игра сегодня
        if not self.is_game_today(game_info):
            print(f"📅 Игра {game_info['date']} не сегодня")
            return False
        
        # Проверяем, есть ли наши команды в игре
        game_text = f"{game_info.get('team1', '')} {game_info.get('team2', '')}"
        target_teams = self.find_target_teams_in_text(game_text)
        
        if not target_teams:
            print(f"ℹ️ Игра без наших команд: {game_info.get('team1', '')} vs {game_info.get('team2', '')}")
            return False
        
        print(f"✅ Игра {game_info['date']} подходит для анонса (сегодня)")
        return True
    
    def format_announcement_message(self, game_info: Dict, game_link: Optional[str] = None) -> str:
        """Форматирует сообщение анонса игры"""
        # Определяем нашу команду и соперника
        team1 = game_info.get('team1', '')
        team2 = game_info.get('team2', '')
        
        if "pull" in team1.lower() and "up" in team1.lower():
            our_team = team1
            opponent = team2
        elif "pull" in team2.lower() and "up" in team2.lower():
            our_team = team2
            opponent = team1
        else:
            # Если не нашли PullUP, используем первую команду как нашу
            our_team = team1
            opponent = team2
        
        # Определяем категорию команды
        team_category = get_team_category(our_team)
        
        # Формируем сообщение анонса в новом формате с эмодзи
        announcement = f"🏀 Сегодня игра {team_category} против {opponent} в {game_info['venue']}.\n"
        announcement += f"🕐 Время игры: {game_info['time']}."
        
        # Добавляем ссылку на игру, если найдена
        if game_link:
            # Формируем полный URL
            if game_link.startswith('game.html?'):
                full_url = f"http://letobasket.ru/{game_link}"
            else:
                full_url = game_link
            announcement += f"\n🔗 Ссылка на игру: <a href=\"{full_url}\">тут</a>"
        
        return announcement
    
    async def send_game_announcement(self, game_info: Dict, game_position: int = 1) -> bool:
        """Отправляет анонс игры"""
        if not self.bot or not CHAT_ID:
            print("❌ Бот или CHAT_ID не настроены")
            return False
        
        try:
            # Ищем ссылку на игру по позиции
            team1 = game_info.get('team1', '')
            team2 = game_info.get('team2', '')
            game_link = await self.find_game_link(team1, team2, game_position)
            
            # Формируем сообщение анонса
            announcement_text = self.format_announcement_message(game_info, game_link)
            
            # Отправляем сообщение в основной топик (без указания топика)
            message = await self.bot.send_message(
                chat_id=int(CHAT_ID),
                text=announcement_text,
                parse_mode='HTML'
            )
            
            # Сохраняем информацию об анонсе
            announcement_key = create_announcement_key(game_info)
            announcement_info = {
                'message_id': message.message_id,
                'text': announcement_text,
                'game_info': game_info,
                'game_link': game_link,
                'game_position': game_position,
                'date': get_moscow_time().isoformat(),
                'chat_id': CHAT_ID,
                'topic_id': 'main'  # Основной топик
            }
            
            # Сохраняем в историю
            self.announcements_history[announcement_key] = announcement_info
            save_announcements_history(self.announcements_history)
            
            print(f"✅ Анонс игры отправлен")
            print(f"📊 ID сообщения: {message.message_id}")
            print(f"📅 Дата: {game_info['date']}")
            print(f"🕐 Время: {game_info['time']}")
            print(f"📍 Место: {game_info['venue']}")
            print(f"🎯 Позиция в табло: {game_position}")
            if game_link:
                print(f"🔗 Ссылка: {game_link}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка отправки анонса игры: {e}")
            return False
    
    async def check_and_send_game_announcements(self):
        """Проверяет расписание и отправляет анонсы для игр сегодня"""
        try:
            print("🔍 Проверка расписания игр на сегодня...")
            
            # Получаем расписание
            games = await self.fetch_letobasket_schedule()
            
            if not games:
                print("⚠️ Игры не найдены")
                return
            
            # Показываем все найденные игры
            print(f"\n📊 НАЙДЕННЫЕ ИГРЫ:")
            for i, game in enumerate(games, 1):
                print(f"   {i}. {game['full_text']}")
            
            # Проверяем каждую игру
            sent_announcements = 0
            for game in games:
                print(f"\n🏀 Проверка игры: {game.get('team1', '')} vs {game.get('team2', '')}")
                
                if self.should_send_announcement(game):
                    print(f"📢 Отправляю анонс для игры...")
                    if await self.send_game_announcement(game):
                        sent_announcements += 1
            
            print(f"\n📊 ИТОГО: Отправлено {sent_announcements} анонсов")
            
        except Exception as e:
            print(f"❌ Ошибка проверки расписания игр: {e}")

# Глобальный экземпляр
game_announcer = GameDayAnnouncer()

async def main():
    """Основная функция"""
    print("📢 АНОНСЕР ИГР В ДЕНЬ ИГР")
    print("=" * 60)
    
    moscow_tz = datetime.timezone(datetime.timedelta(hours=3))
    now = datetime.datetime.now(moscow_tz)
    print(f"🕐 Текущее время (Москва): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 День недели: {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'][now.weekday()]}")
    
    # Проверяем переменные окружения
    bot_token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    
    print("🔧 ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ:")
    print(f"BOT_TOKEN: {'✅' if bot_token else '❌'}")
    print(f"CHAT_ID: {'✅' if chat_id else '❌'}")
    print(f"ANNOUNCEMENTS_TOPIC_ID: {ANNOUNCEMENTS_TOPIC_ID}")
    print(f"TARGET_TEAMS: {TARGET_TEAMS}")
    
    if not all([bot_token, chat_id]):
        print("❌ Не все переменные окружения настроены")
        return
    
    print(f"✅ CHAT_ID: {chat_id}")
    
    # Показываем историю анонсов
    print(f"\n📋 ИСТОРИЯ ОТПРАВЛЕННЫХ АНОНСОВ:")
    if game_announcer.announcements_history:
        for announcement_key, announcement_info in game_announcer.announcements_history.items():
            print(f"   🏀 {announcement_key}")
            print(f"      📊 ID: {announcement_info.get('message_id', 'N/A')}")
            print(f"      📅 Дата отправки: {announcement_info.get('date', 'N/A')}")
    else:
        print("   📝 История пуста")
    
    # Запускаем проверку
    print("\n🔄 Запуск проверки расписания игр на сегодня...")
    await game_announcer.check_and_send_game_announcements()

if __name__ == "__main__":
    asyncio.run(main())
