#!/usr/bin/env python

# Minimal example to peform a single tag inventory. Shows examples of serial or TCP/IP
# communication with a reader.
#
# For readers that support RSSI values returned with the tags (e.g. fixed reader series or UHF
# modules), comment out the get_inventory_uhfreader18 command and G2InventoryResponseFrame18
# format, and instead use the lines immediately preceding them (get_inventory_288 and
# G2InventoryResponseFrame288)

from chafon_rfid.base import CommandRunner, ReaderCommand, ReaderInfoFrame
from chafon_rfid.command import CF_GET_READER_INFO, G2_TAG_INVENTORY
from chafon_rfid.response import G2_TAG_INVENTORY_STATUS_MORE_FRAMES
from chafon_rfid.transport import TcpTransport, MockTransport
from chafon_rfid.transport_serial import SerialTransport
from chafon_rfid.uhfreader18 import G2InventoryResponseFrame as G2InventoryResponseFrame18
from chafon_rfid.uhfreader288m import G2InventoryCommand, G2InventoryResponseFrame as G2InventoryResponseFrame288
import time

# Настройка транспорта
transport = TcpTransport(reader_addr='192.168.1.250', reader_port=6000)
runner = CommandRunner(transport)

time.sleep(1)

# Получение информации о считывателе
get_reader_info = ReaderCommand(CF_GET_READER_INFO)
reader_info = ReaderInfoFrame(runner.run(get_reader_info))
reader_type = reader_info.type

# Определение типа считывателя и соответствующая обработка
if reader_type == 'UHFReader18':
    get_inventory_cmd = ReaderCommand(G2_TAG_INVENTORY)
    g2_response_class = G2InventoryResponseFrame18
elif reader_type == 'UHFReader288M':
    get_inventory_cmd = G2InventoryCommand(q_value=4, antenna=0x80)
    g2_response_class = G2InventoryResponseFrame288

# Выполнение команды инвентаризации меток
transport.write(get_inventory_cmd.serialize())
inventory_status = None
while inventory_status is None or inventory_status == G2_TAG_INVENTORY_STATUS_MORE_FRAMES:
    g2_response = g2_response_class(transport.read_frame())
    inventory_status = g2_response.result_status
    for tag in g2_response.get_tag():
        print('Antenna %d: EPC %s, RSSI %s' % (tag.antenna_num, tag.epc.hex(), tag.rssi))

transport.close()