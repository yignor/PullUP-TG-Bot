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
                                            team_type = 'Состав Развития'
                                        else:
                                            team_type = 'Первый состав'
                                        
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
    
    async def fetch_game_results_from_links(self) -> List[Dict]:
        """Получает результаты игр используя ссылки из сервисного листа"""
        try:
            from enhanced_duplicate_protection import duplicate_protection
            from datetime_utils import get_moscow_time
            
            today = get_moscow_time().strftime('%d.%m.%Y')
            games = []
            
            # Получаем все данные из сервисного листа
            worksheet = duplicate_protection._get_service_worksheet()
            if not worksheet:
                print("❌ Сервисный лист недоступен")
                return []
            
            all_data = worksheet.get_all_values()
            
            # Ищем записи типа АНОНС_ИГРА за сегодня с ссылками
            for row in all_data:
                if (len(row) >= 6 and 
                    row[0] == "АНОНС_ИГРА" and 
                    today in row[1] and 
                    row[5]):  # Есть ссылка
                    
                    game_link = row[5]
                    if not game_link.startswith('http'):
                        game_link = f"http://letobasket.ru/{game_link}"
                    
                    print(f"🔍 Парсим игру по ссылке: {game_link}")
                    
                    # Парсим игру используя улучшенный парсер
                    game_info = await self.parse_game_from_link(game_link)
                    if game_info:
                        games.append(game_info)
                        print(f"✅ Игра добавлена: {game_info['our_team']} vs {game_info['opponent']} - {game_info['result']}")
                    else:
                        print(f"❌ Не удалось распарсить игру")
            
            return games
            
        except Exception as e:
            print(f"❌ Ошибка получения результатов по ссылкам: {e}")
            return []
    
    async def find_game_link(self, team1: str, team2: str, game_date: str = None) -> Optional[str]:
        """Ищет ссылку на игру по командам (сначала в сервисном листе, потом в анонсах, потом в табло)"""
        try:
            # 1. Сначала ищем в сервисном листе Google Sheets (самый надежный способ)
            from enhanced_duplicate_protection import duplicate_protection
            link_from_service_sheet = duplicate_protection.find_game_link_for_today(team1, team2)
            if link_from_service_sheet:
                print(f"🔗 Найдена ссылка в сервисном листе: {link_from_service_sheet}")
                return link_from_service_sheet
            
            # 2. Если не найдено в сервисном листе, ищем в анонсах игр
            print(f"🔍 Ссылка не найдена в сервисном листе, ищем в анонсах...")
            link_from_announcements = self.find_link_in_announcements(team1, team2, game_date)
            if link_from_announcements:
                print(f"🔗 Найдена ссылка в анонсах: {link_from_announcements}")
                return link_from_announcements
            
            # 3. Если не найдено в анонсах, ищем в табло
            print(f"🔍 Ссылка не найдена в анонсах, ищем в табло...")
            result = await self.game_manager.find_game_link(team1, team2)
            if result:
                game_link, found_team = result
                print(f"🔗 Найдена ссылка в табло: {game_link}")
                return game_link
            
            print(f"❌ Ссылка на игру не найдена ни в одном источнике")
            return None
        except Exception as e:
            print(f"❌ Ошибка поиска ссылки на игру: {e}")
            return None
    
    async def parse_game_from_link(self, game_link: str) -> Optional[Dict]:
        """Парсит игру по ссылке используя улучшенный парсер"""
        try:
            from enhanced_game_parser import EnhancedGameParser
            
            async with EnhancedGameParser() as parser:
                game_info = await parser.parse_game_from_url(game_link)
                if game_info and game_info.get('result'):
                    # Определяем статус игры
                    status = 'Завершена' if game_info.get('result') in ['победа', 'поражение', 'ничья'] else 'В процессе'
                    
                    # Преобразуем в формат, ожидаемый системой
                    return {
                        'team1': game_info.get('our_team', ''),
                        'team2': game_info.get('opponent', ''),
                        'our_team': game_info.get('our_team', ''),
                        'opponent': game_info.get('opponent', ''),
                        'our_score': game_info.get('our_score', 0),
                        'opponent_score': game_info.get('opponent_score', 0),
                        'result': game_info.get('result', ''),
                        'status': status,
                        'date': game_info.get('date', ''),
                        'time': game_info.get('time', ''),
                        'venue': game_info.get('venue', ''),
                        'quarters': game_info.get('quarters', []),
                        'team_type': 'Первый состав' if 'фарм' not in game_info.get('our_team', '').lower() else 'Состав Развития',
                        'game_link': game_link,  # Сохраняем исходную ссылку на игру
                        'our_team_leaders': game_info.get('our_team_leaders', {})  # Добавляем лидеров команды
                    }
                return None
        except Exception as e:
            print(f"❌ Ошибка парсинга игры по ссылке: {e}")
            return None
    
    def find_link_in_announcements(self, team1: str, team2: str, game_date: str = None) -> Optional[str]:
        """Ищет ссылку на игру в сохраненных анонсах"""
        try:
            import json
            import os
            
            announcements_file = "game_announcements.json"
            if not os.path.exists(announcements_file):
                print(f"📄 Файл анонсов не найден: {announcements_file}")
                return None
            
            with open(announcements_file, 'r', encoding='utf-8') as f:
                announcements = json.load(f)
            
            print(f"📋 Загружено {len(announcements)} анонсов для поиска ссылки")
            
            # Ищем по разным вариантам ключей
            search_keys = []
            
            # Если есть дата, используем её
            if game_date:
                # Нормализуем время (заменяем точку на двоеточие)
                time_variants = ["12:00", "12.00", "14:00", "14.00", "16:00", "16.00", "18:00", "18.00", "20:00", "20.00"]
                for time_var in time_variants:
                    search_keys.append(f"{game_date}_{time_var}_{team1}_{team2}")
                    search_keys.append(f"{game_date}_{time_var}_{team2}_{team1}")
            else:
                # Ищем по всем возможным комбинациям
                for key in announcements.keys():
                    if team1 in key and team2 in key:
                        search_keys.append(key)
            
            print(f"🔍 Ищем по ключам: {search_keys[:3]}...")  # Показываем первые 3
            
            for key in search_keys:
                if key in announcements:
                    announcement = announcements[key]
                    game_link = announcement.get('game_link')
                    if game_link:
                        # Формируем полную ссылку
                        if game_link.startswith('http'):
                            full_link = game_link
                        else:
                            full_link = f"http://letobasket.ru/{game_link}"
                        print(f"✅ Найдена ссылка в анонсе {key}: {full_link}")
                        return full_link
            
            print(f"❌ Ссылка не найдена в анонсах")
            return None
            
        except Exception as e:
            print(f"❌ Ошибка поиска в анонсах: {e}")
            return None
    
    async def send_game_result(self, game_info: Dict) -> bool:
        """Отправляет результат игры в Telegram"""
        if not self.bot or not CHAT_ID:
            print("❌ Бот не инициализирован или CHAT_ID не настроен")
            return False
        
        try:
            # Создаем ключ для проверки дублирования
            result_key = self.create_result_key(game_info)
            
            # Проверяем дублирование в Google Sheets (основная защита)
            print(f"🔍 Проверяем дублирование в Google Sheets для игры: {game_info['team1']} vs {game_info['team2']}")
            duplicate_check = duplicate_protection.check_duplicate("РЕЗУЛЬТАТ_ИГРА", result_key)
            
            if duplicate_check.get('exists'):
                print(f"⏭️ Результат для игры {game_info['team1']} vs {game_info['team2']} уже отправлен (найдено в Google Sheets)")
                print(f"   📅 Время отправки: {duplicate_check.get('data', ['', '', '', '', ''])[1]}")
                return False
            
            # Дополнительная проверка по локальному файлу (для обратной совместимости)
            print(f"🔍 Проверяем локальную историю для игры: {game_info['team1']} vs {game_info['team2']}")
            if self.was_result_sent(game_info):
                print(f"⏭️ Результат для игры {game_info['team1']} vs {game_info['team2']} уже отправлен (найдено в локальной истории)")
                return False
            
            # Используем новую функцию форматирования с лидерами команды
            our_team_leaders = game_info.get('our_team_leaders', {})
            game_link = game_info.get('game_link')
            
            if not game_link:
                print(f"🔍 Ссылка не найдена в game_info, ищем заново...")
                game_link = await self.find_game_link(game_info['team1'], game_info['team2'], game_info.get('date'))
            
            # Формируем сообщение используя новую функцию
            message = self.game_manager.format_game_result_message(
                game_info=game_info,
                game_link=game_link,
                our_team_leaders=our_team_leaders
            )
            
            # Добавляем четверти только если есть реальные данные
            quarters = game_info.get('quarters', [])
            if quarters and quarters != ['Данные недоступны']:
                message += f"\n📈 Четверти: {quarters}"
            
            if game_link:
                print(f"🔗 Используется ссылка: {game_link}")
            else:
                print(f"❌ Ссылка на игру не найдена")
            
            # Сначала добавляем запись в Google Sheets для защиты от дублирования
            additional_info = f"{game_info['date']} {game_info['our_team']} vs {game_info['opponent']} ({game_info['our_score']}:{game_info['opponent_score']}) - {game_info['result']}"
            protection_result = duplicate_protection.add_record(
                "РЕЗУЛЬТАТ_ИГРА",
                result_key,
                "ОТПРАВЛЯЕТСЯ",  # Временный статус
                additional_info
            )
            
            if not protection_result.get('success'):
                print(f"❌ Ошибка добавления записи в Google Sheets: {protection_result.get('error')}")
                # Продолжаем отправку, но логируем ошибку
            
            # Отправляем сообщение в основной топик (без message_thread_id)
            try:
                # Результаты игр отправляем в основной топик
                bot_instance = self.bot
                sent_message = await bot_instance.send_message(
                    chat_id=int(CHAT_ID),
                    text=message,
                    parse_mode='HTML'
                )
                print(f"✅ Результат отправлен в основной топик")
                
                # Обновляем статус в Google Sheets на "ОТПРАВЛЕНО"
                if protection_result.get('success') and protection_result.get('unique_key'):
                    duplicate_protection.update_record_status(protection_result['unique_key'], "ОТПРАВЛЕНО")
                    print(f"✅ Статус обновлен в Google Sheets: ОТПРАВЛЕНО")
                
            except Exception as send_error:
                print(f"❌ Ошибка отправки: {send_error}")
                # Обновляем статус на "ОШИБКА" если отправка не удалась
                if protection_result.get('success') and protection_result.get('unique_key'):
                    duplicate_protection.update_record_status(protection_result['unique_key'], "ОШИБКА")
                return False
            
            # Сохраняем в локальную историю (для обратной совместимости)
            self.results_history[result_key] = {
                'date': get_moscow_time().isoformat(),
                'game_info': game_info,
                'message': message
            }
            self.save_results_history()
            
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
        print(f"📋 Локальная история результатов: {len(self.results_history)} записей")
        if self.results_history:
            print("   Последние записи:")
            for i, (key, value) in enumerate(list(self.results_history.items())[-3:], 1):
                sent_time = value.get('date', 'неизвестно')
                print(f"   {i}. {key} - {sent_time}")
        
        # Показываем статистику из Google Sheets
        print(f"\n📊 Статистика из Google Sheets:")
        try:
            from enhanced_duplicate_protection import duplicate_protection
            stats = duplicate_protection.get_statistics()
            if 'РЕЗУЛЬТАТ_ИГРА' in stats:
                result_stats = stats['РЕЗУЛЬТАТ_ИГРА']
                print(f"   📈 Всего результатов: {result_stats.get('total', 0)}")
                print(f"   ✅ Отправлено: {result_stats.get('completed', 0)}")
                print(f"   🔄 В процессе: {result_stats.get('active', 0)}")
            else:
                print("   📈 Результатов игр в Google Sheets не найдено")
        except Exception as e:
            print(f"   ❌ Ошибка получения статистики: {e}")
        
        if not BOT_TOKEN or not CHAT_ID:
            print("❌ Не все переменные окружения настроены")
            return
        
        # Проверяем время выполнения (для production, но не при ручном запуске)
        if not force_run and not self.should_check_results():
            from datetime_utils import get_moscow_time
            now = get_moscow_time()
            print(f"⏰ Не время для проверки результатов: {now.strftime('%H:%M')} MSK")
            print("📅 Расписание проверки:")
            print("   Будни: 19:30-00:30 (каждые 15 минут)")
            print("   Выходные: 11:30-00:30 (каждые 15 минут)")
            print("💡 Для принудительного запуска используйте force_run=True")
            return
        
        # Проверяем наличие ссылок на игры для сегодня
        print("\n🔍 Проверка наличия ссылок на игры для сегодня...")
        from enhanced_duplicate_protection import duplicate_protection
        
        # Ищем ссылки на игры в сервисном листе
        today_games_found = False
        try:
            from datetime_utils import get_moscow_time
            today = get_moscow_time().strftime('%d.%m.%Y')
            
            # Получаем все данные из сервисного листа
            worksheet = duplicate_protection._get_service_worksheet()
            if worksheet:
                all_data = worksheet.get_all_values()
                
                # Ищем записи типа АНОНС_ИГРА за сегодня
                for row in all_data:
                    if (len(row) >= 6 and 
                        row[0] == "АНОНС_ИГРА" and 
                        today in row[1] and  # Дата в колонке B
                        row[5]):  # Ссылка в колонке F
                        today_games_found = True
                        print(f"✅ Найдена игра на сегодня: {row[2]} (ссылка: {row[5]})")
                        break
                
                if not today_games_found:
                    print(f"❌ Игры на сегодня ({today}) не найдены в сервисном листе")
                    print("💡 Убедитесь, что анонсы игр были созданы и содержат ссылки")
                    return
            else:
                print("❌ Сервисный лист недоступен")
                return
                
        except Exception as e:
            print(f"❌ Ошибка проверки ссылок на игры: {e}")
            return
        
        # Получаем результаты игр используя ссылки из сервисного листа
        print("\n🔄 Получение результатов игр...")
        games = await self.fetch_game_results_from_links()
        
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
