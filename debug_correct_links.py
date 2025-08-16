import asyncio
import aiohttp
import re

async def debug_correct_links():
    url = "http://letobasket.ru/"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html_content = await response.text()
    
    # Извлекаем текст из HTML
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    page_text = soup.get_text()
    
    print("=== АНАЛИЗ ПРАВИЛЬНЫХ ССЫЛОК ===")
    
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
    
    # Ищем все игры на странице
    print(f"\n=== ВСЕ ИГРЫ НА СТРАНИЦЕ ===")
    
    # Ищем все строки с играми
    game_lines = re.findall(rf'{current_date}\s+\d{{2}}\.\d{{2}}[^-]*-\s*[^-]+[^-]*-\s*[^-]+', page_text)
    
    for i, game_line in enumerate(game_lines):
        print(f"\n--- Игра {i+1} ---")
        print(f"Текст: {game_line}")
        
        # Ищем позицию этой игры в тексте
        game_pos = page_text.find(game_line)
        if game_pos != -1:
            print(f"Позиция в тексте: {game_pos}")
            
            # Находим соответствующую позицию в HTML
            text_before_game = page_text[:game_pos]
            html_before_game = html_content[:len(text_before_game)]
            
            print(f"Позиция в HTML: {len(html_before_game)}")
            
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
                print(f"🔗 Ближайшая ссылка: {closest_link} (расстояние: {closest_distance})")
                
                # Извлекаем gameId
                game_id_match = re.search(r'gameId=(\d+)', closest_link)
                if game_id_match:
                    game_id = game_id_match.group(1)
                    print(f"   GameID: {game_id}")
            else:
                print(f"❌ Ссылка не найдена")

if __name__ == "__main__":
    asyncio.run(debug_correct_links())
