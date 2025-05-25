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

def manage_pins():
    print("On")
    GPIO.output(medicine_pin, GPIO.HIGH)  # Подаём 3.3 вольта на 18-й пин
    GPIO.output(paint_pin, GPIO.HIGH)  # Подаём 3.3 вольта на 18-й пин
    time.sleep(float(ON_TIME))  # Ждём одну секунду
    print("Off")
    GPIO.output(medicine_pin, GPIO.LOW)  # Подаём 3.3 вольта на 18-й пин
    GPIO.output(paint_pin, GPIO.LOW)  # Подаём 3.3 вольта на 18-й пин
    time.sleep(float(OFF_TIME))  # Ждём одну секунду
    

def manage_one_pin(pin):
    pin = medicine_pin if pin == 1 else paint_pin
    print("On")
    GPIO.output(pin, GPIO.HIGH)  # Подаём 3.3 вольта на 18-й пин
    time.sleep(float(ON_TIME))  # Ждём одну секунду
    print("Off")
    GPIO.output(pin, GPIO.LOW)  # Подаём 3.3 вольта на 18-й пин
    time.sleep(float(OFF_TIME))  # Ждём одну секунду
    


def main():
    try:
        print("To Medicine pin: ", medicine_pin)
        print("To Paint pin: ", paint_pin)
        print("Pick 1 or 2 valves to test: ")
        pin = int(input("1 - Medicine, 2 - Paint, 3 - Both: "))
        if pin == 1:
            print("Testing Medicine pin")
        elif pin == 2:
            print("Testing Paint pin")
        else:
            print("Both pins will be tested")
        count = 0
        while(True):
            count += 1
            if pin == 1:
                manage_one_pin(pin)
            elif pin == 2:
                manage_one_pin(pin)
            else:
                manage_pins()

    except KeyboardInterrupt as e:
        print("Ok! Bye!")
        print("Count of cycles: ", count)
        GPIO.cleanup()  # Возвращаем пины в исходное состояние

main()
