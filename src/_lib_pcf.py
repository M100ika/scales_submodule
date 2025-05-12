#!/usr/bin/python3

"""File containing all working functions and algorithms for determining the weight of the animal and spraying.
Author: Aidar Alimbayev and Suieubayev Maxat
Contact: maxat.suieubayev@gmail.com
Number: +7 775 818 48 43"""

from datetime import datetime
import json
import requests
import socket
import binascii
import timeit
import statistics
import time
from collections import Counter
from loguru import logger
import _values_class as value_data
import _adc_data as ADC
from _chafon_rfid_lib import RFIDReader
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    from __gpio_simulator import MockGPIO as GPIO

from _sql_database import SqlDatabase

from _config_manager import ConfigManager
from _sprayer import Sprayer
from _glb_val import *
import select

config_manager = ConfigManager()

def start_obj():
    try:
        obj = ADC.ArduinoSerial(PORT)
        obj.connect()
        offset, scale = float(config_manager.get_setting("Calibration", "offset")), float(config_manager.get_setting("Calibration", "scale"))
        obj.set_offset(offset)
        obj.set_scale(scale)
        return obj
    except Exception as e:
        logger.error(f'Error connecting: {e}')


def start_filter(obj):
    try:
        for i in range(5):
            obj.calc_mean()
            obj.set_arr([])
    except Exception as e:
        logger.error(f'start filter function Error: {e}')


def _set_power_RFID_ethernet():
    try:
        logger.info(f"Start configure antenna power")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((TCP_IP, TCP_PORT))
        s.send(bytearray(RFID_READER_POWER))
        data = s.recv(BUFFER_SIZE)
        recieved_data = str(binascii.hexlify(data))
        check_code = "b'4354000400210143'"
        if recieved_data == check_code:
            logger.info(f"operation succeeded")
        else: 
            logger.info(f"Denied!")
    except Exception as e:
        logger.error(f"_set_power_RFID_ethernet: An error occurred: {e}")
    finally:
        s.close()     

def __connect_rfid_reader_ethernet():
    command = bytearray([0x53, 0x57, 0x00, 0x06, 0xff, 0x01, 0x00, 0x00, 0x00, 0x50])
    s = None
    try:
        logger.debug("Starting RFID Ethernet read cycle...")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(RFID_TIMEOUT)
        s.connect((TCP_IP, TCP_PORT))

        # Очистим буфер перед отправкой команды (на всякий случай)
        try:
            while True:
                s.recv(BUFFER_SIZE)
        except socket.timeout:
            pass
        except Exception:
            pass

        s.send(command)
        time.sleep(0.2)

        ready = select.select([s], [], [], RFID_TIMEOUT)
        if ready[0]:
            data = s.recv(BUFFER_SIZE)
            full_animal_id = binascii.hexlify(data).decode('utf-8')

            logger.debug(f'Raw RFID response: {full_animal_id}')
            logger.debug(f'Response length: {len(full_animal_id)} characters')

            if len(full_animal_id) < 40:
                logger.warning("RFID response too short or invalid.")
                return None

            corrected_rfid = extract_epc_from_raw(full_animal_id)
            if corrected_rfid:
                logger.info(f'Corrected RFID: {corrected_rfid}')
                return corrected_rfid
            else:
                logger.warning('Failed to extract RFID from response.')
                return None
        else:
            logger.warning("No data received from RFID reader within timeout.")
            return None

    except Exception as e:
        logger.error(f'Error during RFID Ethernet read: {e}')
        return None

    finally:
        if s:
            try:
                s.close()
                logger.debug("RFID socket closed.")
            except Exception as e:
                logger.warning(f"Error closing RFID socket: {e}")



