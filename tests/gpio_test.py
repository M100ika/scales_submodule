#!/usr/bin/python3

import RPi.GPIO as GPIO
import time
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / 'src'))

from _config_manager import ConfigManager

ON_TIME = 1
OFF_TIME = 1
config_manager = ConfigManager()

medicine_pin = int(config_manager.get_setting("Sprayer", "medicine_pin"))
paint_pin = int(config_manager.get_setting("Sprayer", "paint_pin"))

GPIO.setmode(GPIO.BCM)  # Устанавливаем BCM-нумерацию пинов
GPIO.setup(medicine_pin, GPIO.OUT)  # Устанавливаем 18-й пин как выход
GPIO.output(medicine_pin, GPIO.LOW)
GPIO.setup(paint_pin, GPIO.OUT)  # Устанавливаем 18-й пин как выход
GPIO.output(paint_pin, GPIO.LOW)

def main():
    try:
        print("To Medicine pin: ", medicine_pin)
        print("To Paint pin: ", paint_pin)
        count = 0
        while(True):
            print("On")
            GPIO.output(medicine_pin, GPIO.HIGH)  # Подаём 3.3 вольта на 18-й пин
            GPIO.output(paint_pin, GPIO.HIGH)  # Подаём 3.3 вольта на 18-й пин
            #GPIO.output(23, GPIO.HIGH)
            time.sleep(float(ON_TIME))  # Ждём одну секунду
            count += 1
            print("off")
            GPIO.output(medicine_pin, GPIO.LOW)  # Подаём 3.3 вольта на 18-й пин
            GPIO.output(paint_pin, GPIO.LOW)  # Подаём 3.3 вольта на 18-й пин

            #GPIO.output(23, GPIO.LOW)
            time.sleep(float(OFF_TIME))

    except KeyboardInterrupt as e:
        print("Ok! Bye!")
        print("Count of cycles: ", count)
        GPIO.cleanup()  # Возвращаем пины в исходное состояние

main()
