#!/usr/bin/env python3
"""
Ручной ввод данных опроса для тестирования
"""

import asyncio
import os
from dotenv import load_dotenv
from training_polls_enhanced import TrainingPollsManager

async def manual_poll_data():
    """Ручной ввод данных опроса"""
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Создаем менеджер
    training_manager = TrainingPollsManager()
    
    print("🔧 РУЧНОЙ ВВОД ДАННЫХ ОПРОСА")
    print("=" * 50)
    
    # Получаем информацию об опросе из Google Sheets
    try:
        worksheet = training_manager.spreadsheet.worksheet("Тренировки")
        all_values = worksheet.get_all_values()
        
        # Ищем активный опрос
        active_polls = []
        for i, row in enumerate(all_values):
            if len(row) > 1 and row[1] and len(row[1]) > 10 and row[1] not in ["Вторник", "Пятница"]:
                active_polls.append({
                    'poll_id': row[1],
                    'date': row[0],
                    'row': i + 1
                })
        
        if active_polls:
            latest_poll = active_polls[-1]
            print(f"📊 Активный опрос: {latest_poll['poll_id']}")
            print(f"📊 Дата: {latest_poll['date']}")
            
            # Ручной ввод данных
            print("\n🔧 РУЧНОЙ ВВОД ДАННЫХ:")
            print("Введите данные участников (формат: Имя Фамилия,день1,день2)")
            print("Дни: 0=Вторник, 1=Пятница, 2=Тренер, 3=Нет")
            print("Пример: Иван Петров,0,1")
            print("Введите 'готово' для завершения")
            
            tuesday_voters = []
            friday_voters = []
            trainer_voters = []
            no_voters = []
            
            while True:
                user_input = input("\nВведите данные участника: ").strip()
                if user_input.lower() == 'готово':
                    break
                
                try:
                    parts = user_input.split(',')
                    if len(parts) < 2:
                        print("❌ Неверный формат. Используйте: Имя Фамилия,день1,день2")
                        continue
                    
                    name = parts[0].strip()
                    days = [int(d.strip()) for d in parts[1:]]
                    
                    print(f"✅ Добавлен: {name} -> дни {days}")
                    
                    if 0 in days:
                        tuesday_voters.append(name)
                    if 1 in days:
                        friday_voters.append(name)
                    if 2 in days:
                        trainer_voters.append(name)
                    if 3 in days:
                        no_voters.append(name)
                        
                except ValueError:
                    print("❌ Ошибка в формате дней. Используйте числа: 0,1,2,3")
                    continue
            
            print(f"\n📊 ИТОГОВЫЕ ДАННЫЕ:")
            print(f"   Вторник: {len(tuesday_voters)} участников")
            print(f"   Пятница: {len(friday_voters)} участников")
            print(f"   Тренер: {len(trainer_voters)} участников")
            print(f"   Нет: {len(no_voters)} участников")
            
            if tuesday_voters:
                print(f"   Участники вторника: {', '.join(tuesday_voters)}")
            if friday_voters:
                print(f"   Участники пятницы: {', '.join(friday_voters)}")
            
            # Сохраняем данные
            save = input("\n💾 Сохранить данные в Google Sheets? (y/n): ").strip().lower()
            if save == 'y':
                try:
                    # Преобразуем данные для сохранения
                    voters_for_sheet = []
                    for voter_name in tuesday_voters:
                        name_parts = voter_name.split()
                        if len(name_parts) >= 2:
                            surname = name_parts[-1]
                            name = ' '.join(name_parts[:-1])
                        else:
                            surname = name_parts[0] if name_parts else "Неизвестный"
                            name = "Неизвестный"
                        
                        voters_for_sheet.append({
                            'surname': surname,
                            'name': name,
                            'telegram_id': voter_name
                        })
                    
                    if voters_for_sheet:
                        training_manager._save_voters_to_sheet("ВТОРНИК", voters_for_sheet, latest_poll['poll_id'])
                        print("✅ Данные за вторник сохранены")
                    
                    # Аналогично для пятницы
                    voters_for_sheet = []
                    for voter_name in friday_voters:
                        name_parts = voter_name.split()
                        if len(name_parts) >= 2:
                            surname = name_parts[-1]
                            name = ' '.join(name_parts[:-1])
                        else:
                            surname = name_parts[0] if name_parts else "Неизвестный"
                            name = "Неизвестный"
                        
                        voters_for_sheet.append({
                            'surname': surname,
                            'name': name,
                            'telegram_id': voter_name
                        })
                    
                    if voters_for_sheet:
                        training_manager._save_voters_to_sheet("ПЯТНИЦА", voters_for_sheet, latest_poll['poll_id'])
                        print("✅ Данные за пятницу сохранены")
                    
                    print("✅ Все данные сохранены в Google Sheets")
                    
                except Exception as e:
                    print(f"❌ Ошибка сохранения: {e}")
            else:
                print("❌ Данные не сохранены")
                
        else:
            print("❌ Активные опросы не найдены")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(manual_poll_data())
