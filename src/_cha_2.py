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
        port = self.config_manager.get_setting("RFID_Reader", "reader_port")
        self.reader_port = None if port == "Отсутствует" else port
        initial_power = int(self.config_manager.get_setting("RFID_Reader", "reader_power"))
        self.reader_power = self._closest_number(initial_power)
        self.reader_timeout = int(self.config_manager.get_setting("RFID_Reader", "reader_timeout"))
        self.reader_buzzer = bool(int(self.config_manager.get_setting("RFID_Reader", "reader_buzzer")))

        # Pre-create inventory command
        self.inventory_cmd = G2InventoryCommand(q_value=4, antenna=0x80)
        self.frame_type = G2InventoryResponseFrame
        self.transport = None
        self.runner = None

    def _closest_number(self, power):
        options = [1, 3, 5, 7, 10, 15, 20, 26]
        if power < min(options):
            return min(options)
        return min(options, key=lambda x: abs(x - power))

    def find_rfid_reader(self):
        ports = list_ports.comports()
        for port in ports:
            try:
                transport = SerialTransport(device=port.device)
                runner = CommandRunner(transport)
                response = runner.run(ReaderCommand(CF_GET_READER_INFO))
                info = ReaderInfoFrame(response)
                if info.type:
                    self.config_manager.update_setting("RFID_Reader", "reader_port", port.device)
                    return port.device
            except Exception:
                continue
        self.config_manager.update_setting("RFID_Reader", "reader_port", "Отсутствует")
        return None

    def open(self, timeout: float = 0.1):
        """
        Открывает порт и настраивает ридер: мощность и бузер.
        """
        if not self.reader_port:
            raise ValueError("RFID reader port not set. Call find_rfid_reader() first.")
        self.transport = SerialTransport(device=self.reader_port, timeout=timeout)
        self.runner = CommandRunner(self.transport)
        # apply power and buzzer settings once
        self._run_command(ReaderCommand(CF_SET_RF_POWER, data=[self.reader_power]))
        self._run_command(ReaderCommand(CF_SET_BUZZER_ENABLED, data=[1 if self.reader_buzzer else 0]))

    def read_tag(self, timeout: float = None) -> str:
        """
        Читает одну метку. Возвращает EPC hex или None.
        """
        if not self.transport or not self.runner:
            raise RuntimeError("Transport not open. Call open() before read_tag().")

        try:
            raw_info = self.runner.run(ReaderCommand(CF_GET_READER_INFO))
            if len(raw_info) < 8:
                logger.warning("Ответ от ридера слишком короткий. Пропуск.")
                return None
            info = ReaderInfoFrame(raw_info)
        except Exception as e:
            logger.error(f"Ошибка при получении информации о ридере: {e}")
            return None

        if info.type not in (ReaderType.UHFReader86, ReaderType.UHFReader86_1):
            return None

        if not self.transport:
            logger.error("Transport закрыт. Прерываем чтение.")
            return None

        start = time.time()
        send_interval = 0.2  # каждые 200 мс посылать команду
        last_send = 0

        while True:
            if timeout and (time.time() - start) > timeout:
                logger.debug("RFID read timeout")
                return None

            if (time.time() - last_send) > send_interval:
                try:
                    self.transport.write(self.inventory_cmd.serialize())
                    last_send = time.time()
                except Exception as e:
                    logger.error(f"Send inventory command failed: {e}")
                    return None

            try:
                frame = self.transport.read_frame()
                if not frame:
                    continue
                resp = self.frame_type(frame)
            except IndexError:
                logger.debug("Empty frame, retrying")
                continue
            except Exception as e:
                logger.error(f"Error reading frame: {e}")
                continue

            if resp.result_status != G2_TAG_INVENTORY_STATUS_MORE_FRAMES:
                tags = resp.get_tag()
                if not tags:
                    continue
                return tags[0].epc.hex()
                    
    def close(self):
        """
        Закрывает порт.
        """
        if self.transport:
            self.transport.close()
            self.transport = None
            self.runner = None

    def _run_command(self, command: ReaderCommand) -> int:
        """
        Отправляет одиночную команду и возвращает статус.
        """
        self.transport.write(command.serialize())
        resp = ReaderResponseFrame(self.transport.read_frame())
        return resp.result_status
