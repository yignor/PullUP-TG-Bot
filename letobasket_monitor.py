import datetime
import os
import asyncio
import aiohttp
import re
import sys
from bs4 import BeautifulSoup
from typing import Any, Optional
from telegram import Bot
from dotenv import load_dotenv

# Импортируем общие модули
from game_parser import game_parser
from notification_manager import notification_manager

# Загружаем переменные окружения
load_dotenv()

# Получаем переменные окружения (уже настроены в Railway)
BOT_TOKEN: str = os.getenv("BOT_TOKEN") or ""
CHAT_ID: str = os.getenv("CHAT_ID") or ""
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"
USE_BROWSER = os.getenv("USE_BROWSER", "0") == "1"

# Валидируем, что обязательные переменные заданы
if not DRY_RUN:
    if not BOT_TOKEN:
        print("❌ Переменная окружения BOT_TOKEN не установлена")
        sys.exit(1)
    if not CHAT_ID:
        print("❌ Переменная окружения CHAT_ID не установлена")
        sys.exit(1)

bot: Any = None
if not DRY_RUN:
    try:
        # На этом этапе BOT_TOKEN гарантированно str, не None
        bot = Bot(token=BOT_TOKEN)
        print(f"✅ Бот инициализирован успешно")
    except Exception as e:
        print(f"❌ ОШИБКА при инициализации бота: {e}")
        sys.exit(1)

# Переменная для отслеживания статуса игр (активные/завершенные)
game_status = {}  # {game_url: {'status': 'active'|'finished', 'last_check': datetime, 'teams': str}}

def is_game_finished(game_info):
    """Проверяет, завершилась ли игра (по времени)"""
    if not game_info or not game_info.get('time'):
        return False
    
    try:
        # Парсим время игры
        game_time_str = game_info['time']
        time_formats = [
            '%d.%m.%Y %H:%M',
            '%Y-%m-%d %H:%M',
            '%d/%m/%Y %H:%M',
            '%H:%M'
        ]
        
        game_datetime = None
        for fmt in time_formats:
            try:
                if ':' in game_time_str and len(game_time_str.split(':')) == 2:
                    # Если указано только время, добавляем сегодняшнюю дату
                    today = datetime.datetime.now().strftime('%Y-%m-%d')
                    time_str_with_date = f"{today} {game_time_str}"
                    game_datetime = datetime.datetime.strptime(time_str_with_date, '%Y-%m-%d %H:%M')
                else:
                    game_datetime = datetime.datetime.strptime(game_time_str, fmt)
                break
            except ValueError:
                continue
        
        if game_datetime:
            now = datetime.datetime.now()
            # Игра считается завершенной через 2 часа после начала
            game_end_time = game_datetime + datetime.timedelta(hours=2)
            return now > game_end_time
            
    except Exception as e:
        print(f"❌ Ошибка при проверке завершения игры: {e}")
    
    return False

async def check_game_completion(game_url, game_info):
    """Проверяет завершение игры и отправляет статистику"""
    try:
        if not game_info:
            return
        
        teams_str = f"{game_info.get('team1', 'Команда 1')} vs {game_info.get('team2', 'Команда 2')}"
        game_id = f"game_completion_{game_url}"
        
        # Проверяем, не отправляли ли мы уже статистику по этой игре
        if game_id in sent_notifications:
            return
        
        # Проверяем, завершилась ли игра
        if is_game_finished(game_info):
            # Формируем сообщение со статистикой
            lines = ["📊 Статистика по игре:"]
            lines.append(f"{teams_str}")
            lines.append("")
            lines.append("🏀 Счет:")
            lines.append(" (будет добавлено позже)")
            lines.append("")
            lines.append(f"📈 Статистика: [Тут]({game_url})")
            
            message = "\n".join(lines)
            
            if DRY_RUN:
                print(f"[DRY_RUN] -> send_message (completion): {message}")
            else:
                await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')
            
            sent_notifications.add(game_id)
            print(f"✅ Отправлена статистика по завершенной игре: {teams_str}")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке завершения игры: {e}")

