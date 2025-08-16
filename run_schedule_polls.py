#!/usr/bin/env python3
"""
Основной скрипт для запуска системы голосований по расписанию
Запускается через cron в 10:00 каждый день
"""

import asyncio
import logging
from schedule_polls import SchedulePollsManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('schedule_polls.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция"""
    logger.info("Запуск системы голосований по расписанию")
    
    try:
        manager = SchedulePollsManager()
        await manager.check_and_create_polls()
        logger.info("Система голосований по расписанию завершена")
    except Exception as e:
        logger.error(f"Ошибка в системе голосований: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
