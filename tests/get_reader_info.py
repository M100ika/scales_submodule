import socket
import binascii
import time
from loguru import logger

TCP_IP = '192.168.1.250'  # IP считывателя
TCP_PORT = 60000
BUFFER_SIZE = 1024

# Команда запроса информации (Reader Info Command)
CMD_GET_READER_INFO = bytearray([0x53, 0x57, 0x00, 0x03, 0xFF, 0x21, 0x43])

def get_reader_info():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            logger.info("Connecting to reader...")
            s.connect((TCP_IP, TCP_PORT))
            s.settimeout(3)
            
            logger.info("Sending reader info command...")
            s.send(CMD_GET_READER_INFO)
            time.sleep(0.1)

            data = s.recv(BUFFER_SIZE)
            hex_data = binascii.hexlify(data).decode()

            logger.success(f"Reader response: {hex_data}")

    except Exception as e:
        logger.error(f"Error communicating with reader: {e}")

if __name__ == '__main__':
    get_reader_info()
