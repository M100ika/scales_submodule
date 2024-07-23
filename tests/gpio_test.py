#!/usr/bin/python3

import RPi.GPIO as GPIO
import time
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / 'src'))

from _config_manager import ConfigManager


config_manager = ConfigManager()

medicine_pin = int(config_manager.get_setting("Sprayer", "medicine_pin"))

GPIO.setmode(GPIO.BCM)  # Устанавливаем BCM-нумерацию пинов
GPIO.setup(medicine_pin, GPIO.OUT)  # Устанавливаем 18-й пин как выход
GPIO.output(medicine_pin, GPIO.LOW)

def main():
    try:
        print("Enter On time: ")
        on_time = input()
        print("Enter off time: ")
        off_time = input()
        count = 0
        while(True):
            print("On")
            GPIO.output(medicine_pin, GPIO.HIGH)  # Подаём 3.3 вольта на 18-й пин
            #GPIO.output(23, GPIO.HIGH)
            time.sleep(float(on_time))  # Ждём одну секунду
            count += 1
            print("off")
            GPIO.output(medicine_pin, GPIO.LOW)  # Подаём 3.3 вольта на 18-й пин
            #GPIO.output(23, GPIO.LOW)
            time.sleep(float(off_time))
    except KeyboardInterrupt as e:
        print("Ok! Bye!")
        print("Count of cycles: ", count)
        GPIO.cleanup()  # Возвращаем пины в исходное состояние

main()
