#!/usr/bin/env python3
"""
Общий модуль с BotWrapper для решения проблем с типизацией pyright
"""

from typing import Optional
from telegram import Bot


class BotWrapper:
    """Обертка для бота для решения проблем с типизацией"""
    
    def __init__(self, bot_instance: Bot):
        self._bot = bot_instance
    
    async def send_poll(self, **kwargs):
        """Отправляет опрос"""
        return await self._bot.send_poll(**kwargs)
    
    async def stop_poll(self, **kwargs):
        """Останавливает опрос"""
        return await self._bot.stop_poll(**kwargs)
    
    async def send_message(self, **kwargs):
        """Отправляет сообщение"""
        return await self._bot.send_message(**kwargs)
    
    async def get_chat(self, **kwargs):
        """Получает информацию о чате"""
        return await self._bot.get_chat(**kwargs)


def create_bot_wrapper(bot_token: str) -> BotWrapper:
    """Создает обертку для бота"""
    bot_instance = Bot(token=bot_token)
    return BotWrapper(bot_instance)


def get_bot_wrapper_from_instance(bot_instance: Bot) -> BotWrapper:
    """Создает обертку из существующего экземпляра бота"""
    return BotWrapper(bot_instance)