def _build_target_team_patterns():
    """Возвращает список паттернов для поиска целевых команд.

    Можно задать переменную окружения TARGET_TEAMS (через запятую),
    например: "PullUP,Визотек".
    По умолчанию используется "PullUP" (с поддержкой вариантов написания).
    """
    targets_csv = os.getenv("TARGET_TEAMS", "PullUP")
    targets = [t.strip() for t in targets_csv.split(",") if t.strip()]

    patterns = []
    for team in targets:
        # Универсальная обработка для команд типа PullUP
        # Ищем команды, которые начинаются с "pull" (регистр не важен) и содержат "up"
        if re.match(r"^pull", team, re.IGNORECASE) and "up" in team.lower():
            patterns.extend([
                # Универсальный паттерн: начинается с pull, содержит up, может быть с пробелами/дефисами
                r"pull\s*[-\s]*up",
                r"pull\s*[-\s]*up\s+\w+",
                r"pull\s*[-\s]*up\s*[-\s]*\w+",
                # Также ищем точное название команды
                re.escape(team),
                re.escape(team) + r"\s+\w+",
            ])
        else:
            escaped = re.escape(team)
            patterns.extend([
                escaped,
                fr"{escaped}\s+\w+",
            ])
    return patterns

# Паттерны формируются динамически на основе переменной окружения TARGET_TEAMS
PULLUP_PATTERNS = _build_target_team_patterns()

def find_pullup_team(text_block):
    """Ищет команду PullUP в тексте с универсальной поддержкой вариантов написания"""
    for pattern in PULLUP_PATTERNS:
        matches = re.findall(pattern, text_block, re.IGNORECASE)
        if matches:
            # Возвращаем первое найденное совпадение
            return matches[0].strip()
    return None

def find_target_teams_in_text(text_block: str) -> "list[str]":
    """Возвращает список целевых команд, обнаруженных в тексте (по TARGET_TEAMS)."""
    found = []
    for team in get_target_team_names():
        # Универсальная проверка для PullUP-подобных команд
        if re.match(r"^pull", team, re.IGNORECASE) and "up" in team.lower():
            # Ищем любую комбинацию pull + up
            pattern = r"pull\s*[-\s]*up"
            if re.search(pattern, text_block, re.IGNORECASE):
                found.append(team)
        else:
            # Обычная проверка для других команд
            pattern = re.escape(team)
            if re.search(pattern, text_block, re.IGNORECASE):
                found.append(team)
    # Удаляем дубликаты, сохраняем порядок
    seen = set()
    unique_found = []
    for t in found:
        if t.lower() not in seen:
            unique_found.append(t)
            seen.add(t.lower())
    return unique_found

def get_target_team_names() -> list:
    targets_csv = os.getenv("TARGET_TEAMS", "PullUP")
    return [t.strip() for t in targets_csv.split(",") if t.strip()]

def _build_full_url(base_url: str, href: str) -> str:
    if href.startswith('http'):
        return href
    return base_url.rstrip('/') + '/' + href.lstrip('/')

def extract_game_links_from_soup(soup: BeautifulSoup, base_url: str, max_links: int = 30) -> list:
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if not href:
            continue
        href_low = href.lower()
        if any(k in href_low for k in ['game.html', 'gameid=', 'match', 'podrobno', 'protocol', 'game']):
            full_url = _build_full_url(base_url, href)
            if full_url not in links:
                links.append(full_url)
        if len(links) >= max_links:
            break
    return links

def team_matches_targets(team_name: Optional[str], targets: list) -> bool:
    if not team_name:
        return False
    lower_name = team_name.lower()
    for t in targets:
        tl = t.lower()
        # Специальная обработка PullUP-подобных команд: допускаем пробелы/дефисы между pull и up
        if re.match(r"^pull", tl, re.IGNORECASE) and "up" in tl:
            if re.search(r"pull\s*[-\s]*up", lower_name, re.IGNORECASE):
                return True
        else:
            if tl in lower_name:
                return True
    return False

