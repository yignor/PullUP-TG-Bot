#!/usr/bin/env python3
"""
Получение Telegram ID всех участников группы
"""

import os
import asyncio
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def get_group_members():
    """Получает всех участников группы"""
    print("🔄 ПОЛУЧЕНИЕ УЧАСТНИКОВ ГРУППЫ")
    print("=" * 50)
    
    try:
        from telegram import Bot
        from telegram.error import TelegramError
        
        # Получаем токен бота
        bot_token = os.getenv("BOT_TOKEN")
        chat_id = os.getenv("CHAT_ID")
        
        if not bot_token:
            print("❌ BOT_TOKEN не настроен")
            return False
        
        if not chat_id:
            print("❌ CHAT_ID не настроен")
            return False
        
        print(f"✅ Токен бота: {bot_token[:10]}...")
        print(f"✅ Chat ID: {chat_id}")
        
        # Создаем бота
        bot = Bot(token=bot_token)
        
        # Получаем информацию о чате
        try:
            chat = await bot.get_chat(chat_id)
            print(f"✅ Название группы: {chat.title}")
            print(f"✅ Тип чата: {chat.type}")
        except TelegramError as e:
            print(f"❌ Ошибка получения информации о чате: {e}")
            return False
        
        # Получаем участников группы
        print(f"\n📊 Получаем участников группы...")
        members = []
        
        try:
            # Получаем администраторов группы
            admins = await bot.get_chat_administrators(chat_id)
            print(f"✅ Администраторов: {len(admins)}")
            
            # Получаем всех участников (если бот имеет права)
            try:
                # Пытаемся получить всех участников
                async for member in bot.get_chat_members(chat_id):
                    members.append(member)
                    if len(members) % 10 == 0:
                        print(f"   Загружено: {len(members)} участников...")
                
                print(f"✅ Всего участников: {len(members)}")
                
            except TelegramError as e:
                print(f"⚠️ Не удалось получить всех участников: {e}")
                print("   Показываем только администраторов")
                members = admins
            
        except TelegramError as e:
            print(f"❌ Ошибка получения участников: {e}")
            return False
        
        # Обрабатываем участников
        print(f"\n📋 СПИСОК УЧАСТНИКОВ:")
        print("=" * 80)
        print(f"{'№':<3} {'ID':<12} {'Имя':<20} {'Фамилия':<20} {'Username':<15} {'Статус':<10}")
        print("-" * 80)
        
        for i, member in enumerate(members, 1):
            user = member.user
            
            # Получаем данные пользователя
            user_id = str(user.id)
            first_name = user.first_name or ''
            last_name = user.last_name or ''
            username = f"@{user.username}" if user.username else ''
            
            # Определяем статус
            if member.status == 'creator':
                status = 'Создатель'
            elif member.status == 'administrator':
                status = 'Админ'
            elif member.status == 'member':
                status = 'Участник'
            else:
                status = member.status
            
            print(f"{i:<3} {user_id:<12} {first_name:<20} {last_name:<20} {username:<15} {status:<10}")
        
        # Сохраняем в файл
        print(f"\n💾 Сохраняем данные в файл...")
        with open('group_members.txt', 'w', encoding='utf-8') as f:
            f.write("СПИСОК УЧАСТНИКОВ ГРУППЫ\n")
            f.write("=" * 50 + "\n")
            f.write(f"Группа: {chat.title}\n")
            f.write(f"Дата: {asyncio.get_event_loop().time()}\n\n")
            
            for member in members:
                user = member.user
                f.write(f"ID: {user.id}\n")
                f.write(f"Имя: {user.first_name or ''}\n")
                f.write(f"Фамилия: {user.last_name or ''}\n")
                f.write(f"Username: {user.username or ''}\n")
                f.write(f"Статус: {member.status}\n")
                f.write("-" * 30 + "\n")
        
        print(f"✅ Данные сохранены в файл 'group_members.txt'")
        
        # Показываем статистику
        print(f"\n📊 СТАТИСТИКА:")
        print(f"   Всего участников: {len(members)}")
        
        # Подсчитываем по статусам
        statuses = {}
        for member in members:
            status = member.status
            statuses[status] = statuses.get(status, 0) + 1
        
        for status, count in statuses.items():
            print(f"   {status}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

async def test_bot_connection():
    """Тестирует подключение бота"""
    print("🧪 ТЕСТ ПОДКЛЮЧЕНИЯ БОТА")
    print("=" * 50)
    
    try:
        from telegram import Bot
        
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            print("❌ BOT_TOKEN не настроен")
            return False
        
        bot = Bot(token=bot_token)
        
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        print(f"✅ Бот подключен: {bot_info.first_name}")
        print(f"   Username: @{bot_info.username}")
        print(f"   ID: {bot_info.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения бота: {e}")
        return False

async def main():
    """Основная функция"""
    print("🤖 ПОЛУЧЕНИЕ УЧАСТНИКОВ ГРУППЫ")
    print("=" * 60)
    
    # Тестируем подключение бота
    if not await test_bot_connection():
        print("❌ Не удалось подключиться к боту")
        return
    
    # Получаем участников группы
    success = await get_group_members()
    
    if success:
        print("\n🎉 Участники группы успешно получены!")
        print("Файл 'group_members.txt' содержит полную информацию")
    else:
        print("\n❌ Ошибка при получении участников группы")

if __name__ == "__main__":
    asyncio.run(main())
