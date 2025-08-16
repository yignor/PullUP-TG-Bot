#!/usr/bin/env python3
"""
Основной скрипт для сбора результатов голосований по расписанию
Запускается через cron для получения статистики посещаемости
"""

import asyncio
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('schedule_poll_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def collect_schedule_poll_results():
    """Собирает результаты голосований по расписанию"""
    logger.info("Запуск сбора результатов голосований по расписанию")
    
    try:
        # Импортируем обработчик результатов
        from schedule_poll_results import schedule_poll_handler
        
        # Проверяем настройки
        telegram_api_id = os.getenv('TELEGRAM_API_ID')
        telegram_api_hash = os.getenv('TELEGRAM_API_HASH')
        telegram_phone = os.getenv('TELEGRAM_PHONE')
        
        if not all([telegram_api_id, telegram_api_hash, telegram_phone]):
            logger.error("Переменные для Telegram Client API не настроены")
            logger.error("Нужно: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE")
            return False
        
        # Запускаем клиент
        logger.info("Подключение к Telegram Client API...")
        if not await schedule_poll_handler.start_client():
            logger.error("Не удалось подключиться к Telegram Client API")
            return False
        
        # Получаем сводку посещаемости за последние 7 дней
        logger.info("Получение сводки посещаемости...")
        summary = await schedule_poll_handler.get_game_attendance_summary(days_back=7)
        
        if summary:
            logger.info(f"СВОДКА ПОСЕЩАЕМОСТИ:")
            logger.info(f"  Всего игр: {summary['total_games']}")
            logger.info(f"  Всего готовы: {summary['total_ready']}")
            logger.info(f"  Всего не готовы: {summary['total_not_ready']}")
            logger.info(f"  Всего тренер: {summary['total_coach']}")
            
            if summary['games']:
                logger.info("ДЕТАЛИ ПО ИГРАМ:")
                for game in summary['games']:
                    logger.info(f"  {game['opponent']} ({game['date']} {game['time']})")
                    logger.info(f"    Тип: {game['team_type']}")
                    logger.info(f"    Зал: {game['venue']}")
                    logger.info(f"    Готовы: {game['ready']}, Не готовы: {game['not_ready']}, Тренер: {game['coach']}")
                    logger.info(f"    Всего: {game['total']}")
        else:
            logger.warning("Сводка посещаемости не получена")
        
        # Закрываем клиент
        await schedule_poll_handler.close_client()
        
        logger.info("Сбор результатов голосований завершен")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка сбора результатов: {e}")
        return False

async def main():
    """Основная функция"""
    logger.info("Запуск системы сбора результатов голосований по расписанию")
    
    try:
        success = await collect_schedule_poll_results()
        if success:
            logger.info("Система сбора результатов завершена успешно")
        else:
            logger.error("Система сбора результатов завершена с ошибками")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
