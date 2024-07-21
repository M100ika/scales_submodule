from microbit import uart

from .transport import BaseTransport


class SerialTransport(BaseTransport):

    def __init__(self, baud_rate=57600):
        self.serial = uart.init(baudrate=baud_rate, tx=pin0, rx=pin1)

    def read_bytes(self, length):
        return self.serial.read(length)

    def write_bytes(self, byte_array):
        self.serial.write(byte_array)

    def close(self):
        self.serial.close()
