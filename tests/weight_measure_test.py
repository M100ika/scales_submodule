import sys
from pathlib import Path
from loguru import logger

sys.path.append(str(Path(__file__).resolve().parent.parent / 'src'))

from _config_manager import ConfigManager
import _lib_pcf as lib

config_manager = ConfigManager()
from time import sleep

logger.remove()
logger.add(sys.stderr, format="{time} {level} {file}:{line} {message}", level="DEBUG")

def main():
    try:
        logger.info(f'\033[1;35mFeeder project. Weight measurment test file.\033[0m')
        lib._calibrate_or_start()
        arduino_start = lib.start_obj()
        while True:
            weight = arduino_start.get_measure()
            logger.info(f"Weight is: {weight}\n")
            sleep(0.1)
    finally:
        logger.info("Bye!")
        arduino_start.disconnect()
    

main()