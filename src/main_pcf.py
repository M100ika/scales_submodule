#!/usr/bin/python3 
#/home/pi/scales7.1/scales_submodule/src/main_pcf.py

"""Scales main file. Additional function: sprayer. Version 7.1
Author: Suieubayev Maxat.
Contact number +7 775 818 48 43. Email maxat.suieubayev@gmail.com"""

from _headers import install_packages

requirement_list = ['loguru', 
                    'requests', 
                    'pyserial',
                    'RPi.GPIO', 
                    'wabson.chafon-rfid']
install_packages(requirement_list)

from _lib_pcf import scales_v71
from loguru import logger
from _config_manager import ConfigManager
import os
try:
    import RPi.GPIO
    log_dir = "/home/pi/scales7.1/scales_submodule/loguru/scales_log"
    error_log_dir = f"{log_dir}/error_log"
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(error_log_dir, exist_ok=True)
    os.system(f"chmod -R 777 {log_dir}")

except RuntimeError:
    from __gpio_simulator import MockGPIO
    log_dir = '../feeder_log'
from _glb_val import DEBUG

config_manager = ConfigManager()
debug_level = "DEBUG" if DEBUG == 1 else "CRITICAL"

"""Инициализация logger для хранения записи о всех действиях программы"""
logger.add(f"{log_dir}/scales.log", format="{time} {level} {function} {message}", 
level=debug_level, rotation="1 day", retention= '1 month', compression="zip")  

"""Инициализация logger для хранения записи об ошибках программы"""
logger.add(f"{error_log_dir}/errors.log", format="{time} {level} {file} {function}:{line} {message}", 
level="ERROR", rotation="1 day", retention= '1 month', compression="zip")          # Настройка логгера

@logger.catch()         # Показывает ошибки, не работает если их обрабатывать
def main():
    try:
        scales_v71()
    except Exception as e: 
        logger.error(f'Error: {e}')
                

main()