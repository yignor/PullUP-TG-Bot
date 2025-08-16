import asyncio
import aiohttp
import re

async def debug_link_positions():
    url = "http://letobasket.ru/"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html_content = await response.text()
    
    # Извлекаем текст из HTML
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    page_text = soup.get_text()
    
    print("=== АНАЛИЗ ПОЗИЦИЙ ССЫЛОК ===")
    
    # Ищем все ссылки game.html и их позиции
    game_links = []
    for match in re.finditer(r'href=["\']([^"\']*game\.html\?gameId=\d+[^"\']*)["\']', html_content, re.IGNORECASE):
        link = match.group(1)
        position = match.start()
        game_links.append((link, position))
    
    print(f"🔗 Найдено ссылок game.html: {len(game_links)}")
    for i, (link, pos) in enumerate(game_links):
        print(f"  {i+1}. {link} (позиция: {pos})")
    
    # Ищем текущую дату
    date_pattern = r'(\d{2}\.\d{2}\.\d{4})'
    date_match = re.search(date_pattern, page_text)
    if date_match:
        current_date = date_match.group(1)
        print(f"\n📅 Найдена дата: {current_date}")
    else:
        print("❌ Дата не найдена")
        return
    
    # Ищем игры PullUP
    pullup_games = [
        {"time": "12.30", "team1": "IT Basket", "team2": "Pull Up-Фарм"},
        {"time": "14.00", "team1": "Маиле Карго", "team2": "Pull Up"}
    ]
    
    print(f"\n=== СОПОСТАВЛЕНИЕ ИГР И ССЫЛОК ===")
    
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
            
            # Ищем ближайшую ссылку после этой позиции
            closest_link = None
            closest_distance = float('inf')
            
            for link, pos in game_links:
                if pos >= len(html_before_game):
                    distance = pos - len(html_before_game)
                    if distance < closest_distance:
                        closest_distance = distance
                        closest_link = link
            
            if closest_link:
                print(f"   🔗 Ближайшая ссылка: {closest_link} (расстояние: {closest_distance})")
            else:
                print(f"   ❌ Ссылка не найдена")
        else:
            print("❌ Игра не найдена в тексте")

if __name__ == "__main__":
    asyncio.run(debug_link_positions())
