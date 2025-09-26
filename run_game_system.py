#!/usr/bin/env python3
"""
Скрипт для запуска единой системы управления играми
Выполняет последовательно: парсинг → создание опросов → создание анонсов
"""

import asyncio
from game_system_manager import GameSystemManager

async def main():
    """Запускает полную систему управления играми"""
    manager = GameSystemManager()
    await manager.run_full_system()

if __name__ == "__main__":
    asyncio.run(main())
