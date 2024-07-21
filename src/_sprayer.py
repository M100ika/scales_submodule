import requests
from requests.exceptions import HTTPError
import RPi.GPIO as GPIO
import timeit
import json
from loguru import logger
from _config_manager import ConfigManager

config_manager = ConfigManager()


class Sprayer:
    def __init__(self, values):
        self.values = values
        self.spray_post = config_manager.get_setting("Sprayer", "post_url")
        self.headers = config_manager.get_setting("Sprayer", "headers")
        self.medicine_pin = int(config_manager.get_setting("Sprayer", "medicine_pin"))
        self.paint_pin = int(config_manager.get_setting("Sprayer", "paint_pin"))
        self.task_url = config_manager.get_setting("Sprayer", "rfid_url_part")
        self.task_url_part = config_manager.get_setting("Sprayer", "post_url")


    def spray_gpio_off(self) -> bool:
        try:
            logger.info("Start spray_gpio_off")
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(True)
            GPIO.setup(int(self.values.pin), GPIO.OUT)
            GPIO.output(int(self.values.pin), GPIO.LOW)
            GPIO.cleanup()
            position = False
            end_time = timeit.default_timer()
            self.values.new_volume = (end_time - self.values.drink_start_time) * 8.3
            post_data = self.spray_json_payload()
            post_res = requests.post(self.spray_post, data=json.dumps(post_data), headers=self.headers, timeout=3)
            logger.info(f'Post status code {post_res.status_code}')
            logger.info(f'GPIO is off. Pin number is {self.values.pin}')
            return position
        except Exception as e:
            logger.error(f"Error: Spray_GPIO_off function isn't working {e}")
            return False

    def spray_gpio_on(self) -> bool:
        try:
            logger.info('Start spray_gpio_on')
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(True)
            GPIO.setup(int(self.values.pin), GPIO.OUT)
            GPIO.output(int(self.values.pin), GPIO.HIGH)
            logger.info(f'Pump turn on is successful. Pin number is {self.values.pin}')
            return True
        except Exception as e:
            logger.error(f"Error: GPIO_on function isn't working {e}")
            self.spray_gpio_off()
            return False

    def spray_json_payload(self) -> dict:
        try:
            logger.debug("Start spray_json_payload function")
            data = {
                "EventDate": '2024-07-04T09:51:35.046Z',
                "TaskId": self.values.task_id,
                "ScalesSerialNumber": self.values.type_scales,
                "SpayerSerialNumber": "s01000001",
                "RFIDNumber": self.values.cow_id,
                "SprayingType": self.values.spraying_type,
                "Volume": self.values.new_volume
            }
            return data
        except Exception as e:
            logger.error(f"Error in spray_json_payload function: {e}")
            return {}

    def request_get(self):
        try:
            cow_id = self.values.cow_id
            type_scales = self.values.type_scales
            url = f'{self.task_url}{type_scales}{self.task_url_part}{cow_id}'
            request_get = requests.get(url, timeout=5).json()
            return request_get
        except Exception as e:
            logger.error(f'request_get function error: {e}')
            return {}

    def spray_json_get(self, request_get_json, get_object=0):
        try:
            logger.info("Start spray_json_get")
            self.values.task_id = request_get_json[get_object]['TaskId']
            self.values.spraying_type = request_get_json[get_object]['SprayingType']
            self.values.volume = request_get_json[get_object]['Volume']
            self.values.server_time = request_get_json[get_object]['ServerTime']
            return self.values
        except BaseException as b:
            logger.error(f"spray_json_get error: {b}")
            return self.values

    def spray(self, position) -> bool:
        try:
            logger.info("Start spray")
            spray_time = self.values.volume / 8.3
            self.values.spray_duration = self.values.drink_start_time + spray_time
            if self.values.spray_duration >= timeit.default_timer():
                logger.info(f'Position is {position}')
                if not position:
                    position = self.spray_gpio_on()
                    return position
                else:
                    return position
            else:
                logger.info('TimeOff')
                position = self.spray_gpio_off()
                return position
        except ValueError as err:
            logger.error(f'Other error occurred: {err}')
            self.spray_gpio_off()
            return False

    def spray_timer(self, position) -> bool:
        try:
            logger.info("Start spray timer check function")
            if self.values.spray_duration >= timeit.default_timer():
                logger.info(f'Time is {self.values.spray_duration} {timeit.default_timer()}')
                if not position:
                    self.spray_gpio_on()
                    position = True
                    return position
                else:
                    return position
            else:
                logger.info('TimeOff')
                position = self.spray_gpio_off()
                return position
        except ValueError as err:
            logger.error(f'Other error occurred: {err}')
            self.spray_gpio_off()
            return False

    def spraying_type(self) -> int:
        try:
            logger.info('Spraying type function start')
            if self.values.spraying_type == 0:
                return self.medicine_pin
            else:
                return self.paint_pin
        except Exception as e:
            logger.error(f'spraying_type function error: {e}')
            return -1

    def spray_main_function(self, position) -> bool:
        try:
            logger.info("Start spray_main_function")
            if not position:
                request_get_json = self.request_get()
                logger.debug(f'JSON Request: {request_get_json}')
                if not request_get_json:
                    logger.info('No tasks there')
                    self.values.flag = True
                    return position
                else:
                    self.values = self.spray_json_get(request_get_json)
                    self.values.pin = self.spraying_type()
                    self.values.drink_start_time = timeit.default_timer()
                    logger.debug(f'Values are: {self.values}')
                    position = self.spray(position)
                    return position
            else:
                position = self.spray_timer(position)
                return position
        except HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err}')
            self.spray_gpio_off()
            return False
        except Exception as err:
            logger.error(f'Other error occurred: {err}')
            self.spray_gpio_off()
            return False

    def gpio_state_check(self, position) -> bool:
        try:
            logger.info("Start gpio_state_check")
            if position:
                position = self.spray_gpio_off()
            return position
        except HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err}')
            self.spray_gpio_off()
            return False
        except Exception as err:
            logger.error(f'Other error occurred: {err}')
            self.spray_gpio_off()
            return False

    def new_start_timer(self, position):
        try:
            logger.info('New start timer function')
            if position:
                return self.values
            else:
                self.values.drink_start_time = timeit.default_timer()
                return self.values
        except ValueError as e:
            logger.error(f'new_start_timer function error: {e}')
            return self.values