def should_send_game_notification(game_time_str):
    """Проверяет, нужно ли отправить уведомление о игре в текущий запуск"""
    if not game_time_str:
        return False
    
    try:
        # Парсим время игры
        time_formats = [
            '%H:%M',
            '%H:%M:%S',
            '%d.%m.%Y %H:%M',
            '%Y-%m-%d %H:%M',
            '%d/%m/%Y %H:%M'
        ]
        
        game_datetime = None
        for fmt in time_formats:
            try:
                if ':' in game_time_str and len(game_time_str.split(':')) >= 2:
                    # Если указано только время, добавляем сегодняшнюю дату
                    if len(game_time_str.split(':')) == 2:
                        today = datetime.datetime.now().strftime('%Y-%m-%d')
                        time_str_with_date = f"{today} {game_time_str}"
                        game_datetime = datetime.datetime.strptime(time_str_with_date, '%Y-%m-%d %H:%M')
                    else:
                        game_datetime = datetime.datetime.strptime(game_time_str, fmt)
                    break
            except ValueError:
                continue
        
        if game_datetime:
            now = datetime.datetime.now()
            
            # Определяем, в какой 30-минутный интервал попадает время игры
            game_hour = game_datetime.hour
            game_minute = game_datetime.minute
            
            # Определяем интервал запуска (0-29 или 30-59)
            if game_minute < 30:
                target_hour = game_hour
                target_minute_range = (0, 29)
            else:
                target_hour = game_hour
                target_minute_range = (30, 59)
            
            # Проверяем, совпадает ли текущий запуск с нужным интервалом
            current_hour = now.hour
            current_minute = now.minute
            
            # Если время игры сегодня и в нужном интервале
            if (game_datetime.date() == now.date() and 
                current_hour == target_hour and 
                target_minute_range[0] <= current_minute <= target_minute_range[1]):
                return True
            
            # Если время игры завтра и сейчас последний запуск дня (23:30-23:59)
            if (game_datetime.date() == now.date() + datetime.timedelta(days=1) and 
                current_hour == 23 and current_minute >= 30):
                return True
                
        return False
        
    except Exception as e:
        print(f"❌ Ошибка при проверке времени уведомления: {e}")
        return False

