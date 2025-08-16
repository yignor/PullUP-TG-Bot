import asyncio
import aiohttp
import re

async def debug_link_mapping():
    url = "http://letobasket.ru/"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html_content = await response.text()
    
    # Извлекаем текст из HTML
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    page_text = soup.get_text()
    
    print("=== АНАЛИЗ СВЯЗИ ИГР И ССЫЛОК ===")
    
    # Ищем текущую дату
    date_pattern = r'(\d{2}\.\d{2}\.\d{4})'
    date_match = re.search(date_pattern, page_text)
    if date_match:
        current_date = date_match.group(1)
        print(f"📅 Найдена дата: {current_date}")
    else:
        print("❌ Дата не найдена")
        return
    
    # Ищем все ссылки game.html
    game_links = re.findall(r'href=["\']([^"\']*game\.html\?gameId=\d+[^"\']*)["\']', html_content, re.IGNORECASE)
    print(f"\n🔗 Найдено ссылок game.html: {len(game_links)}")
    for i, link in enumerate(game_links):
        print(f"  {i+1}. {link}")
    
    # Ищем игры PullUP
    pullup_games = [
        {"time": "12.30", "team1": "IT Basket", "team2": "Pull Up-Фарм"},
        {"time": "14.00", "team1": "Маиле Карго", "team2": "Pull Up"}
    ]
    
    print(f"\n=== АНАЛИЗ КАЖДОЙ ИГРЫ ===")
    
    for i, game in enumerate(pullup_games):
        print(f"\n--- Игра {i+1}: {game['time']} {game['team1']} vs {game['team2']} ---")
        
        # Ищем эту игру в тексте
        game_pattern = rf'{current_date}\s+{game["time"]}[^-]*-\s*{re.escape(game["team1"])}[^-]*-\s*{re.escape(game["team2"])}'
        text_match = re.search(game_pattern, page_text, re.IGNORECASE)
        
        if text_match:
            print(f"✅ Найдена игра в тексте: {text_match.group(0)}")
            print(f"   Позиция в тексте: {text_match.start()} - {text_match.end()}")
            
            # Находим соответствующую позицию в HTML
            text_before_game = page_text[:text_match.start()]
            html_before_game = html_content[:len(text_before_game)]
            
            print(f"   Позиция в HTML: {len(html_before_game)}")
            
            # Ищем ссылки game.html в HTML после этой позиции
            search_start = len(html_before_game)
            search_end = min(len(html_content), search_start + 2000)
            search_area = html_content[search_start:search_end]
            
            print(f"   Область поиска: {search_start} - {search_end} (размер: {len(search_area)})")
            
            # Ищем ссылку game.html в этой области
            game_link_match = re.search(r'href=["\']([^"\']*game\.html\?gameId=\d+[^"\']*)["\']', search_area, re.IGNORECASE)
            if game_link_match:
                found_link = game_link_match.group(1)
                print(f"   ✅ Найдена ссылка в области: {found_link}")
                
                # Находим индекс этой ссылки в общем списке
                for j, link in enumerate(game_links):
                    if link == found_link:
                        print(f"   📍 Это ссылка #{j+1} в общем списке")
                        break
            else:
                print(f"   ❌ Ссылка в области не найдена")
                
                # Показываем часть HTML для анализа
                print(f"   🔍 HTML в области поиска (первые 500 символов):")
                print(f"   {search_area[:500]}")
        else:
            print("❌ Игра не найдена в тексте")

if __name__ == "__main__":
    asyncio.run(debug_link_mapping())
