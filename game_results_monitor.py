#!/usr/bin/env python3
"""
Модуль для мониторинга результатов игр и сравнения с голосованиями
Отправляет уведомления о количестве участников после завершения игры
"""

import os
import asyncio
import datetime
import logging
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Импортируем общие модули
from game_parser import game_parser
from notification_manager import notification_manager

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GameResultsMonitor:
    """Монитор результатов игр"""
    
    def __init__(self):
        pass
        
    async def get_fresh_page_content(self):
        """Получает свежий контент страницы"""
        return await game_parser.get_fresh_page_content()
    
    def extract_current_date(self, page_text: str) -> Optional[str]:
        """Извлекает текущую дату со страницы"""
        return game_parser.extract_current_date(page_text)
    
    def check_finished_games(self, html_content: str, current_date: str) -> List[Dict[str, Any]]:
        """Проверяет завершенные игры PullUP"""
        return game_parser.check_finished_games(html_content, current_date)
    
    def extract_finished_game_info(self, row, html_content: str, current_date: str) -> Optional[Dict[str, Any]]:
        """Извлекает информацию о завершенной игре"""
        return game_parser.extract_finished_game_info(row, html_content, current_date)
    
    async def get_poll_results_for_game(self, opponent_team: str, game_date: str) -> Optional[Dict[str, Any]]:
        """Получает результаты голосования для конкретной игры"""
        try:
            # Проверяем настройки Telegram Client API
            telegram_api_id = os.getenv('TELEGRAM_API_ID')
            telegram_api_hash = os.getenv('TELEGRAM_API_HASH')
            telegram_phone = os.getenv('TELEGRAM_PHONE')
            
            if not all([telegram_api_id, telegram_api_hash, telegram_phone]):
                logger.warning("Telegram Client API не настроен, не удается получить результаты голосования")
                return None
            
            # Импортируем обработчик результатов только если API настроен
            from schedule_poll_results import schedule_poll_handler
            
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
        await notification_manager.send_game_result_notification(game_info, poll_results)
    
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
            
            if not finished_games:
                logger.info("Завершенных игр PullUP не найдено")
                return
            
            # Обрабатываем каждую завершенную игру
            for game_info in finished_games:
                # Проверяем, что это реальная игра с валидными данными
                if not game_info.get('pullup_team') or not game_info.get('opponent_team'):
                    logger.warning(f"Пропускаем игру с неполными данными: {game_info}")
                    continue
                
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
