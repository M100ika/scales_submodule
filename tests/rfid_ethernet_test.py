import sys
import socket
import binascii
from pathlib import Path
from loguru import logger
import time

sys.path.append(str(Path(__file__).resolve().parent.parent / 'src'))

from _config_manager import ConfigManager
from _chafon_rfid_lib import RFIDReader
from _lib_pcf import __connect_rfid_reader_ethernet, _set_power_RFID_ethernet
from _glb_val import RFID_READER_USB

# === Конфигурация и логгирование ===
config_manager = ConfigManager()

logger.remove()
logger.add(sys.stderr, format="{time} {level} {message}", level="DEBUG")

RFID_TIMEOUT = int(config_manager.get_setting("RFID_Reader", "reader_timeout"))

def read_rfid():
    if RFID_READER_USB:
        logger.info("Using USB-connected RFID reader")
        reader = RFIDReader()
        tag_id = reader.connect()
        logger.info(f"RFID tag ID (USB): {tag_id}")
        return tag_id
    else:
        _set_power_RFID_ethernet()
        tag = __connect_rfid_reader_ethernet()
        if tag:
            logger.success(f"RFID tag detected: {tag}")
        time.sleep(0.5) 
        return tag_id

def main():
    logger.info("RFID Reader Test Menu\n1 — Read tag\n2 — Exit")
    choice = input("Enter choice: ").strip()
    if choice == "1":
        try:
            while True:
                tag_id = read_rfid()
                if tag_id:
                    logger.success(f"Detected RFID tag: {tag_id}")
        except KeyboardInterrupt:
            logger.info("Interrupted by user.")
    else:
        logger.info("Exiting.")

if __name__ == "__main__":
    main()
