#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы с токеном
Запускается только при наличии BOT_TOKEN
"""
import sys
import os
sys.path.append('..')

import asyncio
import logging
from notification_manager import notification_manager

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_with_token():
    """Тестирует работу с токеном"""
    try:
        logger.info("🔑 ТЕСТИРОВАНИЕ С ТОКЕНОМ")
        logger.info("=" * 50)
        
        # Проверяем наличие токена
        bot_token = os.getenv('BOT_TOKEN')
        chat_id = os.getenv('CHAT_ID')
        
        if not bot_token:
            logger.error("❌ BOT_TOKEN не настроен")
            return
        
        if not chat_id:
            logger.error("❌ CHAT_ID не настроен")
            return
        
        logger.info(f"✅ BOT_TOKEN настроен (длина: {len(bot_token)})")
        logger.info(f"✅ CHAT_ID настроен: {chat_id}")
        
        # Проверяем инициализацию бота
        if not notification_manager.bot:
            logger.error("❌ Бот не инициализирован")
            return
        
        logger.info("✅ Бот инициализирован")
        
        # Отправляем тестовое сообщение
        test_message = "🧪 ТЕСТОВОЕ СООБЩЕНИЕ\n\n✅ Система работает с новым токеном!\n\n🕐 Время: " + str(asyncio.get_event_loop().time())
        
        try:
            await notification_manager.bot.send_message(
                chat_id=chat_id, 
                text=test_message
            )
            logger.info("✅ Тестовое сообщение отправлено успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки тестового сообщения: {e}")
            return
        
        # Проверяем состояние уведомлений
        logger.info("📊 Состояние уведомлений:")
        logger.info(f"  Отправлено уведомлений о завершении: {len(notification_manager.sent_game_end_notifications)}")
        logger.info(f"  Отправлено уведомлений о результатах: {len(notification_manager.sent_game_result_notifications)}")
        logger.info(f"  Отправлено утренних уведомлений: {len(notification_manager.sent_morning_notifications)}")
        
        logger.info("\n" + "=" * 50)
        logger.info("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в тестировании: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_with_token())