def __connect_rfid_reader_ethernet_2():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((TCP_IP, TCP_PORT))
            s.settimeout(RFID_TIMEOUT)

            # Отправляем команду на считывание метки
            command = bytearray([0x53, 0x57, 0x00, 0x06, 0xff, 0x01, 0x00, 0x00, 0x00, 0x50])
            s.send(command)
            time.sleep(0.2)

            ready = select.select([s], [], [], RFID_TIMEOUT)
            if ready[0]:
                data = s.recv(BUFFER_SIZE)
                full_animal_id = binascii.hexlify(data).decode('utf-8')

                logger.info(f'Raw RFID response: {full_animal_id}')
                logger.info(f'Response length: {len(full_animal_id)} characters')

                # Универсальная обработка EPC
                corrected_rfid = extract_epc_from_raw(full_animal_id)
                if corrected_rfid:
                    logger.info(f'Corrected RFID: {corrected_rfid}')
                    return corrected_rfid
                else:
                    logger.warning('Failed to extract RFID.')
                    return None
            else:
                logger.info("No RFID data received within timeout")
                return None

    except Exception as e:
        logger.error(f'Error connect RFID reader: {e}')
        return None


def extract_epc_from_raw(raw_data):
    """
    Универсальная функция для извлечения EPC из ответа RFID-ридера.
    Убирает CRC и адаптируется к разным форматам меток.
    """
    if len(raw_data) < 40:
        logger.warning("RFID response is too short.")
        return None

    # Находим возможные позиции начала EPC (обычно начинается после заголовка)
    start_positions = [40, 44, 48]  # Возможные позиции EPC

    for start in start_positions:
        epc_candidate = raw_data[start:start + 24]  # EPC 12 байт (24 символа)
        
        if len(epc_candidate) == 24:
            # Удаляем последние 4 символа (CRC)
            corrected_epc = epc_candidate[:-4]
            return corrected_epc

    return None


def post_median_data(animal_id, weight_finall, type_scales, sql_db): # Sending data into Igor's server through JSON
    try:
        logger.debug(f'START SEND DATA TO SERVER:')
        url = config_manager.get_setting("Parameters", "median_url")
        headers = {'Content-type': 'application/json'}
        data = {"AnimalNumber" : animal_id,
                "Date" : str(datetime.now()),
                "Weight" : weight_finall,
                "ScalesModel" : type_scales}
        answer = requests.post(url, data=json.dumps(data), headers=headers, timeout=30)
        logger.debug(f'Answer from server: {answer}') # Is it possible to stop on this line in the debug?
        logger.debug(f'Content from main server: {answer.content}')
        if answer.status_code != 200:
            sql_db.no_internet(data)
            logger.error(f'Response status code: {answer.status_code}')
    except requests.exceptions.RequestException as e:
        logger.error(f'Error sending data to server: {e}')
        if SQL_ON:
            database = SqlDatabase()
            database.no_internet(data)
    else:
        logger.info('Data sent successfully')


def post_array_data(type_scales, animal_id, weight_list, weighing_start_time, weighing_end_time, sql_db):
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
        post = requests.post(url, data=json.dumps(data), headers=headers, timeout=30)
        logger.debug(f'Post Data: {data}')
        logger.debug(f'Answer from server: {post}') # Is it possible to stop on this line in the debug?
        logger.debug(f'Content from main server: {post.content}')
        if post.status_code != 200:
            sql_db.no_internet(data)
            logger.error(f'Response status code: {post.status_code}')
    except requests.exceptions.RequestException as e:
        logger.error(f'Error post data: {e}')
        if SQL_ON:
            database = SqlDatabase()
            database.no_internet(data)


def __input_with_timeout(timeout):
    import sys, select

    logger.info(f"You have {int(timeout)} seconds to respond.")
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    if ready:
        return sys.stdin.readline().strip()
    else:
        logger.warning("Input timed out.")
        logger.error("User input timed out.")


