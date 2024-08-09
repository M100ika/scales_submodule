import binascii

def calculate_crc(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc

def verify_crc(tag):
    # Convert the tag hex string to bytes
    tag_bytes = binascii.unhexlify(tag)
    
    # Extract the data and the CRC value from the tag
    data = tag_bytes[:-2]
    received_crc = int.from_bytes(tag_bytes[-2:], byteorder='big')
    
    # Calculate the CRC from the data
    calculated_crc = calculate_crc(data)
    
    # Compare the calculated CRC with the received CRC
    return calculated_crc == received_crc

def tags_id_dict(tags):
    # Test the function with the given tags
    for tag in tags:
        is_valid = verify_crc(tag)
        print(f"Tag {tag} is {'valid' if is_valid else 'invalid'}")

def inventory_tag():
    import socket
    from chafon_rfid.command import G2_TAG_INVENTORY
    from chafon_rfid.response import G2InventoryResponseFrame
    from chafon_rfid.transport import TcpTransport

    # Параметры подключения к считывателю
    reader_ip = '192.168.1.250'  
    reader_port = 60000
       
    # Создаем транспорт
    transport = TcpTransport(reader_ip, reader_port)

    # Отправляем команду на инвентаризацию
    command = G2_TAG_INVENTORY()
    transport.write(command.serialize())

    # Читаем ответ
    response_frame = G2InventoryResponseFrame(transport.read_frame())

    # Проверяем, есть ли полученные теги
    if response_frame.tag_count > 0:
        for tag in response_frame.tags:
            # Печатаем EPC каждой прочитанной метки
            print(f'Read tag EPC: {tag.epc}')

    # Закрываем соединение
    transport.close()
    

def main():
    tags = [
        "4354001c004501c38d140a0c05d8010f0101e2806894000050103003cc70b0c1",
        "4354001c004501c38d13091e0102010f0101e2806894000040103003e195ba57",
        "4354001c004501c38d13091e0102010f0101e2806894000040103003ed88be54",
        "4354001c004501c38d140a0c05d8010f0101e2806894000050103003cc70b0c1"
    ]
    inventory_tag()

main()