import sys
from pathlib import Path
from loguru import logger
import time
sys.path.append(str(Path(__file__).resolve().parent.parent / 'src'))
from _cha_2 import RFIDReader

def on_tag(epc):
    logger.info(f"🔷 Метка считана: {epc}")

reader = RFIDReader()
if not reader.reader_port:
    port = reader.find_rfid_reader()
    logger.info(f"Найден ридер: {port}")

reader.open()
reader.start_continuous_read(on_tag)

try:
    while True:
        time.sleep(0.02)
except KeyboardInterrupt:
    reader.close()
