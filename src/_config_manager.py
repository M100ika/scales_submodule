import configparser
import os
from loguru import logger
from _headers import CONFIG_FILE_PATH


class ConfigManager:
    def __init__(self, path=CONFIG_FILE_PATH):
        self.path = path
        if not os.path.exists(self.path):
            self.create_config()

    def create_config(self):
        try:
            config = configparser.ConfigParser()
            config.add_section("Parameters")
            config.add_section("Calibration")
            config.add_section("DbId")
            config.add_section("RFID_Reader")
            config.add_section("Relay")

            config.set("Parameters", "model", "feeder_model_1")    
            config.set("Parameters", "type", "Feeder") 
            config.set("Parameters", "serial_number", "feeder0423v21-1") 
            config.set("Parameters", "url", "https://smart-farm.kz:8502/api/v2/RawFeedings") 
            config.set("Parameters", "median_url", "http://194.4.56.86:8501/api/weights") 
            config.set("Parameters", "array_url", "https://smart-farm.kz:8502/v2/OneTimeWeighings") 
            config.set("Parameters", "arduino_port", "dev/ttyUSB0") 
            config.set("Parameters", "debug", "1")
            
            config.set("Calibration", "taring_rfid", "")    
            config.set("Calibration", "scaling_rfid", "")    
            config.set("Calibration", "weight", "80")    
            config.set("Calibration", "offset", "16766507")    
            config.set("Calibration", "scale", "-3358.285714285714")

            config.set("DbId", "id", "0") 
            config.set("DbId", "version", "7.1")    

            config.set("Relay", "sensor_pin", "17")

            config.set("RFID_Reader", "reader_usb", "0")
            config.set("RFID_Reader", "reader_port", "/dev/ttyUSB0")
            config.set("RFID_Reader", "reader_power", "26")
            config.set("RFID_Reader", "reader_timeout", "2")
            config.set("RFID_Reader", "reader_buzzer", "1")

            with open(self.path, "w") as config_file:
                config.write(config_file)
        except ValueError as e:
            logger.error(f'ConfigManager, create_config method error: {e}')

    def get_config(self):
        try:
            config = configparser.ConfigParser()
            config.read(self.path)
            return config
        except ValueError as e:
            logger.error(f'ConfigManager, get_config method error: {e}')

    def get_setting(self, section, setting):
        try:
            config = self.get_config()
            value = config.get(section, setting)
            return value
        except ValueError as e:
            logger.error(f'ConfigManager, get_setting method error: {e}')

    def update_setting(self, section, setting, value):
        try:
            config = self.get_config()
            config.set(section, setting, str(value))
            with open(self.path, "w") as config_file:
                config.write(config_file)
        except ValueError as e:
            logger.error(f'ConfigManager, update_setting method error: {e}')
