import serial
from collections import Counter
import statistics


class ArduinoSerial:
    def __init__(self, port, baud_rate=9600, timeout = 1, window = 50):
        self.adc_arr = []
        self.calib_arr = []
        self.window = window
        self.calib_window = 50
        self.SCALE = 1
        self.OFFSET = 0
        self.timeout = timeout
        self.NOIZE = 0
        self.port = port
        self.baud_rate = baud_rate
        self.arduino = None 


    def connect(self): 
        self.arduino = serial.Serial(self.port, self.baud_rate, bytesize=serial.EIGHTBITS, timeout = self.timeout)


    def disconnect(self):  
        self.arduino.close()


    def set_arr(self, arr): 
        self.adc_arr = arr


    def clean_arr(self):
        self.adc_arr = []


    def get_arr(self):  
        return self.adc_arr


    def read_data(self): 
        if not self.arduino:
            raise ValueError(f'Arduino is not connected\n')
        try:
            self.arduino.write(b'\x02') 
            response = self.arduino.read(4) 
            return int.from_bytes(response, byteorder='big', signed=False) 
        except serial.SerialTimeoutException as e:
            print(f'Timeout error: {e}')


    def set_scale(self, scale):
        self.SCALE = scale


    def set_offset(self, offset): 
        self.OFFSET = offset


    def get_offset(self): 
        return self.OFFSET
    
    
    def get_scale(self): 
        return self.SCALE


    def get_measure(self):  
        adc_val = self.read_data()      
        adc_val = (adc_val-self.OFFSET)
        return round(adc_val/self.SCALE, 2)
    
    def get_measure_2(self, samples: int = 10) -> float:
        """Возвращает финальный вес с учётом offset и scale."""
        raw = self.read_average(samples)
        return (raw - self.OFFSET) / self.SCALE


    def check_weight(self): 
        adc_val = self.get_measure()
        if adc_val < 20:
            return False
        return True
    

    def calc_mean(self):  
        adc_val = self.get_measure()

        if len(self.adc_arr) == self.window:
            self.adc_arr.pop(0)

        self.adc_arr.append(adc_val)

        return statistics.median(self.adc_arr)  # Убираем влияние выбросов


    def common_filter(self): 
        return Counter(self.get_arr()).most_common(1)[0][0]
    

    def tare(self, times=16):   
        sum = self.read_average(times)
        self.set_offset(sum)
        return sum/self.OFFSET


    def read_average(self, times=16):

        sum = 0
        for i in range(times):
            sum += self.read_data()
        return sum / times


    def calib_read(self, times = 20): 
        """Use only in calibration"""
        self.calib_arr = []
        for i in range(5):
            self.read_data()
            self.set_arr([])
        for i in range(times):
            self.calib_arr.append(self.read_data())
        counter = Counter(self.calib_arr)
        most_common = counter.most_common(1)[0][0]
        return most_common
    

    def calib_read_mediana(self): 
        """Use only in calibration"""
        self.calib_arr = []
        for i in range(53):
            row_number = self.read_data()
            if len(self.calib_arr)==self.calib_window:
                self.calib_arr.pop(0)
            print(self.calib_arr)
            self.calib_arr.append(row_number)
        print('Finish')
        return round(statistics.median(self.calib_arr), 2)
    

    def calib_read_average(self): 
        """Use only in calibration"""
        self.calib_arr = []
        for i in range(100):
            row_number = self.read_data()
            if len(self.calib_arr)==self.calib_window:
                self.calib_arr.pop(0)
            self.calib_arr.append(row_number)
        print('Finish')
        return round(sum(self.calib_arr) / len(self.calib_arr),2)


    def get_weight(self, times=16):   
        value = (self.read_average(times) - self.OFFSET)
        weight = (value / self.SCALE)
        return weight
    
    def read_raw(self) -> int:
        """Читает одно значение из Arduino (4 байта, big-endian)."""
        assert self.arduino, "Arduino не подключена"
        self.arduino.write(b'\x02')
        data = self.arduino.read(4)
        return int.from_bytes(data, byteorder='big', signed=False)