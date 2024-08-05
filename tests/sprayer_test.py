import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / 'src'))

from _config_manager import ConfigManager
import time
import timeit
import datetime
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    from __gpio_simulator import MockGPIO as GPIO


from _sprayer import Sprayer
import _values_class as value_data
from _glb_val import *

    
from loguru import logger

debug_level = "DEBUG" if DEBUG == 1 else "CRITICAL"

"""Инициализация logger для хранения записи о всех действиях программы"""
logger.add(sys.stdout, format="{time} {level} {message}", level=debug_level)  


def process(cow_id: str) -> tuple:
    logger.info(f'Sprayer test started for cow_id: {cow_id}')
    try:

        weight_arr = []
        next_time = time.time() + 1
        
        drink_start_time = timeit.default_timer()
        gpio_state = False
        
        values = value_data.Values(
            drink_start_time, 0, TYPE_SCALES, cow_id, 0, '0', 0, 0, 0, 0, True
        )

        logger.info(f'Initial values set: {values}')

        if SPRAYER:
            sprayer = Sprayer(values)
            logger.info('Sprayer initialized.')
        i = 200
        while True:

            current_time = time.time()
            time_to_wait = next_time - current_time

            if SPRAYER:
                if not values.flag:
                    gpio_state = sprayer.spray_main_function(gpio_state)
                    values = sprayer.new_start_timer(gpio_state)
                else:
                    if time_to_wait < 0 and round(time.time(), 0) % 5 == 0:
                        values.flag = False

            if time_to_wait < 0:
                i+=1
                weight_arr.append(i)
                next_time = time.time() + 1
                logger.debug(f'Array weights: {weight_arr}')
            time.sleep(1)
            if i == 220:
                break
        
        GPIO.cleanup()

        if not weight_arr:
            logger.info("null weight list")
            return 0, [], ''

        if SPRAYER:
            gpio_state = sprayer.gpio_state_check(gpio_state)

    except KeyboardInterrupt as e:
        logger.error(f'measure_weight Error: {e}')
        GPIO.cleanup()
        if SPRAYER:
            gpio_state = sprayer.gpio_state_check(gpio_state)
        

def main():
    logger.info(f'Starting test of _sprayer.py.')
    cow_id = '4354001c004501c38d2010132e25010f0101e2806894000040103003'
    process(cow_id)

main()