def __calibrate(timeout):
    start_time = time.time()

    def time_remaining():
        return max(0, timeout - (time.time() - start_time))

    try:
        logger.info(f'\033[1;33mStarting the calibration process.\033[0m')
        arduino = ADC.ArduinoSerial(config_manager.get_setting("Parameters", "arduino_port"), 9600, timeout=30)
        arduino.connect()

        logger.info(f"Ensure the scale is clear. Press any key once it's empty and you're ready to proceed.")
        time.sleep(1)
        __input_with_timeout(time_remaining())

        offset = arduino.calib_read_mediana()
        logger.info("Offset: {}".format(offset))
        arduino.set_offset(offset)

        logger.info("Place a known weight on the scale and then press any key to continue.")
        __input_with_timeout(time_remaining())

        measured_weight = (arduino.calib_read_mediana() - arduino.get_offset())
        logger.info("Please enter the item's weight in kg.\n>")
        
        item_weight = __input_with_timeout(time_remaining())
        scale = int(measured_weight) / int(item_weight)
        arduino.set_scale(scale)

        logger.info(f"\033[1;33mCalibration complete.\033[0m")
        logger.info(f'Calibration details\n\n —Offset: {offset}, \n\n —Scale factor: {scale}')
        
        config_manager.update_setting("Calibration", "Offset", offset)
        config_manager.update_setting("Calibration", "Scale", scale)

        arduino.disconnect()
        del arduino

    except TimeoutError:
        logger.error("Calibration timed out.")
        arduino.disconnect()
        del arduino
    except Exception as e:
        logger.error(f'Calibration failed: {e}')
        arduino.disconnect()
        del arduino


def _rfid_offset_calib():
    try:
        logger.info(f'\033[1;33mStarting the RFID taring process.\033[0m')
        arduino = ADC.ArduinoSerial(ARDUINO_PORT, 9600, timeout=1)
        arduino.connect()
        offset = arduino.calib_read_mediana()
        arduino.set_offset(offset)
        config_manager.update_setting("Calibration", "Offset", offset)
        logger.info(f'Calibration details\n\n —Offset: {offset}')
        arduino.disconnect()
        del arduino
        logger.info(f'\033[1;33mRFID taring process finished succesfully.\033[0m')
    except:
        logger.error(f'RFID taring process Failed')
        arduino.disconnect()


def _rfid_scale_calib():
    try:
        logger.info(f'\033[1;33mStarting the RFID scale calibration process.\033[0m')
        logger.info(f'\033There should be {CALIBRATION_WEIGHT} kg.\033[')
        arduino = ADC.ArduinoSerial(ARDUINO_PORT, 9600, timeout=1)
        arduino.connect()
        offset = float(config_manager.get_setting("Calibration", "Offset"))
        mediana = arduino.calib_read_mediana()
        logger.info(f'Mediana: {mediana}\noffset: {offset}')
        measured_weight = (mediana - offset)
        logger.info(f'measured_weight: {measured_weight}\nCALIBRATION_WEIGHT: {CALIBRATION_WEIGHT}')
        scale = measured_weight/CALIBRATION_WEIGHT
        logger.info(f'calibration weight is: {CALIBRATION_WEIGHT}')
        arduino.set_scale(scale)
        config_manager.update_setting("Calibration", "Scale", scale)
        logger.info(f'Calibration details\n\n —Scale factor: {scale}')
        arduino.disconnect()
        del arduino
        logger.info(f'\033[1;33mRFID scale calibration process finished succesfully.\033[0m')
    except:
        logger.error(f'calibrate Fail')
        arduino.disconnect()


def _calibrate_or_start():
    try:
        logger.info(f'\nTo calibrate the equipment, put a tick in the settings to calibration mode:\nActaul state is {"CALIBRATION_ON" if CALIBRATION_MODE else "CALIBRATION_OFF"}')
        if CALIBRATION_MODE:
            __calibrate(timeout=120)

    except Exception as e:
        logger.error(f'Calibrate or start Error: {e}')


def __animal_rfid():
    try:
        if RFID_READER_USB:
            rfid_reader = RFIDReader()
            return rfid_reader.connect()
        else:
            cow_id = __connect_rfid_reader_ethernet() 
            if cow_id is not None:
                logger.info(f'cow_id__animal_rfid: {cow_id}') 
            return cow_id
    except Exception as e:
        logger.error(f'RFID reader error: {e}')


def __process_calibration(animal_id):
    try:
        if RFID_CABLIBRATION_MODE:
            if animal_id == CALIBRATION_TARING_RFID:
                _rfid_offset_calib()
                return True
            elif animal_id == CALIBRATION_SCALE_RFID:
                _rfid_scale_calib()   
                return True     
        return False
    except Exception as e:
        logger.error(f'Calibration with RFID: {e}')


