import time
from loguru import logger
from _config_manager import ConfigManager
import serial
from serial.tools import list_ports

from chafon_rfid.base import CommandRunner, ReaderCommand, ReaderInfoFrame, ReaderResponseFrame, ReaderType
from chafon_rfid.command import (CF_GET_READER_INFO, CF_SET_BUZZER_ENABLED, CF_SET_RF_POWER)
from chafon_rfid.response import G2_TAG_INVENTORY_STATUS_MORE_FRAMES
from chafon_rfid.transport_serial import SerialTransport
from chafon_rfid.uhfreader288m import G2InventoryCommand, G2InventoryResponseFrame

class RFIDReader:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.reader_port = self.config_manager.get_setting("RFID_Reader", "reader_port")
        if self.reader_port == "Отсутствует":
            self.reader_port = None
        initial_power = int(self.config_manager.get_setting("RFID_Reader", "reader_power"))
        self.reader_power = self.closest_number(initial_power)
        self.reader_timeout = int(self.config_manager.get_setting("RFID_Reader", "reader_timeout"))
        self.reader_buzzer = int(self.config_manager.get_setting("RFID_Reader", "reader_buzzer"))


    def closest_number(self, power):
        numbers = [1, 3, 5, 7, 10, 15, 20, 26]
        if power < min(numbers):
            return min(numbers)
        return min(numbers, key=lambda x: abs(x - power))


    def find_rfid_reader(self):
        ports = list(list_ports.comports())
        for port in ports:
            try:
                transport = SerialTransport(device=port.device)
                runner = CommandRunner(transport)
                get_reader_info_cmd = ReaderCommand(CF_GET_READER_INFO)
                
                response = runner.run(get_reader_info_cmd)
                reader_info = ReaderInfoFrame(response)
                
                if reader_info.type:  
                    self.config_manager.update_setting("RFID_Reader", "reader_port", port.device)
                    return port.device
                    
            except (OSError, serial.SerialException, ValueError):
                pass
        
        self.config_manager.update_setting("RFID_Reader", "reader_port", "Отсутствует")
        return None


    def _get_reader_type(self):
        get_reader_info = ReaderCommand(CF_GET_READER_INFO)
        self.transport = SerialTransport(device=self.reader_port)
        self.runner = CommandRunner(self.transport)
        reader_info = ReaderInfoFrame(self.runner.run(get_reader_info))
        return reader_info.type

    def _run_command(self, command):
        self.transport.write(command.serialize())
        status = ReaderResponseFrame(self.transport.read_frame()).result_status
        return status

    def _set_power(self):
        return self._run_command(ReaderCommand(CF_SET_RF_POWER, data=[self.reader_power]))

    def _set_buzzer_enabled(self):
        return self._run_command(ReaderCommand(CF_SET_BUZZER_ENABLED, data=[self.reader_buzzer and 1 or 0]))

    def connect(self):
        tag_id = None

        try:
            reader_type = self._get_reader_type()
            if reader_type in (ReaderType.UHFReader86, ReaderType.UHFReader86_1):
                get_inventory_cmd = G2InventoryCommand(q_value=4, antenna=0x80)
                frame_type = G2InventoryResponseFrame
                self._set_power()
                self._set_buzzer_enabled()
            else:
                logger.error(f'Unsupported reader type: {reader_type}')
                return None
        except ValueError as e:
            logger.error(f'Unknown reader type: {e}')
            return None

        start_time = time.time()
        while tag_id is None:
            try:
                self.transport.write(get_inventory_cmd.serialize())
                inventory_status = None
                while inventory_status is None or inventory_status == G2_TAG_INVENTORY_STATUS_MORE_FRAMES:
                    if time.time() - start_time > self.reader_timeout:
                        logger.info("Timeout reached, stopping tag reading.")
                        return None
                    resp = frame_type(self.transport.read_frame())
                    inventory_status = resp.result_status
                    tags_generator = resp.get_tag()
                    try:
                        first_tag = next(tags_generator, None)
                        if first_tag:
                            tag_id = first_tag.epc.hex()
                            break
                    except StopIteration:
                        continue
            except KeyboardInterrupt:
                logger.error("Operation cancelled by user.")
                break
            except Exception as e:
                logger.error(f'Error: {e}')
                continue

        self.transport.close()
        return tag_id[16:25] if tag_id else None
        