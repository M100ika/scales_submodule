#!/usr/bin/python3 

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

from submodule.src._lib_pcf import scales_v71
from loguru import logger
from _config_manager import ConfigManager

from _glb_val import DEBUG

config_manager = ConfigManager()
debug_level = "DEBUG" if DEBUG == 1 else "CRITICAL"

logger.add('log/scales_{time}.log', format="{time} {level} {message}", 
level="DEBUG", rotation="1 day", compression="zip")             # Настройка логгера

@logger.catch()         # Показывает ошибки, не работает если их обрабатывать
def main():
    try:
        scales_v71()
    except Exception as e: 
        logger.error(f'Error: {e}')
                

main()