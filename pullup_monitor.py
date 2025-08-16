import asyncio
import time
import logging
from pullup_notifications import PullUPNotificationManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pullup_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def monitor_pullup_games():
    """Постоянный мониторинг игр PullUP"""
    manager = PullUPNotificationManager()
    
    logger.info("Запуск мониторинга игр PullUP")
    
    while True:
        try:
            await manager.check_and_notify()
            logger.info("Проверка завершена, ожидание 5 минут...")
            await asyncio.sleep(300)  # Проверяем каждые 5 минут
            
        except KeyboardInterrupt:
            logger.info("Мониторинг остановлен пользователем")
            break
        except Exception as e:
            logger.error(f"Ошибка в мониторинге: {e}")
            await asyncio.sleep(60)  # При ошибке ждем 1 минуту

if __name__ == "__main__":
    asyncio.run(monitor_pullup_games())
