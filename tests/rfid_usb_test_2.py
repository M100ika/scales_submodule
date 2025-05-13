import sys
from pathlib import Path
from loguru import logger
import time

sys.path.append(str(Path(__file__).resolve().parent.parent / 'src'))

from _chafon_rfid_lib import RFIDReader

logger.remove()
logger.add(sys.stderr, format="{time} {level} {message}", level="DEBUG")

def main():
    logger.info(f'Начало теста rfid_reader модуля - считывание через USB')
    logger.info(f'Пожалуйста заполните ../config/config.ini [RFID_Reader] reader_port = \nК примеру: /dev/ttyUSB0')
    logger.info(f'Если вы не знаете порт пожалуйста сделайте следующие шаги: ')
    logger.info(f'1. Отключите USB от rfid_reader;')
    logger.info(f'2. Откройте терминал (ctrl+alt+t) и введите следующую команду: /dev/tty*;')
    logger.info(f'3. Запомните список. Список возможно будет большой, но внимание нужно обратить на ttyUSB* или ttyACM*;')
    logger.info(f'4. Вставьте USB обратно в raspberry и снова введите команду: /dev/tty*;')
    logger.info(f'5. Должен появиться новый ttyUSB* или ttyACM*')
    logger.info(f'6. Перепишите его в ../config/config.ini [RFID_Reader] reader_port = СЮДА\nК примеру: /dev/ttyUSB0')
    try:
        rfid_reader = RFIDReader()
    except Exception as e:
        logger.error(f'Не удалось инициализировать RFIDReader: {e}')
        logger.info('Программа будет закрыта через 10 секунд...')
        time.sleep(10)
        sys.exit(1)

    start_time = time.time()
    timeout = 600  
    try:
        while True:
            current_time = time.time()
            animal_id = rfid_reader.connect()
            logger.info(animal_id)
            time.sleep(0.1)
            if current_time - start_time > timeout:
                logger.info('10 минут прошли. Пока.')
                break
    except Exception as e:
        logger.error(f'Error: {e}')
        time.sleep(10)
    animal_id = rfid_reader.connect()
    start_time = time.time()
    timeout = 600
    try:
        while True:
            current_time = time.time()
            animal_id = rfid_reader.connect()
            logger.info(animal_id)
            if current_time - start_time > timeout:
                logger.info(f'10 минут прошли. Пока.')
                time.sleep(5)
                break
    except Exception as e:
        logger.error(f'Error: {e}')
        time.sleep(10)

main()