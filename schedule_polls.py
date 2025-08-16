#!/usr/bin/env python3
"""
Модуль для создания голосований по расписанию игр PullUP
"""

import asyncio
import os
import re
import json
import logging
from datetime import datetime, time
from bs4 import BeautifulSoup
import aiohttp
from telegram import Bot
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LETOBASKET_URL = "http://letobasket.ru/"
POLLS_FILE = "schedule_polls.json"

class SchedulePollsManager:
    """Менеджер для создания голосований по расписанию"""
    
    def __init__(self):
        self.bot = Bot(token=os.getenv('BOT_TOKEN')) if os.getenv('BOT_TOKEN') else None
        self.chat_id = os.getenv('CHAT_ID')
        self.topic_id = "1282"  # Топик для голосований
        self.created_polls = self.load_created_polls()
    
    def load_created_polls(self):
        """Загружает список уже созданных голосований"""
        try:
            if os.path.exists(POLLS_FILE):
                with open(POLLS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки созданных голосований: {e}")
        return {}
    
    def save_created_polls(self):
        """Сохраняет список созданных голосований"""
        try:
            with open(POLLS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.created_polls, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения созданных голосований: {e}")
    
    def get_poll_id(self, game):
        """Создает уникальный ID для голосования"""
        return f"{game['date']}_{game['opponent_team']}_{game['pullup_team']}"
    
    def is_poll_created(self, game):
        """Проверяет, было ли уже создано голосование для этой игры"""
        poll_id = self.get_poll_id(game)
        return poll_id in self.created_polls
    
    def mark_poll_created(self, game, message_id):
        """Отмечает голосование как созданное"""
        poll_id = self.get_poll_id(game)
        self.created_polls[poll_id] = {
            'date': game['date'],
            'opponent': game['opponent_team'],
            'pullup_team': game['pullup_team'],
            'message_id': message_id,
            'created_at': datetime.now().isoformat()
        }
        self.save_created_polls()
    
    async def get_fresh_page_content(self):
        """Получает свежий контент страницы"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(LETOBASKET_URL, headers=headers) as response:
                return await response.text()
    
    def parse_schedule(self, html_content):
        """Парсит расписание игр"""
        soup = BeautifulSoup(html_content, 'html.parser')
        schedule_text = soup.get_text()
        
        # Ищем все строки с расписанием
        schedule_pattern = r'\d{2}\.\d{2}\.\d{4}\s+\d{2}\.\d{2}\s*\([^)]+\)\s*-\s*[^-]+[^-]*-\s*[^-]+'
        schedule_matches = re.findall(schedule_pattern, schedule_text)
        
        pullup_games = []
        
        for match in schedule_matches:
            # Проверяем, содержит ли запись PullUP
            pullup_patterns = [
                r'pull\s*up',
                r'PullUP',
                r'Pull\s*Up'
            ]
            
            is_pullup_game = any(re.search(pattern, match, re.IGNORECASE) for pattern in pullup_patterns)
            
            if is_pullup_game:
                # Парсим дату и время
                date_time_match = re.search(r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}\.\d{2})', match)
                if date_time_match:
                    date_str = date_time_match.group(1)
                    time_str = date_time_match.group(2)
                    
                    # Конвертируем дату для получения дня недели
                    try:
                        date_obj = datetime.strptime(date_str, '%d.%m.%Y')
                        weekday_names = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
                        weekday = weekday_names[date_obj.weekday()]
                    except:
                        weekday = "Неизвестно"
                
                # Парсим адрес зала
                venue_match = re.search(r'\(([^)]+)\)', match)
                venue = venue_match.group(1) if venue_match else "Не указан"
                
                # Парсим команды - используем упрощенный подход
                pullup_match = re.search(r'Pull\s*Up', match, re.IGNORECASE)
                if pullup_match:
                    # Ищем команду перед Pull Up
                    opponent_match = re.search(r'-\s*([^-]+?)(?:\s*-\s*Pull\s*Up)', match, re.IGNORECASE)
                    if opponent_match:
                        opponent_team = opponent_match.group(1).strip()
                        pullup_team = "Pull Up"
                        
                        pullup_games.append({
                            'date': date_str if date_time_match else None,
                            'time': time_str if date_time_match else None,
                            'weekday': weekday,
                            'venue': venue,
                            'pullup_team': pullup_team,
                            'opponent_team': opponent_team,
                            'full_text': match.strip()
                        })
        
        return pullup_games
    
    def create_poll_title(self, game):
        """Создает название голосования"""
        # Определяем тип команды
        if "Pull Up-Фарм" in game['pullup_team']:
            team_type = "развитие"
        else:
            team_type = "первый состав"
        
        # Формируем название
        title = f"Летняя лига, {team_type}, {game['opponent_team']}: {game['weekday']} ({game['date'][:8]}) {game['time']}, {game['venue']}"
        
        return title
    
    async def create_poll_for_game(self, game):
        """Создает голосование для конкретной игры"""
        if not self.bot or not self.chat_id:
            logger.error("Бот или CHAT_ID не настроены")
            return False
        
        # Проверяем, не было ли уже создано голосование
        if self.is_poll_created(game):
            logger.info(f"Голосование для игры {game['opponent_team']} на {game['date']} уже создано")
            return False
        
        try:
            # Создаем название голосования
            poll_title = self.create_poll_title(game)
            
            # Варианты ответов
            poll_options = [
                "✅ Готов",
                "❌ Нет", 
                "👨‍🏫 Тренер"
            ]
            
            # Создаем голосование
            poll = await self.bot.send_poll(
                chat_id=self.chat_id,
                question=poll_title,
                options=poll_options,
                allows_multiple_answers=False,  # Единственный выбор
                is_anonymous=False,  # Открытое голосование
                message_thread_id=int(self.topic_id)
            )
            
            # Отмечаем голосование как созданное
            self.mark_poll_created(game, poll.message_id)
            
            logger.info(f"Создано голосование для игры {game['opponent_team']} на {game['date']} (ID: {poll.message_id})")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка создания голосования для игры {game['opponent_team']}: {e}")
            return False
    
    async def check_and_create_polls(self):
        """Проверяет расписание и создает голосования в 10 утра"""
        try:
            # Проверяем текущее время
            current_time = datetime.now().time()
            if not (time(10, 0) <= current_time <= time(10, 5)):  # Только в 10:00-10:05
                logger.info("Не время для создания голосований (только в 10:00-10:05)")
                return
            
            logger.info("Проверяем расписание для создания голосований...")
            
            # Получаем расписание
            html_content = await self.get_fresh_page_content()
            pullup_games = self.parse_schedule(html_content)
            
            logger.info(f"Найдено {len(pullup_games)} игр PullUP в расписании")
            
            # Создаем голосования для новых игр
            created_count = 0
            for game in pullup_games:
                if await self.create_poll_for_game(game):
                    created_count += 1
            
            logger.info(f"Создано {created_count} новых голосований")
            
        except Exception as e:
            logger.error(f"Ошибка в check_and_create_polls: {e}")

async def main():
    """Основная функция для тестирования"""
    manager = SchedulePollsManager()
    await manager.check_and_create_polls()

if __name__ == "__main__":
    asyncio.run(main())
