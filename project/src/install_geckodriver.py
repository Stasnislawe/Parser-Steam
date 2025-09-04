# src/install_geckodriver.py
import os
import sys
import requests
import zipfile
from pathlib import Path


def install_geckodriver_to_venv():
    """Устанавливает geckodriver в папку venv"""
    # Находим папку venv
    venv_path = None
    current_path = Path(__file__).parent

    # Ищем папку venv в нескольких возможных расположениях
    possible_venv_paths = [
        current_path / 'venv',
        current_path.parent / 'venv',
        current_path / '.venv',
        current_path.parent / '.venv',
        Path(sys.prefix)  # Текущее окружение Python
    ]

    for path in possible_venv_paths:
        if path.exists() and any(path.name in {'venv', '.venv'} for path in path.parents):
            venv_path = path
            break
    else:
        venv_path = Path(sys.prefix)

    print(f"📁 Виртуальное окружение: {venv_path}")

    # Создаем папку для драйверов в venv
    drivers_dir = venv_path / 'Scripts' if os.name == 'nt' else venv_path / 'bin'
    drivers_dir.mkdir(exist_ok=True)

    geckodriver_path = drivers_dir / 'geckodriver.exe' if os.name == 'nt' else drivers_dir / 'geckodriver'

    if geckodriver_path.exists():
        print("✅ geckodriver уже установлен в venv")
        return True

    # Скачиваем geckodriver
    version = "0.34.0"
    url = f"https://github.com/mozilla/geckodriver/releases/download/v{version}/geckodriver-v{version}-win64.zip"

    try:
        print("📦 Скачиваем geckodriver...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        zip_path = drivers_dir / 'geckodriver.zip'
        with open(zip_path, 'wb') as f:
            f.write(response.content)

        # Распаковываем
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(drivers_dir)

        # На Windows переименовываем
        if os.name == 'nt':
            extracted_exe = drivers_dir / 'geckodriver.exe'
            if not extracted_exe.exists():
                # Ищем любой exe файл
                for file in drivers_dir.iterdir():
                    if file.suffix == '.exe' and 'gecko' in file.name.lower():
                        file.rename(geckodriver_path)
                        break

        zip_path.unlink()  # Удаляем zip
        print(f"✅ geckodriver установлен в: {geckodriver_path}")
        return True

    except Exception as e:
        print(f"❌ Ошибка установки: {e}")
        return False


if __name__ == "__main__":
    install_geckodriver_to_venv()