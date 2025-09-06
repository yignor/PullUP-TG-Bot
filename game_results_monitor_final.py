#!/usr/bin/env python3
"""
Финальная система мониторинга результатов игр
Production версия для ежедневного запуска
"""

import asyncio
import os
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv
from telegram import Bot
from datetime_utils import get_moscow_time
from game_system_manager import GameSystemManager
from enhanced_duplicate_protection import duplicate_protection, TEST_MODE

# Централизованная загрузка переменных окружения
def load_environment():
    """Загружает переменные окружения с обработкой ошибок"""
    try:
        load_dotenv()
        print("✅ .env файл загружен успешно")
    except Exception as e:
        print(f"⚠️ Ошибка загрузки .env файла: {e}")
        print("📋 Продолжаем работу с переменными окружения из системы")

# Загружаем переменные окружения
load_environment()

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ANNOUNCEMENTS_TOPIC_ID = os.getenv("ANNOUNCEMENTS_TOPIC_ID")

print(f"🔧 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
print(f"   BOT_TOKEN: {'✅' if BOT_TOKEN else '❌'}")
print(f"   CHAT_ID: {'✅' if CHAT_ID else '❌'}")
print(f"   ANNOUNCEMENTS_TOPIC_ID: {'✅' if ANNOUNCEMENTS_TOPIC_ID else '❌'}")

class GameResultsMonitorFinal:
    """Финальная система мониторинга результатов игр"""
    
    def __init__(self):
        self.bot = None
        if BOT_TOKEN:
            self.bot = Bot(token=BOT_TOKEN)
        
        # Создаем экземпляр менеджера игр
        self.game_manager = GameSystemManager()
        
        # Файл для истории отправленных результатов
        self.results_history_file = "game_results_history.json"
        self.results_history = self.load_results_history()
        
        # Если файл не существует, создаем его с базовой структурой
        if not os.path.exists(self.results_history_file):
            print(f"📁 Создаем новый файл истории: {self.results_history_file}")
            self.save_results_history()
    
    def load_results_history(self) -> Dict:
        """Загружает историю отправленных результатов"""
        try:
            if os.path.exists(self.results_history_file):
                with open(self.results_history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    print(f"✅ Загружена история результатов: {len(history)} записей")
                    return history
            else:
                print(f"📁 Файл истории результатов не найден: {self.results_history_file}")
        except Exception as e:
            print(f"⚠️ Ошибка загрузки истории результатов: {e}")
        print(f"📋 Возвращаем пустую историю результатов")
        return {}
    
    def save_results_history(self):
        """Сохраняет историю отправленных результатов"""
        try:
            with open(self.results_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.results_history, f, ensure_ascii=False, indent=2)
            print(f"✅ Сохранена история результатов: {len(self.results_history)} записей в {self.results_history_file}")
        except Exception as e:
            print(f"⚠️ Ошибка сохранения истории результатов: {e}")
    
    def create_result_key(self, game_info: Dict) -> str:
        """Создает уникальный ключ для результата игры"""
        # Нормализуем названия команд для избежания дублирования
        team1 = game_info['team1'].strip().replace(' ', '_')
        team2 = game_info['team2'].strip().replace(' ', '_')
        date = game_info['date']
        
        key = f"result_{date}_{team1}_{team2}"
        print(f"🔑 Создан ключ результата: {key}")
        return key
    
    def was_result_sent(self, game_info: Dict) -> bool:
        """Проверяет, был ли уже отправлен результат для данной игры"""
        result_key = self.create_result_key(game_info)
        was_sent = result_key in self.results_history
        
        if was_sent:
            print(f"⏭️ Результат уже отправлен ранее: {result_key}")
            if result_key in self.results_history:
                sent_time = self.results_history[result_key].get('date', 'неизвестно')
                print(f"   📅 Время отправки: {sent_time}")
        else:
            print(f"✅ Результат еще не отправлялся: {result_key}")
        
        return was_sent
    
    def should_check_results(self) -> bool:
        """Проверяет, нужно ли проверять результаты по новому расписанию"""
        now = get_moscow_time()
        current_hour = now.hour
        current_minute = now.minute
        weekday = now.weekday()  # 0=Понедельник, 6=Воскресенье
        
        # Проверяем, что минуты кратны 15 (0, 15, 30, 45)
        if current_minute % 15 != 0:
            return False
        
        # Будни (Понедельник-Пятница, 0-4)
        if weekday <= 4:  # Понедельник-Пятница
            # Проверяем время с 19:30 до 00:30 (следующий день)
            if current_hour == 19 and current_minute >= 30:  # 19:30-19:59
                return True
            elif current_hour == 0 and current_minute <= 30:  # 00:00-00:30
                return True
            elif current_hour >= 20:  # 20:00-23:59
                return True
            return False
        
        # Выходные (Суббота-Воскресенье, 5-6)
        else:  # Суббота-Воскресенье
            # Проверяем время с 11:30 до 00:30 (следующий день)
            if current_hour == 11 and current_minute >= 30:  # 11:30-11:59
                return True
            elif current_hour == 0 and current_minute <= 30:  # 00:00-00:30
                return True
            elif current_hour >= 12:  # 12:00-23:59
                return True
            return False
    
    async def fetch_game_results(self) -> List[Dict]:
        """Получает результаты игр с сайта letobasket.ru"""
        try:
            import aiohttp
            from bs4 import BeautifulSoup
            
            url = "http://letobasket.ru/"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Получаем весь текст страницы
                        full_text = soup.get_text()
                        
                        # Ищем завершенные игры с нашими командами
                        games = []
                        
                        # Правильный паттерн для результатов игр на сайте
                        # Формат: дата - команда1 - команда2 счет (четверти)
                        # Пример: 23.08.2025- Quasar - Pull Up-Фарм 37:58 (0:12 11:10 15:10 11:26)
                        game_pattern = r'(\d{2}\.\d{2}\.\d{4})-\s*([^-]+)-\s*([^-]+)\s+(\d+):(\d+)\s+\(([^)]+)\)'
                        matches = re.findall(game_pattern, full_text)
                        
                        print(f"🔍 Найдено {len(matches)} потенциальных игр в тексте")
                        
                        for match in matches:
                            date, team1, team2, score1, score2, quarters = match
                            game_text = f"{team1.strip()} {team2.strip()}"
                            
                            # Проверяем, есть ли наши команды
                            if self.game_manager.find_target_teams_in_text(game_text):
                                # Проверяем, что игра сегодняшняя
                                if self.game_manager.is_game_today({'date': date}):
                                    # Определяем нашу команду и соперника
                                    our_team = None
                                    opponent = None
                                    team_type = None
                                    
                                    if any(target_team in team1 for target_team in ['Pull Up', 'PullUP']):
                                        our_team = team1.strip()
                                        opponent = team2.strip()
                                    elif any(target_team in team2 for target_team in ['Pull Up', 'PullUP']):
                                        our_team = team2.strip()
                                        opponent = team1.strip()
                                    
                                    if our_team:
                                        # Определяем тип команды
                                        if 'фарм' in our_team.lower():
                                            team_type = 'состав развития'
                                        else:
                                            team_type = 'первый состав'
                                        
                                        # Определяем результат
                                        our_score = int(score1) if our_team == team1.strip() else int(score2)
                                        opponent_score = int(score2) if our_team == team1.strip() else int(score1)
                                        result = "победа" if our_score > opponent_score else "поражение" if our_score < opponent_score else "ничья"
                                        
                                        game_info = {
                                            'date': date,
                                            'team1': team1.strip(),
                                            'team2': team2.strip(),
                                            'score1': int(score1),
                                            'score2': int(score2),
                                            'quarters': quarters,
                                            'our_team': our_team,
                                            'opponent': opponent,
                                            'team_type': team_type,
                                            'our_score': our_score,
                                            'opponent_score': opponent_score,
                                            'result': result,
                                            'is_finished': True
                                        }
                                        
                                        games.append(game_info)
                                        print(f"🏀 Найдена завершенная игра: {team1.strip()} vs {team2.strip()} ({score1}:{score2})")
                                        print(f"   Дата: {date}, Тип: {team_type}, Результат: {result}")
                                        print(f"   Четверти: {quarters}")
                                else:
                                    print(f"⏭️ Игра {team1.strip()} vs {team2.strip()} не сегодняшняя ({date}), пропускаем")
                        
                        return games
                    else:
                        print(f"❌ Ошибка получения страницы: {response.status}")
                        return []
                        
        except Exception as e:
            print(f"❌ Ошибка получения результатов: {e}")
            return []
    
    async def find_game_link(self, team1: str, team2: str) -> Optional[str]:
        """Ищет ссылку на игру по командам (использует логику из game_system_manager)"""
        try:
            result = await self.game_manager.find_game_link(team1, team2)
            if result:
                game_link, found_team = result
                return game_link
            return None
        except Exception as e:
            print(f"❌ Ошибка поиска ссылки на игру: {e}")
            return None
    
    async def send_game_result(self, game_info: Dict) -> bool:
        """Отправляет результат игры в Telegram"""
        if not self.bot or not CHAT_ID:
            print("❌ Бот не инициализирован или CHAT_ID не настроен")
            return False
        
        try:
            # Проверяем, не отправляли ли мы уже этот результат
            print(f"🔍 Проверяем историю для игры: {game_info['team1']} vs {game_info['team2']}")
            if self.was_result_sent(game_info):
                print(f"⏭️ Результат для игры {game_info['team1']} vs {game_info['team2']} уже отправлен")
                return False
            
            # Формируем сообщение о результате
            result_emoji = "🏆" if game_info['result'] == "победа" else "😔" if game_info['result'] == "поражение" else "🤝"
            
            message = f"{result_emoji} <b>РЕЗУЛЬТАТ ИГРЫ</b>\n\n"
            message += f"🏀 <b>{game_info['team_type'].title()}</b>\n"
            message += f"📅 {game_info['date']}\n"
            message += f"⚔️ {game_info['our_team']} vs {game_info['opponent']}\n"
            message += f"📊 Счет: <b>{game_info['our_score']}:{game_info['opponent_score']}</b>\n"
            message += f"🎯 Результат: <b>{game_info['result'].upper()}</b>\n"
            message += f"📈 Четверти: {game_info['quarters']}"
            
            # Ищем ссылку на игру
            game_link = await self.find_game_link(game_info['team1'], game_info['team2'])
            if game_link:
                message += f"\n\n🔗 <a href='{game_link}'>Страница игры</a>"
            
            # Отправляем сообщение
            try:
                if ANNOUNCEMENTS_TOPIC_ID:
                    message_thread_id = int(ANNOUNCEMENTS_TOPIC_ID)
                    # Используем более явный вызов метода
                    bot_instance = self.bot
                    sent_message = await bot_instance.send_message(
                        chat_id=int(CHAT_ID),
                        text=message,
                        parse_mode='HTML',
                        message_thread_id=message_thread_id
                    )
                else:
                    # Используем более явный вызов метода
                    bot_instance = self.bot
                    sent_message = await bot_instance.send_message(
                        chat_id=int(CHAT_ID),
                        text=message,
                        parse_mode='HTML'
                    )
            except Exception as topic_error:
                print(f"⚠️ Ошибка с topic ID: {topic_error}")
                # Пробуем без topic ID
                bot_instance = self.bot
                sent_message = await bot_instance.send_message(
                    chat_id=int(CHAT_ID),
                    text=message,
                    parse_mode='HTML'
                )
            
            # Сохраняем в историю (для обратной совместимости)
            result_key = self.create_result_key(game_info)
            self.results_history[result_key] = {
                'date': get_moscow_time().isoformat(),
                'game_info': game_info,
                'message': message
            }
            self.save_results_history()
            
            # Добавляем запись в сервисный лист для защиты от дублирования
            additional_info = f"{game_info['date']} {game_info['our_team']} vs {game_info['opponent']} ({game_info['our_score']}:{game_info['opponent_score']}) - {game_info['result']}"
            duplicate_protection.add_record(
                "РЕЗУЛЬТАТ_ИГРА",
                result_key,
                "ОБРАБОТАН",
                additional_info
            )
            
            print(f"✅ Результат игры отправлен: {game_info['our_team']} vs {game_info['opponent']}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка отправки результата: {e}")
            return False
    
    async def run_game_results_monitor(self, force_run: bool = False):
        """Основная функция мониторинга результатов"""
        print("🏀 ЗАПУСК МОНИТОРИНГА РЕЗУЛЬТАТОВ ИГР")
        print("=" * 50)
        
        # Проверяем переменные окружения
        print("🔧 ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ:")
        print(f"BOT_TOKEN: {'✅' if BOT_TOKEN else '❌'}")
        print(f"CHAT_ID: {'✅' if CHAT_ID else '❌'}")
        print(f"ANNOUNCEMENTS_TOPIC_ID: {'✅' if ANNOUNCEMENTS_TOPIC_ID else '❌'}")
        print(f"ТЕСТОВЫЙ РЕЖИМ: {'✅ ВКЛЮЧЕН' if TEST_MODE else '❌ ВЫКЛЮЧЕН'}")
        
        # Показываем информацию о истории
        print(f"📋 История результатов: {len(self.results_history)} записей")
        if self.results_history:
            print("   Последние записи:")
            for i, (key, value) in enumerate(list(self.results_history.items())[-3:], 1):
                sent_time = value.get('date', 'неизвестно')
                print(f"   {i}. {key} - {sent_time}")
        
        if not BOT_TOKEN or not CHAT_ID:
            print("❌ Не все переменные окружения настроены")
            return
        
        # Проверяем время выполнения (для production, но не при ручном запуске)
        if not force_run and not self.should_check_results():
            now = get_moscow_time()
            print(f"⏰ Не время для проверки результатов: {now.strftime('%H:%M')} MSK")
            print("📅 Расписание проверки:")
            print("   Будни: 19:30-00:30 (каждые 15 минут)")
            print("   Выходные: 11:30-00:30 (каждые 15 минут)")
            print("💡 Для принудительного запуска используйте force_run=True")
            return
        
        # Получаем результаты игр
        print("\n🔄 Получение результатов игр...")
        games = await self.fetch_game_results()
        
        if not games:
            print("⚠️ Завершенных игр не найдено")
            return
        
        print(f"\n📊 Найдено {len(games)} завершенных игр:")
        for i, game in enumerate(games, 1):
            print(f"   {i}. {game['our_team']} vs {game['opponent']} ({game['our_score']}:{game['opponent_score']}) - {game['result']}")
        
        # Отправляем результаты
        print(f"\n📤 Отправка результатов...")
        sent_count = 0
        
        for i, game in enumerate(games, 1):
            print(f"\n🎮 Отправка результата {i}/{len(games)}...")
            success = await self.send_game_result(game)
            
            if success:
                sent_count += 1
            
            # Небольшая пауза между отправками
            await asyncio.sleep(2)
        
        print(f"\n📊 ИТОГИ:")
        print(f"✅ Отправлено результатов: {sent_count}")
        print(f"📋 Всего игр: {len(games)}")
        
        if sent_count > 0:
            print("\n✅ Мониторинг результатов завершен успешно!")
        else:
            print("\n⚠️ Результаты не отправлены (возможно, уже были отправлены ранее)")

async def main():
    """Основная функция"""
    monitor = GameResultsMonitorFinal()
    await monitor.run_game_results_monitor()

if __name__ == "__main__":
    asyncio.run(main())
