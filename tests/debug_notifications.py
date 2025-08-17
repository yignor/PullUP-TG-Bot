#!/usr/bin/env python3
"""
Тестовый скрипт для отладки уведомлений
Помогает понять, какие уведомления отправляются
"""
import sys
import os
sys.path.append('..')

import asyncio
import logging
from pullup_notifications import PullUPNotificationManager
from notification_manager import notification_manager

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def debug_notifications():
    """Отладочная функция для уведомлений"""
    try:
        logger.info("🔍 ОТЛАДКА УВЕДОМЛЕНИЙ")
        logger.info("=" * 50)
        
        # Создаем менеджер
        manager = PullUPNotificationManager()
        
        # Проверяем время
        from pullup_notifications import should_send_morning_notification
        should_send = should_send_morning_notification()
        logger.info(f"Должно отправляться утреннее уведомление: {'✅ ДА' if should_send else '❌ НЕТ'}")
        
        # Получаем свежий контент
        logger.info("📡 Получение контента...")
        html_content = await manager.get_fresh_page_content()
        
        # Извлекаем текущую дату
        current_date = manager.extract_current_date(html_content)
        logger.info(f"Текущая дата: {current_date}")
        
        # Проверяем завершенные игры
        logger.info("🏀 Поиск завершенных игр...")
        finished_games = manager.check_finished_games(html_content, current_date)
        logger.info(f"Найдено завершенных игр: {len(finished_games)}")
        
        for i, game in enumerate(finished_games, 1):
            logger.info(f"Игра {i}: {game.get('pullup_team', 'N/A')} vs {game.get('opponent_team', 'N/A')}")
        
        # Проверяем предстоящие игры
        logger.info("📅 Поиск предстоящих игр...")
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        page_text = soup.get_text()
        pullup_games = manager.find_pullup_games(page_text, current_date)
        logger.info(f"Найдено предстоящих игр: {len(pullup_games)}")
        
        for i, game in enumerate(pullup_games, 1):
            logger.info(f"Предстоящая игра {i}: {game.get('team', 'N/A')} vs {game.get('opponent', 'N/A')}")
        
        # Проверяем состояние уведомлений
        logger.info("📊 Состояние уведомлений:")
        logger.info(f"  Отправлено уведомлений о завершении: {len(notification_manager.sent_game_end_notifications)}")
        logger.info(f"  Отправлено уведомлений о результатах: {len(notification_manager.sent_game_result_notifications)}")
        logger.info(f"  Отправлено утренних уведомлений: {len(notification_manager.sent_morning_notifications)}")
        
        logger.info("\n" + "=" * 50)
        logger.info("✅ ОТЛАДКА ЗАВЕРШЕНА")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в отладке: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(debug_notifications())
