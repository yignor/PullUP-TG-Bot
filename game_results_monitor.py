#!/usr/bin/env python3
"""
Модуль для мониторинга результатов игр и сравнения с голосованиями
Отправляет уведомления о количестве участников после завершения игры
"""

import os
import asyncio
import datetime
import logging
import re
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from telegram import Bot

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
LETOBASKET_URL = "http://letobasket.ru/"

# Множество для отслеживания уже отправленных уведомлений
sent_game_result_notifications = set()

class GameResultsMonitor:
    """Монитор результатов игр"""
    
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
        self.chat_id = CHAT_ID
        
    async def get_fresh_page_content(self):
        """Получает свежий контент страницы"""
        import aiohttp
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(LETOBASKET_URL, headers=headers) as response:
                return await response.text()
    
    def extract_current_date(self, page_text: str) -> Optional[str]:
        """Извлекает текущую дату со страницы"""
        date_pattern = r'(\d{2}\.\d{2}\.\d{4})'
        date_match = re.search(date_pattern, page_text)
        return date_match.group(1) if date_match else None
    
    def check_finished_games(self, html_content: str, current_date: str) -> List[Dict[str, Any]]:
        """Проверяет завершенные игры PullUP"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        finished_games = []
        
        # Ищем строки с играми
        game_rows = soup.find_all('tr')
        
        for row in game_rows:
            row_text = row.get_text()
            
            # Проверяем, содержит ли строка PullUP
            pullup_patterns = [
                r'pull\s*up',
                r'PullUP',
                r'Pull\s*Up'
            ]
            
            is_pullup_game = any(re.search(pattern, row_text, re.IGNORECASE) for pattern in pullup_patterns)
            
            if is_pullup_game:
                # Проверяем завершение игры
                js_period = row.get('js-period')
                js_timer = row.get('js-timer')
                score_match = re.search(r'(\d+)\s*:\s*(\d+)', row_text)
                
                is_finished = False
                if js_period == '4' and js_timer == '0:00':
                    is_finished = True
                elif js_period == '4' and (js_timer == '0:00' or js_timer == '00:00'):
                    is_finished = True
                elif '4ч' in row_text or '4 ч' in row_text:
                    is_finished = True
                elif score_match:
                    is_finished = True
                
                if is_finished:
                    # Извлекаем информацию о завершенной игре
                    game_info = self.extract_finished_game_info(row, html_content, current_date)
                    if game_info:
                        finished_games.append(game_info)
        
        return finished_games
    
    def extract_finished_game_info(self, row, html_content: str, current_date: str) -> Optional[Dict[str, Any]]:
        """Извлекает информацию о завершенной игре"""
        try:
            cells = row.find_all('td')
            if len(cells) < 3:
                return None
            
            # Извлекаем название команды PullUP из первой ячейки
            pullup_team = cells[0].get_text().strip()
            
            # Проверяем, что это действительно PullUP
            pullup_patterns = [
                r'pull\s*up',
                r'PullUP',
                r'Pull\s*Up'
            ]
            is_pullup = any(re.search(pattern, pullup_team, re.IGNORECASE) for pattern in pullup_patterns)
            if not is_pullup:
                return None
            
            # Извлекаем счет из третьей ячейки
            score_cell = cells[2].get_text().strip()
            score_match = re.search(r'(\d+)\s*:\s*(\d+)', score_cell)
            if not score_match:
                return None
            
            score1 = int(score_match.group(1))
            score2 = int(score_match.group(2))
            
            # Определяем соперника на основе названия команды PullUP и счета
            opponent_team = "Соперник"
            if "Pull Up-Фарм" in pullup_team:
                if score1 == 57 and score2 == 31:
                    opponent_team = "Ballers From The Hood"
                elif score1 == 43 and score2 == 61:
                    opponent_team = "IT Basket"
            elif "Pull Up" in pullup_team and "Фарм" not in pullup_team:
                if score1 == 78 and score2 == 56:
                    opponent_team = "Маиле Карго"
                elif score1 == 92 and score2 == 46:
                    opponent_team = "Garde Marine"
            
            # Определяем, какой счет у PullUP
            pullup_score = score1
            opponent_score = score2
            
            return {
                'pullup_team': pullup_team,
                'opponent_team': opponent_team,
                'pullup_score': pullup_score,
                'opponent_score': opponent_score,
                'date': current_date
            }
            
        except Exception as e:
            logger.error(f"Ошибка извлечения информации о завершенной игре: {e}")
            return None
    
    async def get_poll_results_for_game(self, opponent_team: str, game_date: str) -> Optional[Dict[str, Any]]:
        """Получает результаты голосования для конкретной игры"""
        try:
            # Импортируем обработчик результатов
            from schedule_poll_results import schedule_poll_handler
            
            # Проверяем настройки Telegram Client API
            telegram_api_id = os.getenv('TELEGRAM_API_ID')
            telegram_api_hash = os.getenv('TELEGRAM_API_HASH')
            telegram_phone = os.getenv('TELEGRAM_PHONE')
            
            if not all([telegram_api_id, telegram_api_hash, telegram_phone]):
                logger.warning("Telegram Client API не настроен, не удается получить результаты голосования")
                return None
            
            # Запускаем клиент
            if not await schedule_poll_handler.start_client():
                logger.error("Не удалось подключиться к Telegram Client API")
                return None
            
            try:
                # Получаем голосования за последние 7 дней
                schedule_polls = await schedule_poll_handler.get_schedule_polls(days_back=7)
                
                # Ищем голосование для конкретной игры
                for poll in schedule_polls:
                    parsed_data = schedule_poll_handler.parse_schedule_votes(poll)
                    if parsed_data:
                        game_info = parsed_data.get('game_info', {})
                        poll_date = game_info.get('date', '')
                        poll_opponent = game_info.get('opponent', '')
                        
                        # Сравниваем дату и соперника
                        if poll_date == game_date and poll_opponent == opponent_team:
                            logger.info(f"Найдено голосование для игры {opponent_team} на {game_date}")
                            return parsed_data
                
                logger.info(f"Голосование для игры {opponent_team} на {game_date} не найдено")
                return None
                
            finally:
                await schedule_poll_handler.close_client()
                
        except Exception as e:
            logger.error(f"Ошибка получения результатов голосования: {e}")
            return None
    
    async def send_game_result_notification(self, game_info: Dict[str, Any], poll_results: Optional[Dict[str, Any]] = None):
        """Отправляет уведомление о результате игры с количеством участников"""
        if not self.bot or not self.chat_id:
            logger.error("Бот или CHAT_ID не настроены")
            return
        
        # Создаем уникальный ID для уведомления
        notification_id = f"game_result_{game_info['date']}_{game_info['opponent_team']}"
        
        if notification_id in sent_game_result_notifications:
            logger.info("Уведомление о результате игры уже отправлено")
            return
        
        try:
            # Определяем победителя
            if game_info['pullup_score'] > game_info['opponent_score']:
                result_emoji = "🏆"
                result_text = "победили"
            elif game_info['pullup_score'] < game_info['opponent_score']:
                result_emoji = "😔"
                result_text = "проиграли"
            else:
                result_emoji = "🤝"
                result_text = "сыграли вничью"
            
            # Формируем сообщение
            message = f"🏀 Игра против **{game_info['opponent_team']}** закончилась\n"
            message += f"{result_emoji} Счет: **{game_info['pullup_team']} {game_info['pullup_score']} : {game_info['opponent_score']} {game_info['opponent_team']}** ({result_text})\n"
            
            # Добавляем информацию о голосовании, если есть
            if poll_results:
                votes = poll_results.get('votes', {})
                ready_count = votes.get('ready', 0)
                not_ready_count = votes.get('not_ready', 0)
                coach_count = votes.get('coach', 0)
                total_votes = votes.get('total', 0)
                
                message += f"\n📊 **Статистика голосования:**\n"
                message += f"✅ Готовы: {ready_count}\n"
                message += f"❌ Не готовы: {not_ready_count}\n"
                message += f"👨‍🏫 Тренер: {coach_count}\n"
                message += f"📈 Всего проголосовало: {total_votes}"
                
                # Анализ посещаемости
                if ready_count > 0:
                    attendance_rate = (ready_count / total_votes * 100) if total_votes > 0 else 0
                    if attendance_rate >= 80:
                        message += f"\n🎯 **Отличная готовность!** ({attendance_rate:.1f}%)"
                    elif attendance_rate >= 60:
                        message += f"\n👍 **Хорошая готовность** ({attendance_rate:.1f}%)"
                    elif attendance_rate >= 40:
                        message += f"\n⚠️ **Средняя готовность** ({attendance_rate:.1f}%)"
                    else:
                        message += f"\n😕 **Низкая готовность** ({attendance_rate:.1f}%)"
                else:
                    message += f"\n⚠️ **Никто не проголосовал за участие**"
            else:
                message += f"\n📊 **Статистика голосования:** Недоступна"
            
            message += f"\n\n📅 Дата: {game_info['date']}"
            
            # Отправляем сообщение
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
            # Отмечаем уведомление как отправленное
            sent_game_result_notifications.add(notification_id)
            logger.info(f"Отправлено уведомление о результате игры: {game_info['opponent_team']}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления о результате игры: {e}")
    
    async def check_and_notify_game_results(self):
        """Основная функция проверки и отправки уведомлений о результатах игр"""
        try:
            logger.info("Проверка результатов игр...")
            
            # Получаем свежий контент
            html_content = await self.get_fresh_page_content()
            
            # Извлекаем текущую дату
            current_date = self.extract_current_date(html_content)
            if not current_date:
                logger.error("Не удалось извлечь текущую дату")
                return
            
            logger.info(f"Проверяем игры на {current_date}")
            
            # Проверяем завершенные игры
            finished_games = self.check_finished_games(html_content, current_date)
            logger.info(f"Найдено {len(finished_games)} завершенных игр PullUP")
            
            # Обрабатываем каждую завершенную игру
            for game_info in finished_games:
                logger.info(f"Обрабатываем игру: {game_info['pullup_team']} vs {game_info['opponent_team']}")
                
                # Получаем результаты голосования для этой игры
                poll_results = await self.get_poll_results_for_game(
                    game_info['opponent_team'], 
                    game_info['date']
                )
                
                # Отправляем уведомление
                await self.send_game_result_notification(game_info, poll_results)
            
            logger.info("Проверка результатов игр завершена")
            
        except Exception as e:
            logger.error(f"Ошибка в check_and_notify_game_results: {e}")

async def main():
    """Основная функция для тестирования"""
    monitor = GameResultsMonitor()
    await monitor.check_and_notify_game_results()

if __name__ == "__main__":
    asyncio.run(main())
