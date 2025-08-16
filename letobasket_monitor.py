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

# URL для мониторинга
LETOBASKET_URL = "http://letobasket.ru/"

# Переменная для отслеживания уже отправленных уведомлений
sent_notifications = set()

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
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(game_url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    
                    # Парсим HTML
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # 1) Пытаемся достать дату/время и команды из блока el-tournament-head
                    game_time = None
                    team1_name = None
                    team2_name = None

                    head_block = soup.find('div', class_='el-tournament-head')
                    if head_block:
                        head_text = head_block.get_text(separator=' ', strip=True)
                        if DRY_RUN:
                            print(f"[DRY_RUN] el-tournament-head: {head_text}")

                        # Поддержка русских месяцев
                        month_map = {
                            'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04', 'мая': '05',
                            'июня': '06', 'июля': '07', 'августа': '08', 'сентября': '09', 'октября': '10',
                            'ноября': '11', 'декабря': '12'
                        }

                        def extract_datetime_from_text(text: str) -> Optional[str]:
                            # Комбинированные шаблоны (дата+время)
                            patterns_combo = [
                                r"(\d{1,2}[./]\d{1,2}[./]\d{2,4})\s+(\d{1,2}[:.]\d{2}(?:[:.]\d{2})?)",
                                r"(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s*(\d{4})?\s*(?:в\s+)?(\d{1,2}[:.]\d{2}(?:[:.]\d{2})?)",
                                r"(\d{1,2}[:.]\d{2}(?:[:.]\d{2})?)\s+(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
                            ]
                            for pat in patterns_combo:
                                m = re.search(pat, text, re.IGNORECASE)
                                if m:
                                    if len(m.groups()) == 2:
                                        # dd.mm.yyyy HH:MM[:SS]  или  HH:MM[:SS] dd.mm.yyyy (поддержка : и .)
                                        if re.match(r"\d{1,2}[./]", m.group(1)):
                                            return f"{m.group(1)} {m.group(2)}".strip().rstrip(',')
                                        return f"{m.group(2)} {m.group(1)}".strip().rstrip(',')
                                    else:
                                        # dd <month> [yyyy] [в ] HH:MM[:SS]
                                        day = int(m.group(1))
                                        month_name = m.group(2).lower()
                                        year = m.group(3) or str(datetime.datetime.now().year)
                                        time_part = m.group(4)
                                        month_num = month_map.get(month_name)
                                        if month_num:
                                            return f"{day:02d}.{month_num}.{year} {time_part}".strip().rstrip(',')
                            # Отдельно дата и отдельно время
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
                                # Если нашли только время — вернем время
                                return time_match.group(1).strip().rstrip(',')
                            return None

                        extracted_dt = extract_datetime_from_text(head_text)
                        if extracted_dt:
                            game_time = extracted_dt

                        # Пытаемся извлечь наименования команд из заголовка
                        # Популярные разделители: " - ", "—", "против", "vs"
                        splits = re.split(r"\s+-\s+|\s+—\s+|против|vs|VS|Vs", head_text, maxsplit=1)
                        if len(splits) == 2:
                            team1_name = splits[0].strip()
                            team2_name = splits[1].strip()

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
            # Создаем уникальный идентификатор для уведомления о начале игры
            start_notification_id = f"game_start_{game_url}"
            
            if start_notification_id not in sent_notifications:
                # Формируем сообщение
                team1 = game_info['team1'] or "Команда 1"
                team2 = game_info['team2'] or "Команда 2"
                
                message = f"🏀 Игра {team1} против {team2} начинается в {game_info['time']}!\n\nСсылка на игру: {game_url}"
                if DRY_RUN:
                    print(f"[DRY_RUN] -> send_message: {message}")
                else:
                    await bot.send_message(chat_id=CHAT_ID, text=message)
                sent_notifications.add(start_notification_id)
                print(f"✅ Отправлено уведомление о начале игры: {team1} vs {team2} в {game_info['time']}")
    except Exception as e:
        print(f"❌ Ошибка при проверке начала игры: {e}")

async def check_letobasket_site():
    """Проверяет сайт letobasket.ru на наличие игр PullUP"""
    try:
        print(f"🔍 Проверяю сайт {LETOBASKET_URL}...")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(LETOBASKET_URL) as response:
                if response.status == 200:
                    html_content = await response.text()
                    
                    # Парсим HTML
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Ищем блок между "Табло игры" и "online видеотрансляции игр доступны на странице"
                    page_text = soup.get_text()
                    
                    # Ищем начало блока "Табло игры"
                    start_marker = "Табло игры"
                    end_marker = "online видеотрансляции игр доступны на странице"
                    
                    start_index = page_text.find(start_marker)
                    end_index = page_text.find(end_marker)
                    
                    targets = get_target_team_names()
                    found_targets = []
                    if start_index != -1 and end_index != -1 and start_index < end_index:
                        # Извлекаем нужный блок текста
                        target_block = page_text[start_index:end_index]
                        
                        # Ищем команду PullUP с поддержкой различных вариаций
                        pullup_team = find_pullup_team(target_block)
                        # Дополнительно ищем все целевые команды из списка TARGET_TEAMS
                        for t in targets:
                            if re.search(re.escape(t), target_block, re.IGNORECASE):
                                found_targets.append(t)
                        
                        if pullup_team or found_targets:
                            primary = pullup_team or (found_targets[0] if found_targets else None)
                            print(f"🏀 Найдена целевая команда: {primary}")
                            
                            # Ищем ссылку "СТРАНИЦА ИГРЫ" в HTML
                            # Собираем все кандидаты-ссылки и валидируем каждую страницу на соответствие целевым командам
                            candidate_links = extract_game_links_from_soup(soup, LETOBASKET_URL)
                            matched_games = []
                            for link_url in candidate_links:
                                game_info = await parse_game_info(link_url)
                                if not game_info:
                                    continue
                                t1 = game_info.get('team1')
                                t2 = game_info.get('team2')
                                if team_matches_targets(t1, targets) or team_matches_targets(t2, targets):
                                    matched_games.append((link_url, game_info))

                            if matched_games:
                                lines = ["🏀 Игры сегодня:"]
                                for link_url, info in matched_games:
                                    n1 = info.get('team1') or 'Команда 1'
                                    n2 = info.get('team2') or 'Команда 2'
                                    lines.append(f" {n1} vs {n2}")
                                
                                # Добавляем время и ссылки
                                lines.append("")
                                lines.append("📅 Дата и Время:")
                                for link_url, info in matched_games:
                                    tm = info.get('time') or 'Время не указано'
                                    lines.append(f" {tm}")
                                
                                lines.append("")
                                lines.append("🔗 Ссылка на игру:")
                                for link_url, info in matched_games:
                                    lines.append(f" [Тут]({link_url})")
                                
                                message = "\n".join(lines)
                                id_base = "|".join([u for (u, _) in matched_games])
                                notification_id = f"targets_{hash(id_base)}"
                                if notification_id not in sent_notifications:
                                    if DRY_RUN:
                                        print(f"[DRY_RUN] -> send_message: {message}")
                                    else:
                                        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')
                                    sent_notifications.add(notification_id)
                                    print("✅ Отправлено агрегированное уведомление о целевых играх")
                                for link_url, info in matched_games:
                                    await check_game_start(info, link_url)
                                    # Также проверяем завершение игр
                                    await check_game_completion(link_url, info)
                            else:
                                print("📊 Подходящих игр по целевым командам среди собранных ссылок не найдено")
                                        
                            
                        else:
                            print("📊 Целевая команда не найдена в ограниченном блоке, сканирую всю страницу и валидирую ссылки")
                            # Фолбэк-агрегация: собираем ссылки и фильтруем по целевым командам
                            candidate_links = extract_game_links_from_soup(soup, LETOBASKET_URL)
                            matched_games = []
                            for link_url in candidate_links:
                                game_info = await parse_game_info(link_url)
                                if not game_info:
                                    continue
                                t1 = game_info.get('team1')
                                t2 = game_info.get('team2')
                                if team_matches_targets(t1, targets) or team_matches_targets(t2, targets):
                                    matched_games.append((link_url, game_info))
                            if matched_games:
                                lines = ["🏀 Игры сегодня:"]
                                for link_url, info in matched_games:
                                    n1 = info.get('team1') or 'Команда 1'
                                    n2 = info.get('team2') or 'Команда 2'
                                    lines.append(f" {n1} vs {n2}")
                            
                            # Добавляем время и ссылки
                            lines.append("")
                            lines.append("📅 Дата и Время:")
                            for link_url, info in matched_games:
                                tm = info.get('time') or 'Время не указано'
                                lines.append(f" {tm}")
                            
                            lines.append("")
                            lines.append("🔗 Ссылка на игру:")
                            for link_url, info in matched_games:
                                lines.append(f" [Тут]({link_url})")
                            
                            message = "\n".join(lines)
                            id_base = "|".join([u for (u, _) in matched_games])
                            notification_id = f"targets_{hash(id_base)}"
                            if notification_id not in sent_notifications:
                                if DRY_RUN:
                                    print(f"[DRY_RUN] -> send_message: {message}")
                                else:
                                    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')
                                sent_notifications.add(notification_id)
                                print("✅ Отправлено агрегированное уведомление о целевых играх")
                            for link_url, info in matched_games:
                                await check_game_start(info, link_url)
                                # Также проверяем завершение игр
                                await check_game_completion(link_url, info)
                            else:
                                print("📊 Подходящих игр по целевым командам среди собранных ссылок не найдено")
                    else:
                        print("ℹ️ Не найдены ожидаемые маркеры, сканирую всю страницу и валидирую ссылки")
                        candidate_links = extract_game_links_from_soup(soup, LETOBASKET_URL)
                        matched_games = []
                        for link_url in candidate_links:
                            game_info = await parse_game_info(link_url)
                            if not game_info:
                                continue
                            t1 = game_info.get('team1')
                            t2 = game_info.get('team2')
                            if team_matches_targets(t1, targets) or team_matches_targets(t2, targets):
                                matched_games.append((link_url, game_info))
                        if matched_games:
                            lines = ["🏀 Найдены игры целевых команд:"]
                            for link_url, info in matched_games:
                                tm = info.get('time') or 'Время не указано'
                                n1 = info.get('team1') or 'Команда 1'
                                n2 = info.get('team2') or 'Команда 2'
                                lines.append(f"- {n1} vs {n2} — {tm}\n  📋 {link_url}")
                            message = "\n".join(lines)
                            id_base = "|".join([u for (u, _) in matched_games])
                            notification_id = f"targets_{hash(id_base)}"
                            if notification_id not in sent_notifications:
                                if DRY_RUN:
                                    print(f"[DRY_RUN] -> send_message: {message}")
                                else:
                                    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')
                                sent_notifications.add(notification_id)
                                print("✅ Отправлено агрегированное уведомление о целевых играх")
                            for link_url, info in matched_games:
                                await check_game_start(info, link_url)
                                # Также проверяем завершение игр
                                await check_game_completion(link_url, info)
                        else:
                            print("📊 Подходящих игр по целевым командам среди собранных ссылок не найдено")
                else:
                    print(f"❌ Ошибка при загрузке сайта: {response.status}")
                    
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
