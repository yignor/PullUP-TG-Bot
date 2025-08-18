#!/usr/bin/env python3
"""
Получение Telegram ID всех участников группы (исправленная версия)
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
            
            # Добавляем администраторов в список
            members.extend(admins)
            
            # Примечание: Telegram Bot API не позволяет получать всех участников группы
            # из соображений безопасности. Можно получить только:
            # 1. Администраторов группы
            # 2. Информацию о конкретном пользователе, если он взаимодействовал с ботом
            
            print(f"⚠️ Telegram Bot API ограничения:")
            print(f"   - Можно получить только администраторов группы")
            print(f"   - Для получения всех участников нужны специальные права")
            print(f"   - Или использование Telegram Client API")
            
        except TelegramError as e:
            print(f"❌ Ошибка получения участников: {e}")
            return False
        
        # Обрабатываем участников
        print(f"\n📋 СПИСОК АДМИНИСТРАТОРОВ:")
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
        with open('group_admins.txt', 'w', encoding='utf-8') as f:
            f.write("СПИСОК АДМИНИСТРАТОРОВ ГРУППЫ\n")
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
        
        print(f"✅ Данные сохранены в файл 'group_admins.txt'")
        
        # Показываем статистику
        print(f"\n📊 СТАТИСТИКА:")
        print(f"   Всего администраторов: {len(members)}")
        
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

async def get_all_members_with_client():
    """Получает всех участников с помощью Telegram Client API"""
    print("\n🔄 ПОЛУЧЕНИЕ ВСЕХ УЧАСТНИКОВ (Telegram Client API)")
    print("=" * 60)
    
    try:
        from telethon import TelegramClient
        from telethon.tl.functions.channels import GetParticipantsRequest
        from telethon.tl.types import ChannelParticipantsSearch
        
        # Получаем переменные окружения
        api_id = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")
        phone = os.getenv("TELEGRAM_PHONE")
        chat_id = os.getenv("CHAT_ID")
        
        if not all([api_id, api_hash, phone, chat_id]):
            print("❌ Не все переменные Telegram Client API настроены")
            print("   Нужны: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE")
            return False
        
        print(f"✅ API ID: {api_id}")
        print(f"✅ API Hash: {api_hash[:10]}...")
        print(f"✅ Phone: {phone}")
        print(f"✅ Chat ID: {chat_id}")
        
        # Создаем клиент
        client = TelegramClient('session_name', api_id, api_hash)
        
        # Подключаемся
        await client.start(phone=phone)
        print("✅ Подключение к Telegram успешно")
        
        # Получаем информацию о чате
        chat = await client.get_entity(chat_id)
        print(f"✅ Группа: {chat.title}")
        
        # Получаем всех участников
        print(f"📊 Получаем всех участников...")
        all_participants = []
        
        try:
            participants = await client.get_participants(chat)
            print(f"✅ Получено участников: {len(participants)}")
            
            # Обрабатываем участников
            for participant in participants:
                user_data = {
                    'id': participant.id,
                    'first_name': participant.first_name or '',
                    'last_name': participant.last_name or '',
                    'username': participant.username or '',
                    'phone': participant.phone or '',
                    'status': str(participant.status)
                }
                all_participants.append(user_data)
            
            # Показываем первые 10 участников
            print(f"\n📋 ПЕРВЫЕ 10 УЧАСТНИКОВ:")
            print("=" * 80)
            print(f"{'№':<3} {'ID':<12} {'Имя':<20} {'Фамилия':<20} {'Username':<15}")
            print("-" * 80)
            
            for i, user in enumerate(all_participants[:10], 1):
                user_id = str(user['id'])
                first_name = user['first_name']
                last_name = user['last_name']
                username = f"@{user['username']}" if user['username'] else ''
                
                print(f"{i:<3} {user_id:<12} {first_name:<20} {last_name:<20} {username:<15}")
            
            # Сохраняем в файл
            print(f"\n💾 Сохраняем всех участников в файл...")
            with open('all_group_members.txt', 'w', encoding='utf-8') as f:
                f.write("СПИСОК ВСЕХ УЧАСТНИКОВ ГРУППЫ\n")
                f.write("=" * 50 + "\n")
                f.write(f"Группа: {chat.title}\n")
                f.write(f"Дата: {asyncio.get_event_loop().time()}\n")
                f.write(f"Всего участников: {len(all_participants)}\n\n")
                
                for user in all_participants:
                    f.write(f"ID: {user['id']}\n")
                    f.write(f"Имя: {user['first_name']}\n")
                    f.write(f"Фамилия: {user['last_name']}\n")
                    f.write(f"Username: {user['username']}\n")
                    f.write(f"Телефон: {user['phone']}\n")
                    f.write(f"Статус: {user['status']}\n")
                    f.write("-" * 30 + "\n")
            
            print(f"✅ Данные сохранены в файл 'all_group_members.txt'")
            print(f"📊 Всего участников: {len(all_participants)}")
            
            # Отключаемся
            await client.disconnect()
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка получения участников: {e}")
            await client.disconnect()
            return False
        
    except Exception as e:
        print(f"❌ Ошибка Telegram Client API: {e}")
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
    
    # Получаем администраторов через Bot API
    success = await get_group_members()
    
    if success:
        print("\n✅ Администраторы группы получены!")
    
    # Пытаемся получить всех участников через Client API
    client_success = await get_all_members_with_client()
    
    if client_success:
        print("\n🎉 Все участники группы успешно получены!")
        print("Файлы 'group_admins.txt' и 'all_group_members.txt' содержат информацию")
    else:
        print("\n⚠️ Не удалось получить всех участников через Client API")
        print("Проверьте настройки TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE")

if __name__ == "__main__":
    asyncio.run(main())
