#!/usr/bin/env python3
"""
Детальный анализатор для поиска ссылок "СТРАНИЦА ИГРЫ"
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def analyze_game_pages():
    """Анализирует ссылки на страницы игр"""
    print("🔍 ДЕТАЛЬНЫЙ АНАЛИЗ ССЫЛОК 'СТРАНИЦА ИГРЫ'")
    print("=" * 60)
    
    try:
        url = "http://letobasket.ru"
        
        print(f"🌐 Получение данных с {url}...")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as response:
                if response.status != 200:
                    print(f"❌ Ошибка получения страницы: {response.status}")
                    return
                
                html = await response.text()
                print(f"✅ Страница получена, размер: {len(html)} символов")
        
        # Парсим HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Ищем все ссылки на странице
        all_links = soup.find_all('a', href=True)
        
        print(f"\n📊 НАЙДЕНО {len(all_links)} ССЫЛОК НА СТРАНИЦЕ")
        print("=" * 60)
        
        # Анализируем ссылки
        game_page_links = []
        vizotek_related_links = []
        
        for i, link in enumerate(all_links):
            href = link.get('href', '')
            link_text = link.get_text().strip()
            link_text_lower = link_text.lower()
            
            if not href or not link_text:
                continue
            
            # Ищем ссылки "СТРАНИЦА ИГРЫ"
            if 'страница игры' in link_text_lower or 'game page' in link_text_lower:
                game_page_links.append({
                    'index': i,
                    'href': href,
                    'text': link_text,
                    'context': link.parent.get_text()[:100] if link.parent else ""
                })
            
            # Ищем ссылки, связанные с Визотек
            if 'визотек' in link_text_lower or 'vizotek' in link_text_lower:
                vizotek_related_links.append({
                    'index': i,
                    'href': href,
                    'text': link_text,
                    'context': link.parent.get_text()[:100] if link.parent else ""
                })
        
        # Выводим результаты
        print(f"\n🎮 ССЫЛКИ 'СТРАНИЦА ИГРЫ' ({len(game_page_links)}):")
        for link in game_page_links:
            print(f"   {link['index']:3d}. {link['text']} -> {link['href']}")
            print(f"       Контекст: {link['context']}")
            print()
        
        if not game_page_links:
            print("   ❌ Ссылки 'СТРАНИЦА ИГРЫ' не найдены")
        
        print(f"\n🎯 ССЫЛКИ, СВЯЗАННЫЕ С ВИЗОТЕК ({len(vizotek_related_links)}):")
        for link in vizotek_related_links:
            print(f"   {link['index']:3d}. {link['text']} -> {link['href']}")
            print(f"       Контекст: {link['context']}")
            print()
        
        if not vizotek_related_links:
            print("   ❌ Ссылки с упоминанием Визотек не найдены")
        
        # Ищем все ссылки с текстом, содержащим "игра" или "game"
        game_related_texts = []
        for i, link in enumerate(all_links):
            link_text = link.get_text().strip()
            if any(keyword in link_text.lower() for keyword in ['игра', 'game', 'match', 'матч']):
                game_related_texts.append({
                    'index': i,
                    'text': link_text,
                    'href': link.get('href', '')
                })
        
        print(f"\n🏀 ССЫЛКИ С ИГРОВЫМИ ТЕРМИНАМИ ({len(game_related_texts)}):")
        for link in game_related_texts[:20]:  # Показываем первые 20
            print(f"   {link['index']:3d}. {link['text']} -> {link['href']}")
        
        if len(game_related_texts) > 20:
            print(f"   ... и еще {len(game_related_texts) - 20} ссылок")
        
        # Ищем все уникальные тексты ссылок, содержащие "страница"
        page_links = []
        for i, link in enumerate(all_links):
            link_text = link.get_text().strip()
            if 'страница' in link_text.lower():
                page_links.append({
                    'index': i,
                    'text': link_text,
                    'href': link.get('href', '')
                })
        
        print(f"\n📄 ССЫЛКИ С ТЕКСТОМ 'СТРАНИЦА' ({len(page_links)}):")
        for link in page_links:
            print(f"   {link['index']:3d}. {link['text']} -> {link['href']}")
        
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")

if __name__ == "__main__":
    asyncio.run(analyze_game_pages())
