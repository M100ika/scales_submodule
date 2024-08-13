import socket
from chafon_rfid.base import CommandRunner, ReaderCommand, ReaderInfoFrame, ReaderResponseFrame
from chafon_rfid.command import G2_TAG_INVENTORY
from chafon_rfid.transport import TcpTransport
from chafon_rfid.uhfreader288m import G2InventoryResponseFrame

TCP_IP = '192.168.1.250'
TCP_PORT = 60000

def read_tags(reader_addr, reader_port):
    # Установка соединения с считывателем через TCP
    transport = TcpTransport(reader_addr=reader_addr, reader_port=reader_port)
    runner = CommandRunner(transport)
    
    try:
        # Отправка команды на инвентаризацию меток
        get_inventory_cmd = ReaderCommand(G2_TAG_INVENTORY)
        transport.write(get_inventory_cmd.serialize())

        # Чтение и обработка ответа от считывателя
        inventory_status = None
        while inventory_status is None or inventory_status == G2_TAG_INVENTORY_STATUS_MORE_FRAMES:
            resp = G2InventoryResponseFrame(transport.read_frame())
            inventory_status = resp.result_status
            
            # Вывод информации о каждой найденной метке
            for tag in resp.get_tag():
                tag_id = tag.epc.hex()
                print(f"Tag ID: {tag_id}")
                
    finally:
        # Закрытие соединения
        transport.close()

if __name__ == "__main__":
    read_tags(TCP_IP, TCP_PORT)

# pip install chafon-rfid

