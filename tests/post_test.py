import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / 'src'))

from _config_manager import ConfigManager
import time
import timeit
from datetime import datetime, timedelta
import statistics
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    from __gpio_simulator import MockGPIO as GPIO


from _sprayer import Sprayer
import _values_class as value_data
from _glb_val import *
import json
import json
import requests
    
from loguru import logger

debug_level = "DEBUG" if DEBUG == 1 else "CRITICAL"

"""Инициализация logger для хранения записи о всех действиях программы"""
logger.add(sys.stdout, format="{time} {level} {message}", level=debug_level)  

config_manager = ConfigManager()

def post_median_data(animal_id, weight_finall, type_scales): # Sending data into Igor's server through JSON
    try:
        logger.debug(f'START SEND DATA TO SERVER:')
        url = config_manager.get_setting("Parameters", "median_url")
        headers = {'Content-type': 'application/json'}
        data = {"AnimalNumber" : animal_id,
                "Date" : str(datetime.now()),
                "Weight" : weight_finall,
                "ScalesModel" : type_scales}
        answer = requests.post(url, data=json.dumps(data), headers=headers, timeout=3)
        logger.debug(f'Answer from server: {answer}') # Is it possible to stop on this line in the debug?
        logger.debug(f'Content from main server: {answer.content}')
    except Exception as e:
        logger.error(f'Error send data to server {e}')


def post_array_data(type_scales, animal_id, weight_list, weighing_start_time, weighing_end_time):
    try:
        logger.debug(f'Post data function start')
        url = config_manager.get_setting("Parameters", "array_url")
        headers =  {'Content-Type': 'application/json; charset=utf-8'}
        data = {
                "ScalesSerialNumber": type_scales,
                "WeighingStart": weighing_start_time,
                "WeighingEnd": weighing_end_time,
                "RFIDNumber": animal_id,
                "Data": weight_list
                }  
        post = requests.post(url, data=json.dumps(data), headers=headers, timeout=3)
        logger.debug(f'Post Data: {data}')
        logger.debug(f'Answer from server: {post}') # Is it possible to stop on this line in the debug?
        logger.debug(f'Content from main server: {post.content}')
    except Exception as e:
        logger.error(f'Error post data: {e}')


def main():
    cow_id = '940000401030_test'
    weight_array = [50.00 for i in range(60)]
    #weight_array = [50.06, 49.94, 49.74, 49.76, 49.87, 49.93, 50.02, 49.97, 49.95, 49.98, 49.88, 49.91, 50.2, 179.95, 668.44, 1274.77, 1899.45, 2517.68, 3087.39, 3368.32, 3367.92, 3367.45]
    weighing_start_time = str(datetime.now())
    weighing_end_time = str(datetime.now() + timedelta(seconds=30))
    weight_finall = statistics.median(weight_array)
    post_array_data(TYPE_SCALES, cow_id, weight_array, weighing_start_time, weighing_end_time)
    post_median_data(cow_id, weight_finall, TYPE_SCALES) 


main()