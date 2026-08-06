import serial
import struct
import time
import csv
import sys
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal, QCoreApplication

class TelemetryWorker(QThread):
    telemetry_signal = pyqtSignal(dict)

    def __init__(self, port_name='COM4', baud_rate=115200):
        super().__init__()
        self.port_name = port_name
        self.baud_rate = baud_rate
        self.is_running = True

    def run(self):

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        csv_filename = f"telemetry_data_log_{timestamp}.csv"

        csv_file = open(csv_filename, mode='w', newline='', encoding='utf-8')
        csv_writer = csv.writer(csv_file)

        csv_writer.writerow(['Timestamp', 'Sequence', 'Accel_X', 'Accel_Y', 'Accel_Z', 'Gyro_X', 'Gyro_Y',
                            'Gyro_Z', 'Temperature', 'Pressure', 'CRC'])

        print(f"Logging telemetry data to: '{csv_filename}'")

        csv_file.flush()

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

        try:

            ser = serial.Serial(self.port_name, self.baud_rate, timeout=0.1)

            print(f"Connected to {self.port_name} at {self.baud_rate} baud.")

            while self.is_running:
                single_byte_1 = ser.read(1)

                if single_byte_1 == b'\xAA':
                    single_byte_2 = ser.read(1)

                    if single_byte_2 == b'\x55':

                        remaining_bytes = ser.read(38)

                        full_packet = single_byte_1 + single_byte_2 + remaining_bytes

                        if len(full_packet) == 40:

                            packet_format = '<BBHBB8fH'
                            unpacked_data = struct.unpack(packet_format, full_packet)
                            h1, h2, seq, length, ptype, ax, ay, az, gx, gy, gz, temp, press, crc = (unpacked_data)

                            data_bytes = full_packet[:38]
                            calculated_crc = calculate_crc16(data_bytes)

                            if calculated_crc == crc:

                                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

                                csv_writer.writerow([timestamp, seq, ax, ay, az, gx, gy, gz, temp, press, crc])

                                csv_file.flush()

                                telemetry_payload = {
                                    'timestamp': timestamp,
                                    'seq': seq,
                                    'ax': round(ax, 2), 'ay': round(ay, 2), 'az': round(az, 2),
                                    'gx': round(gx, 2), 'gy': round(gy, 2), 'gz': round(gz, 2),
                                    'temp': round(temp, 2),
                                    'press': round(press, 2),
                                    'crc': hex(crc)
                                }

                                self.telemetry_signal.emit(telemetry_payload)

                            else:   
                                print(f"CRC mismatch: calculated {calculated_crc:04X}, received {crc:04X}")

        except serial.SerialException as e:
            print(f"Serial error: {e}")
        except KeyboardInterrupt:
            print("Keyboard interrupt received. Exiting...")
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            csv_file.close()
            print(f"Telemetry data logging stopped. Data saved to '{csv_filename}'")
            if "ser" in locals() and ser.is_open:
                ser.close()

    def stop(self):
        self.is_running = False
        self.wait()        

def handle_telemetry_data(data: dict):
    print(f"[GUI SLOT] Received Packet #{data['seq']} -> Temp: {data['temp']} C | Press: {data['press']} hPa")

if __name__ == '__main__':
    # 1. Initialize Qt Event Loop
    app = QCoreApplication(sys.argv)

    # 2. Instantiate Worker Thread
    worker = TelemetryWorker(port_name='COM4', baud_rate=115200)

    # 3. Connect Worker Signal to Slot Function (Interrupt Handler)
    worker.telemetry_signal.connect(handle_telemetry_data)

    # 4. Start Thread execution (Calls run() method in background)
    worker.start()

    print("[MAIN] Telemetry worker thread started. Press Ctrl+C to stop.")

    try:
        # Run Qt Event Loop
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n[MAIN] Stopping worker thread...")
        worker.stop()
        print("[MAIN] Program terminated safely.")
