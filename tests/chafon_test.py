import time
import binascii
from chafon_rfid.transport_serial import SerialTransport
from chafon_rfid.uhfreader288m import G2InventoryCommand, G2InventoryResponseFrame
from loguru import logger

DEVICE_PORT = "/dev/ttyUSB0"   # или 'COM3' на Windows
BAUD_RATE = 115200              # Обычно 57600 или 115200
READ_TIMEOUT = 1.0             # Секунды ожидания ответа

def main():
    logger.info("Connecting to USB RFID reader...")

    try:
        transport = SerialTransport(device=DEVICE_PORT, baud_rate=BAUD_RATE, timeout=READ_TIMEOUT)
        logger.success(f"Connected to {DEVICE_PORT} at {BAUD_RATE} baud.")

        inventory_command = G2InventoryCommand(q_value=4, antenna=0x80)

        while True:
            logger.debug("Sending inventory command...")
            transport.write(inventory_command.serialize())

            try:
                response_data = transport.read_frame()
                frame = G2InventoryResponseFrame(response_data)

                for tag in frame.get_tag():
                    epc_hex = tag.epc.hex()
                    logger.success(f"Tag EPC: {epc_hex}")

            except Exception as e:
                logger.warning(f"No tag or error: {e}")

            time.sleep(0.1)

    except Exception as e:
        logger.error(f"Error opening transport: {e}")

    finally:
        logger.info("Closing transport...")
        transport.close()

if __name__ == "__main__":
    main()
