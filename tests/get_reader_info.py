import socket
import struct
from loguru import logger

TCP_IP = '192.168.1.250'
TCP_PORT = 60000
BUFFER_SIZE = 1024

# Команда инвентаризации ISO18000-6C (бесконечно до остановки)
def build_inventory_command():
    base = bytearray([
        0xCF,  # HEAD
        0xFF,  # ADDR
        0x00, 0x01,  # CMD
        0x05,  # LEN
        0x00,  # InvType = 0x00 (по времени)
        0x00, 0x00, 0x00, 0x00  # InvParam = 0
    ])
    crc = crc16_ccitt(base)
    base.extend([crc >> 8, crc & 0xFF])
    return base

# CRC16-CCITT (poly 0x8408, init 0xFFFF)
def crc16_ccitt(data, preset=0xFFFF, poly=0x8408):
    crc = preset
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ poly
            else:
                crc >>= 1
    return crc & 0xFFFF

# Разбор пакета и извлечение EPC
def parse_epc_response(data: bytes):
    tags = []
    idx = 0
    while idx < len(data):
        if data[idx] != 0xCF:
            idx += 1
            continue

        try:
            length = data[idx + 4]
            frame = data[idx:idx + 5 + length + 2]  # 5 байт заголовка, len, и 2 байта CRC
            if len(frame) < 7:
                break
            cmd = frame[2:4]
            if cmd == b'\x80\x01' and frame[5] == 0x00:  # EPC inventory response, Status = 0x00
                epc_len = frame[6]
                epc_data = frame[7:7 + epc_len]
                tags.append(epc_data.hex())
            idx += len(frame)
        except Exception:
            idx += 1
    return tags

def run_test():
    command = build_inventory_command()
    logger.info("Connecting to RFID reader...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(3)
        s.connect((TCP_IP, TCP_PORT))
        logger.info("Sending inventory command...")
        s.send(command)

        unique_tags = set()

        try:
            while True:
                data = s.recv(BUFFER_SIZE)
                if not data:
                    break
                tags = parse_epc_response(data)
                for tag in tags:
                    if tag not in unique_tags:
                        unique_tags.add(tag)
                        logger.success(f"New tag detected: {tag}")
        except KeyboardInterrupt:
            logger.info("Interrupted by user.")
        except socket.timeout:
            logger.warning("Timeout waiting for data.")
        finally:
            logger.info("Test completed.")
            s.close()

run_test()
