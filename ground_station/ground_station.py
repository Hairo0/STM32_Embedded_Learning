import serial
import struct
import time

port_name = 'COM4'
baud_rate = 115200

ser = serial.Serial(port_name, baud_rate, timeout=0.1)

print(f"Connected to {port_name} at {baud_rate} baud.")

def calculate_crc16(data_bytes: bytes) -> int:
    crc = 0x0000
    for byte in data_bytes:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc

while True:
    single_byte_1 = ser.read(1)

    if single_byte_1 == b'\xAA':
        single_byte_2 = ser.read(1)

        if single_byte_2 == b'\x55':

            print(f"Packet Header Captured! Received data: {single_byte_1.hex()} {single_byte_2.hex()}")

            remaining_bytes = ser.read(38)

            full_packet = single_byte_1 + single_byte_2 + remaining_bytes

            if len(full_packet) == 40:

                packet_format = '<BBHBB8fH'
                unpacked_data = struct.unpack(packet_format, full_packet)
                h1, h2, seq, length, ptype, ax, ay, az, gx, gy, gz, temp, press, crc = (unpacked_data)

                data_bytes = full_packet[:38]
                calculated_crc = calculate_crc16(data_bytes)

                if calculated_crc == crc:
                    print("CRC check passed.")
                    print(f"Sequence: {seq: .2f}, Accel: {az: .2f}, Gyro: {gz: .2f}, Temp: {temp: .2f}, Pressure: {press: .2f}")
                    
                else:
                    print(f"CRC check failed! Calculated: {calculated_crc:04X}, Received: {crc:04X}")
