# src/check_drivers.py
import os
import sys


def check_drivers():
    print("🔍 Поиск geckodriver в системе:")
    print(f"Python prefix: {sys.prefix}")

    # Проверяем различные расположения
    locations = [
        # Venv locations
        os.path.join(sys.prefix, 'Scripts', 'geckodriver.exe'),
        os.path.join(sys.prefix, 'bin', 'geckodriver'),
        os.path.join('venv', 'Scripts', 'geckodriver.exe'),
        os.path.join('venv', 'bin', 'geckodriver'),
        # System locations
        '/usr/bin/geckodriver',
        '/usr/local/bin/geckodriver',
        'C:\\WebDriver\\geckodriver.exe',
        # PATH
        'geckodriver'  # Проверим PATH
    ]

    found = False
    for location in locations:
        if os.path.exists(location):
            print(f"✅ Найден: {location}")
            found = True
        else:
            print(f"❌ Не найден: {location}")

    # Проверим PATH
    try:
        import subprocess
        result = subprocess.run(['geckodriver', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Найден в PATH: {result.stdout.split()[1]}")
            found = True
    except:
        print("❌ Не найден в PATH")

    if not found:
        print("\n🔧 Geckodriver не найден. Запусти:")
        print("   python install_geckodriver.py")


if __name__ == "__main__":
    check_drivers()