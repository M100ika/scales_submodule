import sys
from pathlib import Path
from loguru import logger
import time

# Добавляем путь к src, где лежит _chafon_rfid_lib.py
sys.path.append(str(Path(__file__).resolve().parent.parent / 'src'))

from _cha_2 import RFIDReader

# Настройка логирования
logger.remove()
logger.add(sys.stderr, format="{time} {level} {message}", level="DEBUG")


def main():
    # Создаём экземпляр
    reader = RFIDReader()

    # Если порт не задан в config.ini — ищем автоматически
    if not reader.reader_port:
        port = reader.find_rfid_reader()
        if port:
            logger.info(f"Найден ридер на порту {port}")
        else:
            logger.error("Не удалось найти RFID-ридер. Проверьте подключение.")
            return

    # Открываем соединение (timeout на чтение 0.05 с)
    try:
        reader.open(timeout=0.05)
    except Exception as e:
        logger.error(f"Ошибка при открытии порта: {e}")
        return

    logger.info("Начинаем читать метки (Ctrl+C для выхода)")
    start_time = time.time()
    try:
        while True:
            # Читаем одну метку с таймаутом 1 с
            tag = reader.read_tag(timeout=3.0)
            if tag:
                logger.info(f"Прочитана метка: {tag}")

            # Выходим по истечении 10 минут
            if time.time() - start_time > 600:
                logger.info("10 минут прошли. Завершаем тест.")
                break

            time.sleep(0.05)

    except KeyboardInterrupt:
        logger.info("Выход по Ctrl+C")

    finally:
        reader.close()
        logger.info("Соединение закрыто")


if __name__ == '__main__':
    main()