async def parse_game_info(game_url):
    """Парсит информацию о игре с страницы игры"""
    return await game_parser.parse_game_info(game_url)

                    # 2) Пытаемся извлечь команды из DOM: left/right -> comman/name
                    if not team1_name or not team2_name:
                        # Встречается написание class="comman"; добавим резерв на случай class="command"
                        left_block = soup.find('div', class_='left')
                        right_block = soup.find('div', class_='right')

                        def get_team_name(root):
                            if not root:
                                return None
                            name_node = None
                            # Сначала строго по иерархии
                            comman = root.find('div', class_='comman') or root.find('div', class_='command')
                            if comman:
                                name_node = comman.find('div', class_='name')
                            # Фолбэк: искать name в пределах блока
                            if not name_node:
                                name_node = root.find('div', class_='name')
                            return name_node.get_text(strip=True) if name_node else None

                        extracted_left = get_team_name(left_block)
                        extracted_right = get_team_name(right_block)
                        team1_name = team1_name or extracted_left
                        team2_name = team2_name or extracted_right

                    # Если время/команды не найдены, можно попробовать отрендерить страницу в браузере
                    if USE_BROWSER and (not game_time or not team1_name or not team2_name):
                        try:
                            from pyppeteer import launch
                            browser = await launch(args=['--no-sandbox', '--disable-setuid-sandbox'], headless=True)
                            page = await browser.newPage()
                            await page.setViewport({"width": 1280, "height": 800})
                            await page.goto(game_url, {"waitUntil": "networkidle2", "timeout": 30000})
                            # Не всегда head появляется быстро — ждём, но не падаем, если нет
                            try:
                                await page.waitForSelector('div.el-tournament-head', {"timeout": 10000})
                            except Exception:
                                pass
                            head_text = await page.evaluate("() => { const el = document.querySelector('div.el-tournament-head'); return el ? el.innerText : ''; }")
                            if DRY_RUN:
                                print(f"[DRY_RUN] el-tournament-head (browser): {head_text}")
                            if head_text:
                                # Повторно парсим данные из полученного текста
                                # Поддержка русских месяцев
                                month_map = {
                                    'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04', 'мая': '05',
                                    'июня': '06', 'июля': '07', 'августа': '08', 'сентября': '09', 'октября': '10',
                                    'ноября': '11', 'декабря': '12'
                                }
                                def extract_dt(text: str):
                                    patterns_combo = [
                                        r"(\d{1,2}[./]\d{1,2}[./]\d{2,4})\s+(\d{1,2}[:.]\d{2}(?:[:.]\d{2})?)",
                                        r"(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s*(\d{4})?\s*(?:в\s+)?(\d{1,2}[:.]\d{2}(?:[:.]\d{2})?)",
                                        r"(\d{1,2}[:.]\d{2}(?:[:.]\d{2})?)\s+(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
                                    ]
                                    for pat in patterns_combo:
                                        m = re.search(pat, text, re.IGNORECASE)
                                        if m:
                                            if len(m.groups()) == 2:
                                                if re.match(r"\d{1,2}[./]", m.group(1)):
                                                    return f"{m.group(1)} {m.group(2)}".strip().rstrip(',')
                                                return f"{m.group(2)} {m.group(1)}".strip().rstrip(',')
                                            else:
                                                day = int(m.group(1))
                                                month_name = m.group(2).lower()
                                                year = m.group(3) or str(datetime.datetime.now().year)
                                                time_part = m.group(4)
                                                month_num = month_map.get(month_name)
                                                if month_num:
                                                    return f"{day:02d}.{month_num}.{year} {time_part}".strip().rstrip(',')
                                    # Отдельно
                                    date_numeric = re.search(r"(\d{1,2}[./]\d{1,2}[./]\d{2,4})", text)
                                    date_russian = re.search(r"(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s*(\d{4})?", text, re.IGNORECASE)
                                    time_match = re.search(r"\b(\d{1,2}[:.]\d{2}(?:[:.]\d{2})?)\b", text)
                                    if time_match:
                                        if date_numeric:
                                            return f"{date_numeric.group(1)} {time_match.group(1)}".strip().rstrip(',')
                                        if date_russian:
                                            day = int(date_russian.group(1))
                                            month_name = date_russian.group(2).lower()
                                            year = date_russian.group(3) or str(datetime.datetime.now().year)
                                            month_num = month_map.get(month_name)
                                            if month_num:
                                                return f"{day:02d}.{month_num}.{year} {time_match.group(1)}".strip().rstrip(',')
                                        return time_match.group(1).strip().rstrip(',')
                                    return None
                                dt = extract_dt(head_text)
                                if dt:
                                    game_time = dt
                                # Команды
                                splits = re.split(r"\s+-\s+|\s+—\s+|против|vs|VS|Vs", head_text, maxsplit=1)
                                if len(splits) == 2:
                                    team1_name = team1_name or splits[0].strip()
                                    team2_name = team2_name or splits[1].strip()

                                # Попробуем вытащить команды по DOM-селекторам в контексте страницы и всех фреймов
                                if not team1_name or not team2_name:
                                    try:
                                        js_fn = "() => {\n  const pick = (root) => {\n    if (!root) return '';\n    const trySelectors = [\n      'div.comman div.name',\n      'div.command div.name',\n      'div.name',\n      'div.comman a',\n      'div.command a',\n      'div.name a',\n      'a.name',\n      'span.name',\n      '.team-name',\n    ];\n    for (const sel of trySelectors) {\n      const el = root.querySelector(sel);\n      if (el && el.textContent) {\n        return el.textContent.trim();\n      }\n    }\n    return (root.innerText || '').trim();\n  };\n  const left = document.querySelector('div.left');\n  const right = document.querySelector('div.right');\n  return { left: pick(left), right: pick(right) };\n}"
                                        # Сначала пробуем в основном документе
                                        names = await page.evaluate(js_fn)
                                        if DRY_RUN:
                                            print(f"[DRY_RUN] browser teams (main): {names}")
                                        if names:
                                            if not team1_name and names.get('left'):
                                                team1_name = names.get('left')
                                            if not team2_name and names.get('right'):
                                                team2_name = names.get('right')
                                        # Если пусто — пробуем во всех фреймах
                                        if (not names or (not names.get('left') and not names.get('right'))):
                                            picked = None
                                            for fr in page.frames:
                                                try:
                                                    n = await fr.evaluate(js_fn)
                                                    if n and (n.get('left') or n.get('right')):
                                                        picked = { 'names': n, 'url': fr.url }
                                                        break
                                                except Exception:
                                                    continue
                                            if picked and DRY_RUN:
                                                print(f"[DRY_RUN] browser teams (frame {picked['url']}): {picked['names']}")
                                            if picked:
                                                if not team1_name:
                                                    team1_name = picked['names'].get('left') or team1_name
                                                if not team2_name:
                                                    team2_name = picked['names'].get('right') or team2_name
                                    except Exception as __e:
                                        if DRY_RUN:
                                            print(f"[DRY_RUN] Browser team extraction failed: {__e}")
                            # Закрываем браузер по завершению
                            await browser.close()
                        except Exception as _e:
                            if DRY_RUN:
                                print(f"[DRY_RUN] Browser fallback failed: {_e}")

                    # Ищем время игры в элементе с классом fa-calendar
                    time_element = soup.find('i', class_='fa fa-calendar')
                    
                    if time_element:
                        # Получаем текст после иконки календаря
                        time_text = time_element.get_text().strip()
                        if time_text:
                            game_time = time_text
                        else:
                            # Ищем время в родительском элементе
                            parent = time_element.parent
                            if parent:
                                time_text = parent.get_text().strip()
                                game_time = time_text
                    
                    # Ищем элементы с protocol.team1.TeamRegionName и protocol.team2.TeamRegionName
                    page_text = soup.get_text()
                    
                    # Ищем команды в тексте страницы
                    team_patterns = [
                        r'protocol\.team1\.TeamRegionName[:\s]*([^\n\r]+)',
                        r'protocol\.team2\.TeamRegionName[:\s]*([^\n\r]+)',
                        r'Команда 1[:\s]*([^\n\r]+)',
                        r'Команда 2[:\s]*([^\n\r]+)',
                        r'Team 1[:\s]*([^\n\r]+)',
                        r'Team 2[:\s]*([^\n\r]+)'
                    ]
                    
                    for pattern in team_patterns:
                        matches = re.findall(pattern, page_text, re.IGNORECASE)
                        if matches:
                            if 'team1' in pattern or 'Команда 1' in pattern or 'Team 1' in pattern:
                                team1_name = matches[0].strip()
                            elif 'team2' in pattern or 'Команда 2' in pattern or 'Team 2' in pattern:
                                team2_name = matches[0].strip()
                    
                    # Если не нашли через протокол, ищем в заголовках или других элементах
                    if not team1_name or not team2_name:
                        # Ищем в заголовках h1, h2, h3
                        headers = soup.find_all(['h1', 'h2', 'h3'])
                        for header in headers:
                            header_text = header.get_text().strip()
                            if 'против' in header_text.lower() or 'vs' in header_text.lower():
                                # Разделяем по "против" или "vs"
                                if 'против' in header_text.lower():
                                    teams = header_text.split('против')
                                else:
                                    teams = header_text.split('vs')
                                
                                if len(teams) >= 2:
                                    team1_name = teams[0].strip()
                                    team2_name = teams[1].strip()
                                    break
                    
                    return {
                        'time': game_time,
                        'team1': team1_name,
                        'team2': team2_name
                    }
                else:
                    print(f"⚠️ Ошибка при загрузке страницы игры: {response.status}")
                    return None
                    
    except Exception as e:
        print(f"❌ Ошибка при парсинге информации о игре: {e}")
        return None

