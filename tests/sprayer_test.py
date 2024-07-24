import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'src'))

from src._config_manager import ConfigManager
import time
import timeit
import datetime
from src._sprayer import Sprayer
from src._values_class import value_data
from src._glb_val import *
import RPi.GPIO as GPIO

from loguru import logger


def process(obj, cow_id: str) -> tuple:
    try:
        weight_arr = []
        next_time = time.time() + 1
        
        drink_start_time = timeit.default_timer()
        gpio_state = False
        
        values = value_data.Values(
            drink_start_time, 0, TYPE_SCALES, cow_id, 0, '0', 0, 0, 0, 0, True
        )

        if SPRAYER:
            sprayer = Sprayer(values)
        
        weight_on_moment = obj.get_measure()
        logger.info(f'Weight on the moment: {weight_on_moment}')

        while True:
            obj.calc_mean()
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
                weight_arr.append(obj.calc_mean())
                next_time = time.time() + 1
                logger.debug(f'Array weights: {weight_arr}')

            weight_on_moment = obj.get_measure()


    except KeyboardInterrupt as e:
        logger.error(f'measure_weight Error: {e}')
        GPIO.cleanup()
        if SPRAYER:
            gpio_state = sprayer.gpio_state_check(gpio_state)
        

def main():
    logger(f'Starting test of _sprayer.py. ')
    cow_id = '940000501030'
    process(cow_id)