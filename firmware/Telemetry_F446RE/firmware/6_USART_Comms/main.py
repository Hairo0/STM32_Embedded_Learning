import serial

port_name = 'COM4'  
baud_rate = 115200

ser = serial.Serial(port_name, baud_rate)

while True:
    if ser.in_waiting > 0:
        data = ser.readline().decode('utf-8').rstrip()
        print("Data from STM32:", data)