async def check_game_start(game_info, game_url):
    """Проверяет, нужно ли отправить уведомление о начале игры"""
    try:
        if not game_info or not game_info['time']:
            return
        
        if should_send_game_notification(game_info['time']):
            # Используем общий менеджер уведомлений
            await notification_manager.send_game_start_notification(game_info, game_url)
    except Exception as e:
        print(f"❌ Ошибка при проверке начала игры: {e}")

async def check_letobasket_site():
    """Проверяет сайт letobasket.ru на наличие игр PullUP"""
    try:
        print(f"🔍 Проверяю сайт letobasket.ru...")
        
        # Получаем свежий контент страницы
        html_content = await game_parser.get_fresh_page_content()
                if response.status == 200:
                    html_content = await response.text()
                    
                    # Парсим HTML
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Получаем весь текст страницы
                    page_text = soup.get_text()
                    
                    # Ищем дату на странице
                    date_match = re.search(r'(\d{1,2}[./]\d{1,2}[./]\d{2,4})', page_text)
                    current_date = date_match.group(1) if date_match else None
                    print(f"📅 Дата на странице: {current_date}")
                    
                    # Ищем все вариации PullUP во всей странице
                    pullup_patterns = [
                        r'PULL UP ФАРМ',
                        r'PULL UP-ФАРМ',
                        r'Pull Up-Фарм',
                        r'pull up-фарм',
                        r'PULL UP',
                        r'Pull Up',
                        r'pull up',
                        r'PullUP Фарм',
                        r'PullUP'
                    ]
                    
                    found_pullup_games = []
                    used_links = set()  # Множество уже использованных ссылок
                    
                    # Ищем конкретные игры с PullUP по времени
                    pullup_games = [
                        {"time": "12.30", "team1": "IT Basket", "team2": "Pull Up"},
                        {"time": "14.00", "team1": "Маиле Карго", "team2": "Pull Up"}
                    ]
                    
                    for game in pullup_games:
                        game_time = game["time"]
                        team1 = game["team1"]
                        team2 = game["team2"]
                        
                        # Ищем эту игру в тексте
                        game_pattern = rf'{current_date}\s+{game_time}[^-]*-\s*{re.escape(team1)}[^-]*-\s*{re.escape(team2)}'
                        if re.search(game_pattern, page_text, re.IGNORECASE):
                            print(f"   🏀 Найдена игра PullUP: {team1} vs {team2} - {game_time}")
                            
                            # Определяем, какая команда является PullUP
                            pullup_team = None
                            opponent_team = None
                            
                            if "pull" in team1.lower() and "up" in team1.lower():
                                pullup_team = team1
                                opponent_team = team2
                            elif "pull" in team2.lower() and "up" in team2.lower():
                                pullup_team = team2
                                opponent_team = team1
                            
                            if pullup_team and opponent_team:
                                # Очищаем название соперника
                                opponent_team = re.sub(r'\s+', ' ', opponent_team).strip()
                                opponent_team = re.sub(r'^[-—\s]+|[-—\s]+$', '', opponent_team).strip()
                                opponent_team = re.sub(r'\s*pull\s*up\s*', '', opponent_team, flags=re.IGNORECASE).strip()
                                opponent_team = re.sub(r'[-—]+', '', opponent_team).strip()
                                
                                # Ищем ссылку на игру в HTML
                                game_link = None
                                
                                # Находим порядок игры на странице
                                game_pattern = rf'{current_date}\s+{game_time}[^-]*-\s*{re.escape(team1)}[^-]*-\s*{re.escape(team2)}'
                                text_match = re.search(game_pattern, page_text, re.IGNORECASE)
                                
                                if text_match:
                                    # Ищем все игры на странице для определения порядка
                                    all_games = re.findall(rf'{current_date}\s+\d{{2}}\.\d{{2}}[^-]*-\s*[^-]+[^-]*-\s*[^-]+', page_text)
                                    
                                    # Находим позицию текущей игры в списке
                                    current_game_text = text_match.group(0)
                                    game_order = None
                                    
                                    for i, game in enumerate(all_games):
                                        # Сравниваем более гибко, проверяя время и команды
                                        if (game.strip() == current_game_text.strip() or 
                                            game.replace(' ', '').lower() == current_game_text.replace(' ', '').lower()):
                                            game_order = i + 1  # Порядок начинается с 1
                                            break
                                    
                                    # Если не нашли точное совпадение, ищем по времени и командам
                                    if not game_order:
                                        for i, game in enumerate(all_games):
                                            # Проверяем, содержит ли игра нужное время и команды
                                            has_time = game_time in game
                                            has_team1 = team1 in game
                                            has_team2 = team2 in game
                                            
                                            if has_time and has_team1 and has_team2:
                                                game_order = i + 1
                                                break
                                    
                                    if game_order:
                                        print(f"   📍 Игра находится на позиции {game_order}")
                                        
                                        # Берем ссылку по порядку
                                        game_links = re.findall(r'href=["\']([^"\']*game\.html\?gameId=\d+[^"\']*)["\']', html_content, re.IGNORECASE)
                                        if game_order <= len(game_links):
                                            game_link = game_links[game_order - 1]  # Индексация с 0
                                            if not game_link.startswith('http'):
                                                game_link = LETOBASKET_URL.rstrip('/') + '/' + game_link.lstrip('/')
                                            print(f"   🔗 Используем ссылку #{game_order}: {game_link}")
                                        else:
                                            print(f"   ⚠️ Ссылка #{game_order} не найдена, всего ссылок: {len(game_links)}")
                                    else:
                                        print(f"   ⚠️ Позиция игры не определена")
                                
                                # Если не нашли по порядку, берем первую неиспользованную
                                if not game_link:
                                    game_links = re.findall(r'href=["\']([^"\']*game\.html\?gameId=\d+[^"\']*)["\']', html_content, re.IGNORECASE)
                                    for link in game_links:
                                        if link not in used_links:
                                            game_link = link
                                            used_links.add(link)  # Помечаем ссылку как использованную
                                            break
                                    
                                    if game_link and not game_link.startswith('http'):
                                        game_link = LETOBASKET_URL.rstrip('/') + '/' + game_link.lstrip('/')
                                
                                game_info = {
                                    'team': pullup_team,
                                    'opponent': opponent_team,
                                    'date': current_date,
                                    'time': game_time,
                                    'score': None,  # Счет пока не известен для новых игр
                                    'status': 'в процессе',  # Новые игры в процессе
                                    'link': game_link
                                }
                                
                                # Проверяем, что это не дубликат
                                is_duplicate = False
                                for existing_game in found_pullup_games:
                                    if (pullup_team and existing_game['team'].lower() == pullup_team.lower() and 
                                        existing_game['opponent'] == opponent_team):
                                        is_duplicate = True
                                        break
                                
                                if not is_duplicate:
                                    found_pullup_games.append(game_info)
                                    print(f"   ✅ Добавлена игра: {pullup_team} vs {opponent_team} - {game_time}")
                                    if game_link:
                                        print(f"      🔗 Ссылка: {game_link}")
                                else:
                                    print(f"   ⚠️ Дубликат пропущен: {pullup_team}")
                    
                    if found_pullup_games:
                        # Формируем сообщение
                        lines = []
                        
                        for game in found_pullup_games:
                            team = game['team']
                            opponent = game['opponent'] or 'Команда соперника'
                            date = game['date'] or 'Дата не указана'
                            time = game['time'] or ''
                            score = game['score'] or ''
                            status = game['status']
                            link = game['link'] or LETOBASKET_URL
                            
                            # Формируем строку игры
                            game_line = f"Сегодня игра {team}"
                            if opponent and opponent != 'Команда соперника':
                                game_line += f" против {opponent}"
                            
                            if time:
                                game_line += f" {time}"
                            
                            lines.append(game_line)
                            
                            # Добавляем ссылку на игру
                            lines.append(f"Ссылка на игру: [Тут]({link})")
                            lines.append("")  # Пустая строка между играми
                        
                        message = "\n".join(lines)
                        notification_id = f"pullup_games_{hash(str(found_pullup_games))}"
                        
                        if notification_id not in sent_notifications:
                            if DRY_RUN:
                                print(f"[DRY_RUN] -> send_message: {message}")
                            else:
                                await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')
                            sent_notifications.add(notification_id)
                            print("✅ Отправлено уведомление о играх PullUP")
                        else:
                            print("ℹ️ Уведомление уже было отправлено")
                    else:
                        print("📊 Игры с PullUP не найдены на странице")
                        
                else:
                    print(f"❌ Ошибка получения страницы: {response.status}")
                    
    except Exception as e:
        print(f"❌ Ошибка при проверке сайта: {e}")

async def main():
    """Основная функция"""
    try:
        now = datetime.datetime.now()
        print(f"🤖 Запуск мониторинга сайта letobasket.ru в {now.strftime('%Y-%m-%d %H:%M')}...")
        
        # Выполняем проверку
        await check_letobasket_site()
        
        print("✅ Проверка завершена")
    except Exception as e:
        print(f"❌ Критическая ошибка в main(): {e}")

if __name__ == "__main__":
    try:
        # Запускаем основную проверку (без планировщика)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка при запуске: {e}")
        sys.exit(1)
