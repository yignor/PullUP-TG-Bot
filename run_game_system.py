#!/usr/bin/env python3
"""
Скрипт для запуска единой системы управления играми
Выполняет последовательно: парсинг → создание опросов → создание анонсов
"""

import asyncio
from game_system_manager import game_system_manager

async def main():
    """Запускает полную систему управления играми"""
    await game_system_manager.run_full_system()

if __name__ == "__main__":
    asyncio.run(main())
