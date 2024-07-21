import statistics

def read_data():
    print(f'Enter: ')
    return int(input())

def calib_read_2(times=10):
    """Use only in calibration"""
    calib_arr = []
    
    # Collect data 'times' times
    for _ in range(times):
        calib_arr.append(read_data())
        
    # Calculate and return the average value
    average_value = sum(calib_arr) / len(calib_arr)
    return average_value

def calib_read(times=10):
    """Use only in calibration"""
    calib_arr = []
    calib_arr_2 = []
    
    # Collect data 'times' times
    for _ in range(times):
        number = read_data()
        calib_arr.append(number)
        calib_arr_2.append(number)

    median_value = statistics.median(calib_arr)
    average_value = sum(calib_arr_2) / len(calib_arr_2)
    from collections import Counter

    counter = Counter(calib_arr)
    most_common = counter.most_common(1)[0][0]
    return median_value, average_value, most_common

def main():
    median, average, most_common = calib_read()
    print(f'med: {median}')
    print(f'ave: {average}')
    print(f'mc: {most_common}')

main()