import time
import threading
from loguru import logger
from _config_manager import ConfigManager
from serial.tools import list_ports

from chafon_rfid.base import CommandRunner, ReaderCommand, ReaderInfoFrame, ReaderResponseFrame, ReaderType
from chafon_rfid.command import CF_GET_READER_INFO, CF_SET_BUZZER_ENABLED, CF_SET_RF_POWER
from chafon_rfid.transport_serial import SerialTransport
from chafon_rfid.uhfreader288m import G2InventoryCommand, G2InventoryResponseFrame


class RFIDReader:
    def __init__(self):
        self.config_manager = ConfigManager()
        port = self.config_manager.get_setting("RFID_Reader", "reader_port")
        self.reader_port = None if port == "Отсутствует" else port
        initial_power = int(self.config_manager.get_setting("RFID_Reader", "reader_power"))
        self.reader_power = self._closest_number(initial_power)
        self.reader_timeout = float(self.config_manager.get_setting("RFID_Reader", "reader_timeout"))
        self.reader_buzzer = bool(int(self.config_manager.get_setting("RFID_Reader", "reader_buzzer")))

        self.transport = None
        self.runner = None
        self.read_thread = None
        self.running = False

    def _closest_number(self, power):
        options = [1, 3, 5, 7, 10, 15, 20, 26]
        return min(options, key=lambda x: abs(x - power))

    def find_rfid_reader(self):
        ports = list_ports.comports()
        for port in ports:
            try:
                transport = SerialTransport(device=port.device, timeout=0.2)
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

    def open(self):
        """
        Открывает соединение с ридером и настраивает мощность и буззер.
        """
        if not self.reader_port:
            raise ValueError("RFID reader port not set. Call find_rfid_reader() first.")

        self.transport = SerialTransport(device=self.reader_port, timeout=self.reader_timeout)
        self.runner = CommandRunner(self.transport)

        self._run_command(ReaderCommand(CF_SET_RF_POWER, data=[self.reader_power]))
        self._run_command(ReaderCommand(CF_SET_BUZZER_ENABLED, data=[1 if self.reader_buzzer else 0]))

        logger.info(f"Соединение установлено с {self.reader_port}")

    def start_continuous_read(self, on_tag_callback, interval=0.3):
        """
        Запускает непрерывное считывание в фоне.
        `on_tag_callback` вызывается при каждой считанной метке.
        """
        if not self.runner or not self.transport:
            raise RuntimeError("Call open() first.")

        self.running = True
        inventory_cmd = G2InventoryCommand(q_value=4, antenna=0x80)
        last_epc = None

        def read_loop():
            logger.info("Старт фонового чтения меток")
            while self.running:
                try:
                    self.transport.write(inventory_cmd.serialize())
                    time.sleep(0.02)
                    frame = self.transport.read_frame()
                    if frame:
                        resp = G2InventoryResponseFrame(frame)
                        for tag in resp.get_tag():
                            epc = tag.epc.hex()
                            on_tag_callback(epc)
                except Exception as e:
                    logger.warning(f"Ошибка при чтении: {e}")
                time.sleep(interval)

            logger.info("Фоновое чтение остановлено")

        self.read_thread = threading.Thread(target=read_loop, daemon=True)
        self.read_thread.start()

    def stop_continuous_read(self):
        self.running = False
        if self.read_thread:
            self.read_thread.join(timeout=2)

    def close(self):
        self.stop_continuous_read()
        if self.transport:
            self.transport.close()
            logger.info("Соединение с ридером закрыто")
        self.transport = None
        self.runner = None

    def _run_command(self, command: ReaderCommand) -> int:
        self.transport.write(command.serialize())
        resp = ReaderResponseFrame(self.transport.read_frame())
        return resp.result_status