def scales_v71():
    try:
        _calibrate_or_start()
        if RFID_READER_USB == False:
            _set_power_RFID_ethernet()
        
        sql_db = SqlDatabase(db_path='sql_table.db')
        last_internet_check = time.time()

        while True:
            cow_id = __animal_rfid()  # Считывание меток
            if cow_id is not None:
                logger.info(f'scales_v71_cow_id: {cow_id}') 
            calib_id = __process_calibration(cow_id) 
            
            if calib_id == False and cow_id != None:  
                arduino = start_obj()   # Создаем объект
                time.sleep(1)   # задержка для установления связи между rasp и arduino
            
                weight_finall, weight_array, weighing_start_time, most_common_animal_id = measure_weight(arduino, cow_id) 
                
                logger.info("main: weight_finall", weight_finall) 
                weighing_end_time = str(datetime.now()) # Время окончания измерения

                if str(weight_finall) > '0':
                    logger.info("main: Send data to server")
                    post_array_data(TYPE_SCALES, most_common_animal_id, weight_array, weighing_start_time, weighing_end_time, sql_db)
                    post_median_data(most_common_animal_id, weight_finall, TYPE_SCALES, sql_db) # Send data to server by JSON post request
                arduino.disconnect() # Закрываем связь

            current_time = time.time()
            if current_time - last_internet_check > INTERNET_CHECK_INTERVAL:
                sql_db.internet_on()
                last_internet_check = current_time

    except KeyboardInterrupt as e:
        arduino.disconnect()
        logger.error(f'Bye bye: {e}')
            
    except Exception as k:
        arduino.disconnect()
        logger.error(f'Main error: {k}')


def is_valid_rfid(animal_id):
    """
    Проверка, что animal_id выглядит как более-менее адекватный
    """
    return (
        animal_id and                        # не None и не пустая строка
        len(animal_id) >= 8 and              # хотя бы 8 символов
        len(animal_id) <= 64 and             # ограничим максимум
        any(c.isalnum() for c in animal_id)  # хотя бы одна буква или цифра
    )


def _take_weight(weight, count = 50) -> float:
    try:
        weight.clean_arr()  # Очистим массив перед стартом
        for _ in range(count):  # Например, взять 50 значений
            weight.calc_mean()
            time.sleep(0.05)  # Делаем паузу, чтобы усреднить медленнее

        #logger.info(f'ARRAY {weight.get_arr()}')
        return sum(weight.get_arr()) / len(weight.get_arr())
    except Exception as e:
        logger.error(f'Error _take_weight: {e}')


def measure_weight(obj, cow_id: str) -> tuple:
    try:
        animal_id_list = []
        animal_id_list.append(cow_id)
        weight_arr = []
        start_filter(obj)
        next_time = time.time() + 1
        
        drink_start_time = timeit.default_timer()
        gpio_state = False
        start_timedate = str(datetime.now())
        
        values = value_data.Values(
            drink_start_time, 0, TYPE_SCALES, cow_id, 0, '0', 0, 0, 0, 0, True
        )

        if SPRAYER:
            sprayer = Sprayer(values)
        
        weight_on_moment = _take_weight(obj, 20)
        logger.info(f'Weight on the moment: {weight_on_moment}')

        while weight_on_moment > 20:

            current_animal_id = __animal_rfid()
            if is_valid_rfid(current_animal_id):
                animal_id_list.append(current_animal_id)
                logger.info(f"RFID added to list: {current_animal_id}")
            else:
                logger.warning(f"Ignored suspicious RFID: {current_animal_id}")

            weight_on_moment = _take_weight(obj, 20)
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
                weight_arr.append(weight_on_moment)
                next_time = time.time() + 1
                logger.debug(f'Array weights: {weight_arr}')

            

        GPIO.cleanup()

        if not weight_arr:
            logger.info("null weight list")
            return 0, [], '', ''

        most_common_animal_id = None
        most_common_animal_id = Counter(animal_id_list).most_common(1)[0][0] if animal_id_list else "UNKNOWN"
        weight_finall = statistics.median(weight_arr)
        if SPRAYER:
            gpio_state = sprayer.gpio_state_check(gpio_state)

        return weight_finall, weight_arr, start_timedate, most_common_animal_id

    except Exception as e:
        logger.error(f'measure_weight Error: {e}')
        GPIO.cleanup()
        return 0, [], ''



