import socket

# Параметры подключения
TCP_IP = '192.168.1.250'  # Замените на IP-адрес вашего считывателя
TCP_PORT = 60000          # Замените на порт вашего считывателя
BUFFER_SIZE = 1024        # Размер буфера для получения данных

# Команда для запроса информации о считывателе (пример)
GET_READER_INFO = bytes([0x53, 0x57, 0x00, 0x03, 0xFF, 0x21, 0xC3])

def get_reader_info():
    try:
        # Устанавливаем соединение
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((TCP_IP, TCP_PORT))
            print("Соединение установлено.")

            # Отправляем команду
            s.sendall(GET_READER_INFO)
            print("Команда отправлена.")

            # Получаем ответ
            data = s.recv(BUFFER_SIZE)
            print("Ответ получен:", data.hex())

    except Exception as e:
        print("Ошибка при общении с считывателем:", e)

if __name__ == "__main__":
    get_reader_info()
