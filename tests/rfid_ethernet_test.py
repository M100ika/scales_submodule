import socket
import binascii
import sys
from pathlib import Path
from loguru import logger

sys.path.append(str(Path(__file__).resolve().parent.parent / 'src'))

from _config_manager import ConfigManager
from chafon_rfid.command import CF_GET_READER_INFO
from chafon_rfid.base import RfidReader


config_manager = ConfigManager()

logger.remove()
logger.add(sys.stderr, format="{time} {level} {message}", level="DEBUG")

TCP_IP = '192.168.1.250'  # Chafon 5300 reader address
TCP_PORT = 60000          # Chafon 5300 port
BUFFER_SIZE = 1024
RFID_TIMEOUT = int(config_manager.get_setting("RFID_Reader", "reader_timeout"))

def __connect_rfid_reader_feeder():
    try:    
        logger.info('Start connect RFID function')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((TCP_IP, TCP_PORT))
            s.send(bytearray([0x53, 0x57, 0x00, 0x06, 0xff, 0x01, 0x00, 0x00, 0x00, 0x50])) # Chafon RU5300 Answer mode reading mode command
            s.settimeout(RFID_TIMEOUT)
            for attempt in range(1, 4):
                try:
                    data = s.recv(BUFFER_SIZE)
                    animal_id = binascii.hexlify(data).decode('utf-8')[:-10][-12:]
                    logger.info(f'After end: Animal ID: {animal_id}')
                    return animal_id if animal_id != None else None
                except socket.timeout:
                    logger.error(f'Timeout occurred on attempt {attempt}')
        return None
    except Exception as e:
        logger.error(f'Error connect RFID reader {e}')
        return None
    
def __reader_info():
    # Пример для считывателя, подключенного через Ethernet
    reader = RfidReader(ip=TCP_IP, port=TCP_PORT)  # Замените на актуальный IP-адрес и порт
    reader.connect()

    try:
        response = reader.execute(CF_GET_READER_INFO)
        logger.info("Reader Information:", response)
    except Exception as e:
        logger.info("Error getting reader information:", e)
    finally:
        reader.disconnect()


def main():
    logger.info(f'Enter:\n1 - For reading\n2 - To take reader info')
    choice = input()
    try:
        if int(choice) == 1:
            logger.info(f'Start test rfid reader antenna\n')
            cow_id = '435400040001'
            while(1):
                cow_id = __connect_rfid_reader_feeder()
                if cow_id != '435400040001':
                    logger.info(f'Cow_id now is: {cow_id}\n')
        elif int(choice) == 2:
            __reader_info()
    except TypeError as e:
        logger.error(f'Error {e}')

main()