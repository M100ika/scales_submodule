import sys
from pathlib import Path
from loguru import logger

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from _config_manager import ConfigManager
import _feeder_module as fdr

config_manager = ConfigManager()
from time import sleep

logger.remove()
logger.add(sys.stderr, format="{time} {level} {file}:{line} {message}", level="DEBUG")

def main():
    try:
        logger.info(f'\033[1;35mFeeder project. Weight measurment test file.\033[0m')
        fdr._calibrate_or_start()
        arduino_start = fdr.initialize_arduino()
        while True:
            weight = fdr._first_weight(arduino_start)
            logger.info(f"Weight is: {weight}\n")
            sleep(0.1)
    finally:
        logger.info("Bye!")
        arduino_start.disconnect()
    

main()