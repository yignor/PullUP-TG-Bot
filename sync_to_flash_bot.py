#!/usr/bin/env python3
"""
Скрипт для синхронизации изменений из Basketball-Team-Bot в Flash-bot
Копирует только измененные файлы и делает коммит
"""

import os
import subprocess
import sys
from pathlib import Path

# Пути к репозиториям
SOURCE_REPO = Path(__file__).parent
TARGET_REPO = Path("/Users/y/Downloads/Flash-bot")

# Файлы, которые нужно синхронизировать (относительно корня репозитория)
FILES_TO_SYNC = [
    "enhanced_duplicate_protection.py",
    "game_system_manager.py",
    "birthday_notifications.py",
    "training_polls_enhanced.py",
    "notification_manager.py",
    "game_results_monitor_final.py",
    "datetime_utils.py",
    "info_basket_client.py",
    "infobasket_smart_parser.py",
    "comp_names.py",
    "players_manager.py",
    "cleanup_service_sheet.py",
    ".github/workflows/daily_operations.yml",
    ".github/workflows/game_results_monitor_v2.yml",
    ".github/workflows/cleanup_service_sheet.yml",
    "requirements-github.txt",
    "env.example",
]

# Файлы, которые НЕ нужно синхронизировать
FILES_TO_EXCLUDE = [
    ".env",
    ".git",
    "__pycache__",
    "*.pyc",
    ".vscode",
    "*.md",  # Документация может отличаться
]

def run_command(cmd, cwd=None, check=True):
    """Выполняет команду и возвращает результат"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout.strip(), e.stderr.strip(), e.returncode

def get_changed_files():
    """Получает список измененных файлов в исходном репозитории"""
    # Сначала проверяем незакоммиченные изменения
    stdout, stderr, code = run_command(
        "git diff --name-only",
        cwd=SOURCE_REPO,
        check=False
    )
    
    if stdout.strip():
        changed = [f.strip() for f in stdout.split('\n') if f.strip()]
        return changed
    
    # Если нет незакоммиченных, проверяем последний коммит
    stdout, stderr, code = run_command(
        "git diff --name-only HEAD~1 HEAD",
        cwd=SOURCE_REPO,
        check=False
    )
    
    if stdout.strip():
        changed = [f.strip() for f in stdout.split('\n') if f.strip()]
        return changed
    
    return []

def should_sync_file(file_path):
    """Проверяет, нужно ли синхронизировать файл"""
    file_str = str(file_path)
    
    # Проверяем исключения
    for exclude in FILES_TO_EXCLUDE:
        if exclude in file_str:
            return False
    
    # Если файл в списке для синхронизации
    if file_path.name in FILES_TO_SYNC or any(f in file_str for f in FILES_TO_SYNC):
        return True
    
    # Синхронизируем Python файлы и конфигурационные файлы
    if file_path.suffix in ['.py', '.yml', '.yaml', '.txt', '.json']:
        # Но не в служебных директориях
        if '.git' not in file_str and '__pycache__' not in file_str:
            return True
    
    return False

def sync_file(source_file, target_file):
    """Копирует файл из исходного репозитория в целевой"""
    try:
        # Создаем директорию, если её нет
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Копируем файл
        import shutil
        shutil.copy2(source_file, target_file)
        print(f"✅ Скопирован: {source_file.relative_to(SOURCE_REPO)}")
        return True
    except Exception as e:
        print(f"❌ Ошибка копирования {source_file}: {e}")
        return False

def main():
    """Основная функция синхронизации"""
    print("🔄 Синхронизация изменений из Basketball-Team-Bot в Flash-bot")
    print("=" * 60)
    
    # Проверяем существование целевого репозитория
    if not TARGET_REPO.exists():
        print(f"❌ Целевой репозиторий не найден: {TARGET_REPO}")
        sys.exit(1)
    
    # Обработка аргументов командной строки
    sync_all = "--all" in sys.argv
    specific_files = [arg for arg in sys.argv[1:] if not arg.startswith("--") and (SOURCE_REPO / arg).exists()]
    
    if specific_files:
        # Синхронизируем указанные файлы
        print(f"\n📋 Синхронизация указанных файлов: {len(specific_files)}")
        files_to_process = [SOURCE_REPO / f for f in specific_files]
    elif sync_all:
        # Синхронизируем все файлы из списка
        print("\n📋 Синхронизация всех файлов из списка...")
        files_to_process = [SOURCE_REPO / f for f in FILES_TO_SYNC if (SOURCE_REPO / f).exists()]
    else:
        # Получаем измененные файлы
        print("\n📋 Определение измененных файлов...")
        changed_files = get_changed_files()
        
        if not changed_files:
            print("ℹ️ Нет измененных файлов для синхронизации")
            print("\n💡 Доступные опции:")
            print("   --all              - синхронизировать все файлы из списка")
            print("   file1.py file2.py  - синхронизировать конкретные файлы")
            print("\nПримеры:")
            print("   python3 sync_to_flash_bot.py --all")
            print("   python3 sync_to_flash_bot.py game_system_manager.py enhanced_duplicate_protection.py")
            sys.exit(0)
        
        # Фильтруем файлы для синхронизации
        files_to_process = []
        for file_path_str in changed_files:
            file_path = SOURCE_REPO / file_path_str
            if file_path.exists() and should_sync_file(file_path):
                files_to_process.append(file_path)
    
    if not files_to_process:
        print("ℹ️ Нет файлов для синхронизации")
        sys.exit(0)
    
    print(f"\n📦 Найдено файлов для синхронизации: {len(files_to_process)}")
    
    # Копируем файлы
    synced_files = []
    for source_file in files_to_process:
        relative_path = source_file.relative_to(SOURCE_REPO)
        target_file = TARGET_REPO / relative_path
        
        if sync_file(source_file, target_file):
            synced_files.append(relative_path)
    
    if not synced_files:
        print("\n⚠️ Не удалось синхронизировать файлы")
        sys.exit(1)
    
    print(f"\n✅ Синхронизировано файлов: {len(synced_files)}")
    
    # Делаем коммит в целевом репозитории
    print("\n📝 Создание коммита...")
    stdout, stderr, code = run_command(
        "git status --short",
        cwd=TARGET_REPO,
        check=False
    )
    
    if not stdout.strip():
        print("ℹ️ Нет изменений для коммита")
        sys.exit(0)
    
    # Добавляем файлы
    for file_path in synced_files:
        run_command(
            f"git add {file_path}",
            cwd=TARGET_REPO,
            check=False
        )
    
    # Создаем коммит
    commit_message = f"Синхронизация из Basketball-Team-Bot: {', '.join([str(f) for f in synced_files[:3]])}"
    if len(synced_files) > 3:
        commit_message += f" и еще {len(synced_files) - 3} файлов"
    
    stdout, stderr, code = run_command(
        f'git commit -m "{commit_message}"',
        cwd=TARGET_REPO,
        check=False
    )
    
    if code == 0:
        print(f"✅ Коммит создан: {commit_message}")
    else:
        if "nothing to commit" in stderr.lower():
            print("ℹ️ Нет изменений для коммита")
        else:
            print(f"⚠️ Ошибка создания коммита: {stderr}")
    
    # Предлагаем отправить изменения
    print("\n💡 Для отправки изменений выполните:")
    print(f"   cd {TARGET_REPO}")
    print("   git push")
    
    print("\n✅ Синхронизация завершена!")

if __name__ == "__main__":
    main()

