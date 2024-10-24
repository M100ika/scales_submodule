import sys
from pathlib import Path
from loguru import logger

sys.path.append(str(Path(__file__).resolve().parent.parent / 'src'))

from _config_manager import ConfigManager


config_manager = ConfigManager()
from time import sleep

logger.remove()
logger.add(sys.stderr, format="{time} {level} {file}:{line} {message}", level="DEBUG")

def main():
    try:
        logger.info(f'\033[1;35mFeeder project. Test.\033[0m')
        logger.info(f'RFID_TIMEOUT = {float(config_manager.get_setting("RFID_Reader", "reader_timeout"))}')

    finally:
        logger.info("Bye!")

main()