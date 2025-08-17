#!/usr/bin/env python3
"""
Тестовый скрипт для отладки PullUP Monitor
Помогает понять, какие игры находит система и почему
"""
import sys
import os
sys.path.append('..')

import asyncio
import logging
from game_parser import game_parser

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def debug_pullup_monitor():
    """Отладочная функция для PullUP Monitor"""
    try:
        logger.info("🔍 ОТЛАДКА PULLUP MONITOR")
        logger.info("=" * 50)
        
        # Получаем свежий контент
        logger.info("📡 Получение контента с сайта...")
        html_content = await game_parser.get_fresh_page_content()
        logger.info(f"✅ Контент получен, размер: {len(html_content)} символов")
        
        # Извлекаем текущую дату
        logger.info("📅 Извлечение текущей даты...")
        current_date = game_parser.extract_current_date(html_content)
        if not current_date:
            logger.error("❌ Не удалось извлечь текущую дату")
            return
        logger.info(f"✅ Текущая дата: {current_date}")
        
        # Проверяем завершенные игры
        logger.info("🏀 Поиск завершенных игр PullUP...")
        finished_games = game_parser.check_finished_games(html_content, current_date)
        
        logger.info("=" * 50)
        logger.info("📊 РЕЗУЛЬТАТЫ АНАЛИЗА:")
        logger.info(f"Всего найдено игр: {len(finished_games)}")
        
        if not finished_games:
            logger.info("✅ Завершенных игр PullUP не найдено")
            return
        
        for i, game in enumerate(finished_games, 1):
            logger.info(f"\n🎯 ИГРА #{i}:")
            logger.info(f"   Команда PullUP: {game.get('pullup_team', 'N/A')}")
            logger.info(f"   Соперник: {game.get('opponent_team', 'N/A')}")
            logger.info(f"   Счет: {game.get('pullup_score', 'N/A')}:{game.get('opponent_score', 'N/A')}")
            logger.info(f"   Дата: {game.get('date', 'N/A')}")
            logger.info(f"   Ссылка: {game.get('game_link', 'N/A')}")
        
        logger.info("\n" + "=" * 50)
        logger.info("✅ ОТЛАДКА ЗАВЕРШЕНА")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в отладке: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(debug_pullup_monitor())
