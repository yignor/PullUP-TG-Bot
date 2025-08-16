#!/usr/bin/env python3
"""
Основной скрипт для запуска мониторинга результатов игр
Запускается через cron для проверки завершенных игр и отправки уведомлений
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
        logging.FileHandler('game_results_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def monitor_game_results():
    """Мониторит результаты игр и отправляет уведомления"""
    logger.info("Запуск мониторинга результатов игр")
    
    try:
        # Импортируем монитор результатов
        from game_results_monitor import GameResultsMonitor
        
        # Проверяем настройки
        bot_token = os.getenv('BOT_TOKEN')
        chat_id = os.getenv('CHAT_ID')
        
        if not bot_token or not chat_id:
            logger.error("BOT_TOKEN или CHAT_ID не настроены")
            return False
        
        # Создаем экземпляр монитора
        monitor = GameResultsMonitor()
        
        # Запускаем проверку и отправку уведомлений
        await monitor.check_and_notify_game_results()
        
        logger.info("Мониторинг результатов игр завершен")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка мониторинга результатов: {e}")
        return False

async def main():
    """Основная функция"""
    logger.info("Запуск системы мониторинга результатов игр")
    
    try:
        success = await monitor_game_results()
        if success:
            logger.info("Система мониторинга результатов завершена успешно")
        else:
            logger.error("Система мониторинга результатов завершена с ошибками")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
