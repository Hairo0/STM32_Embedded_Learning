import math
import sys
import time
import csv
import serial
import struct
import trimesh
import numpy as np
from datetime import datetime

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QComboBox, QPushButton, QLabel, QGroupBox, QGridLayout

import pyqtgraph as pg
import pyqtgraph.opengl as gl

DARK_THEME_QSS = """
QMainWindow {
    background-color: #11111b;
}
QWidget {
    background-color: #11111b;
    color: #cdd6f4;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QGroupBox {
    font-weight: bold;
    border: 1px solid #313244;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 15px;
    background-color: #1e1e2e;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #89b4fa;
}
QLabel {
    color: #cdd6f4;
    background-color: transparent;
}
QComboBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 5px;
    min-width: 80px;
}
QComboBox::drop-down {
    border: none;
}
QPushButton {
    background-color: #89b4fa;
    color: #11111b;
    font-weight: bold;
    border-radius: 4px;
    padding: 6px 15px;
}
QPushButton:hover {
    background-color: #b4befe;
}
QPushButton:pressed {
    background-color: #74c7ec;
}
"""

class TelemetryWorker(QThread):
    telemetry_signal = pyqtSignal(dict)

    def __init__(self, port_name='COM4', baud_rate=115200):
        super().__init__()
        self.port_name = port_name
        self.baud_rate = baud_rate
        self.is_running = True
        self.ser = None 

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

            self.ser = serial.Serial(self.port_name, self.baud_rate, timeout=0.1)

            print(f"Connected to {self.port_name} at {self.baud_rate} baud.")

            while self.is_running:
                single_byte_1 = self.ser.read(1)

                if single_byte_1 == b'\xAA':
                    single_byte_2 = self.ser.read(1)

                    if single_byte_2 == b'\x55':

                        remaining_bytes = self.ser.read(38)

                        full_packet = single_byte_1 + single_byte_2 + remaining_bytes

                        if len(full_packet) == 40:

                            packet_format = '<BBHBB8fH'
                            unpacked_data = struct.unpack(packet_format, full_packet)
                            h1, h2, seq, length, ptype, ax, ay, az, gx, gy, gz, temp, press, crc = (unpacked_data)

                            data_bytes = full_packet[:38]
                            calculated_crc = calculate_crc16(data_bytes)

                            crc_valid = (calculated_crc == crc)

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
                                    'crc': hex(crc),
                                    'crc_valid': crc_valid
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
            if self.ser and self.ser.is_open:
                self.ser.close()

    def stop(self):
        self.is_running = False

        self.wait(1000)

        if self.ser and self.ser.is_open:
            self.ser.close()

        self.wait()
              

class GroundStationGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ground Station GUI - V1.0")
        self.resize(1200, 800)
        self.setStyleSheet(DARK_THEME_QSS)
        self.worker_thread = None

        self.base_pressure = None
        self.maxpoints = 100
        self.update_counter = 0
        self.last_seq = None
        self.lost_packets = 0
        self.crc_errors = 0

        self.packet_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0

        self.roll = 0.0
        self.pitch = 0.0
        self.last_filter_time = time.time()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()

        top_bar_layout = QHBoxLayout()

        self.port_label = QLabel("Select Serial Port:")
        top_bar_layout.addWidget(self.port_label)

        self.port_combobox = QComboBox()
        self.port_combobox.addItems(["COM1", "COM2", "COM3", "COM4", "COM5"])  # Example COM ports
        self.port_combobox.setCurrentText("COM4")  # Default selection
        top_bar_layout.addWidget(self.port_combobox)

        self.baud_label = QLabel("Select Baud Rate:")
        top_bar_layout.addWidget(self.baud_label)
        self.baud_combobox = QComboBox()
        self.baud_combobox.addItems(["9600", "19200", "38400", "57600", "115200"])  # Example baud rates
        self.baud_combobox.setCurrentText("115200")  # Default selection
        top_bar_layout.addWidget(self.baud_combobox)

        self.start_button = QPushButton("Start Telemetry")
        self.start_button.clicked.connect(self.start_telemetry)

        self.status_label = QLabel("Status: DISCONNECTED")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        top_bar_layout.addWidget(self.status_label)

        top_bar_layout.addWidget(self.start_button)

        main_layout.addLayout(top_bar_layout)

        system_status_groupbox = QGroupBox("System Status & Metrics")
        system_status_layout = QHBoxLayout()

        self.fps_label = QLabel("FPS: 0")
        self.lost_packets_label = QLabel("Lost Packets: 0")
        self.crc_errors_label = QLabel("CRC Errors: 0")
        self.orientation_label = QLabel("Roll: 0.0° | Pitch: 0.0°")

        system_status_layout.addWidget(self.fps_label)
        system_status_layout.addWidget(self.lost_packets_label)
        system_status_layout.addWidget(self.crc_errors_label)
        system_status_layout.addWidget(self.orientation_label)

        system_status_groupbox.setLayout(system_status_layout)
        main_layout.addWidget(system_status_groupbox)

        middle_layout = QHBoxLayout()

        left_panel_layout = QVBoxLayout()

        metrics_groupbox = QGroupBox("Live Telemetry Data")
        metrics_layout = QGridLayout()  # Set spacing between widgets

        self.metrics_labels = {}
        metrics = ["Temperature (°C)", "Pressure (hPa)", "Accel X (m/s²)", "Gyro X (°/s)", "Accel Y (m/s²)",
                    "Gyro Y (°/s)", "Accel Z (m/s²)", "Gyro Z (°/s)"]

        for i, metric in enumerate(metrics):
            label = QLabel(f"{metric}: N/A")
            self.metrics_labels[metric] = label
            metrics_layout.addWidget(label, i // 2, i % 2)  # Arrange in two columns

        metrics_groupbox.setLayout(metrics_layout)
        left_panel_layout.addWidget(metrics_groupbox)

        group3d = QGroupBox("3D Orientation Visualization")
        layout_3d = QVBoxLayout()
        self.view_3d = gl.GLViewWidget()
        self.view_3d.setCameraPosition(distance=15, elevation=20, azimuth=45)
        self.view_3d.setBackgroundColor('#121212')

        grid = gl.GLGridItem()
        grid.setSize(20, 20)
        grid.setSpacing(1, 1)
        self.view_3d.addItem(grid)

        self.mesh_item = self.load_3d_model("baykar_bayraktar_tb2.glb")
        if self.mesh_item:
            self.view_3d.addItem(self.mesh_item)

        layout_3d.addWidget(self.view_3d)
        group3d.setLayout(layout_3d)
        left_panel_layout.addWidget(group3d)

        middle_layout.addLayout(left_panel_layout, stretch=1)

        self.seq_data = []

        self.press_data = []

        self.ax_data = []
        self.ay_data = []
        self.az_data = []

        self.gx_data = []
        self.gy_data = []
        self.gz_data = []

        graph_groupbox = QGroupBox("Telemetry Graphs")
        graph_layout = QHBoxLayout()

        self.pressure_plot = pg.PlotWidget(title="Pressure (hPa)")
        self.pressure_plot.setBackground('#121212')
        self.pressure_plot.showGrid(x=True, y=True)
        self.pressure_curve = self.pressure_plot.plot(pen=pg.mkPen(color='#FF6B00', width=2))
        graph_layout.addWidget(self.pressure_plot)

        self.accel_plot = pg.PlotWidget(title="Acceleration (m/s²)")
        self.accel_plot.setBackground('#121212')
        self.accel_plot.showGrid(x=True, y=True)
        self.accel_plot.addLegend()
        self.ax_curve = self.accel_plot.plot(pen=pg.mkPen(color='#00FF00', width=2), name='Accel X')
        self.ay_curve = self.accel_plot.plot(pen=pg.mkPen(color='#0000FF', width=2), name='Accel Y')
        self.az_curve = self.accel_plot.plot(pen=pg.mkPen(color='#FF0000', width=2), name='Accel Z')
        graph_layout.addWidget(self.accel_plot)

        self.gyro_plot = pg.PlotWidget(title="Gyroscope (°/s)")
        self.gyro_plot.setBackground('#121212')
        self.gyro_plot.showGrid(x=True, y=True)
        self.gyro_plot.addLegend()
        self.gx_curve = self.gyro_plot.plot(pen=pg.mkPen(color='#00FF00', width=2), name='Gyro X')
        self.gy_curve = self.gyro_plot.plot(pen=pg.mkPen(color='#0000FF', width=2), name='Gyro Y')
        self.gz_curve = self.gyro_plot.plot(pen=pg.mkPen(color='#FF0000', width=2), name='Gyro Z')
        graph_layout.addWidget(self.gyro_plot)

        graph_groupbox.setLayout(graph_layout)
        middle_layout.addWidget(graph_groupbox, stretch=1)
        main_layout.addLayout(middle_layout)

        central_widget.setLayout(main_layout)

    def load_3d_model(self, file_path: str):
        try:
            scene_or_mesh = trimesh.load(file_path,)
            if isinstance(scene_or_mesh, trimesh.Scene):
                mesh = scene_or_mesh.dump(concatenate=True)
            else:
                mesh = scene_or_mesh

            mesh.vertices -= mesh.center_mass
            mesh.vertices[:, 2] -= np.min(mesh.vertices[:, 2])
            max_dim = np.max(mesh.extents)

            if max_dim > 0:
                mesh.vertices /= (max_dim / 6.0)

            vertices = mesh.vertices
            faces = mesh.faces

            mesh_data = gl.MeshData(vertexes=vertices, faces=faces)
            mesh_item = gl.GLMeshItem(meshdata=mesh_data, smooth=True, color=(0.2, 0.6, 0.8, 1.0), shader='shaded', glOptions='translucent')
            print(f"Successfully loaded 3D model '{file_path}'")
            return mesh_item

        except Exception as e:
            print(f"Error loading 3D model '{file_path}': {e}")

            vertices = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
            faces = np.array([[0, 1, 2], [0, 2, 3]])
            mesh_data = gl.MeshData(vertexes=vertices, faces=faces)
            return gl.GLMeshItem(meshdata=mesh_data, color=(1, 0.5, 0, 1), shader='shaded')

    def update_3d_view(self, roll: float, pitch: float, altitude: float = 0.0):
        
        if self.mesh_item is not None:
            self.mesh_item.resetTransform()

            self.mesh_item.translate(0, 0, 1.5 + altitude)
            
            self.mesh_item.rotate(90, 1, 0, 0)
            self.mesh_item.rotate(roll, 1, 0, 0)
            self.mesh_item.rotate(pitch, 0, 1, 0)

    def closeEvent(self, event):
        if self.worker_thread is not None and self.worker_thread.isRunning():
            self.worker_thread.stop()
        event.accept()

    def start_telemetry(self):

        if self.worker_thread is None or not self.worker_thread.isRunning():

            port_name = self.port_combobox.currentText()
            baud_rate = int(self.baud_combobox.currentText())

            self.worker_thread = TelemetryWorker(port_name=port_name, baud_rate=baud_rate)
            self.worker_thread.telemetry_signal.connect(self.update_metrics)
            self.worker_thread.start()

            self.status_label.setText("Status: CONNECTED")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            
            self.start_button.setText("Stop Telemetry")

        else:
            self.worker_thread.stop()
            self.worker_thread = None

            self.status_label.setText("Status: DISCONNECTED")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")

            self.start_button.setText("Start Telemetry")

    def update_metrics(self, data: dict):

        if not data.get("crc_valid", True):
                    self.crc_errors += 1
                    self.crc_errors_label.setText(f"CRC Errors: {self.crc_errors}")
                    return

        if self.base_pressure is None and data["press"] > 0:
            self.base_pressure = data["press"]

        rel_altitude = 0

        if self.base_pressure is not None:
            rel_altitude = (self.base_pressure - data["press"]) * 8.43

        seq = data['seq']
        if self.last_seq is not None and seq != (self.last_seq + 1):
            expected_seq = (self.last_seq + 1) % 65536
            if seq != expected_seq:
                diff = (seq - expected_seq) % 65536
                self.lost_packets += diff
                self.lost_packets_label.setText(f"Lost Packets: {self.lost_packets}")
        self.last_seq = seq

        self.packet_count += 1
        now = time.time()
        dt_fps = now - self.last_fps_time
        if dt_fps >= 1.0:
            self.current_fps = round(self.packet_count / dt_fps, 1)
            self.fps_label.setText(f"FPS: {self.current_fps}")
            self.packet_count = 0
            self.last_fps_time = now

        dt_filter = now - self.last_filter_time
        self.last_filter_time = now

        accel_roll = math.atan2(data['ay'], data['az']) * (180.0 / math.pi) if data['az'] != 0 else 0.0
        accel_pitch = math.atan2(-data['ax'], math.sqrt(data['ay']**2 + data['az']**2)) * (180.0 / math.pi)

        alpha = 0.98
        self.roll = alpha * (self.roll + data['gx'] * dt_filter) + (1 - alpha) * accel_roll
        self.pitch = alpha * (self.pitch + data['gy'] * dt_filter) + (1 - alpha) * accel_pitch

        self.orientation_label.setText(f"Roll: {self.roll:.1f}° | Pitch: {self.pitch:.1f}°")

        self.update_3d_view(self.roll, self.pitch, rel_altitude)

        self.metrics_labels["Temperature (°C)"].setText(f"Temperature (°C): {data['temp']:.2f}")
        self.metrics_labels["Pressure (hPa)"].setText(f"Pressure (hPa): {data['press']:.2f}")
        self.metrics_labels["Accel X (m/s²)"].setText(f"Accel X (m/s²): {data['ax']:.2f}")
        self.metrics_labels["Gyro X (°/s)"].setText(f"Gyro X (°/s): {data['gx']:.2f}")
        self.metrics_labels["Accel Y (m/s²)"].setText(f"Accel Y (m/s²): {data['ay']:.2f}")
        self.metrics_labels["Gyro Y (°/s)"].setText(f"Gyro Y (°/s): {data['gy']:.2f}")
        self.metrics_labels["Accel Z (m/s²)"].setText(f"Accel Z (m/s²): {data['az']:.2f}")
        self.metrics_labels["Gyro Z (°/s)"].setText(f"Gyro Z (°/s): {data['gz']:.2f}")

        self.seq_data.append(data['seq'])

        self.press_data.append(data['press'])

        self.ax_data.append(data['ax'])
        self.ay_data.append(data['ay'])
        self.az_data.append(data['az'])

        self.gx_data.append(data['gx'])
        self.gy_data.append(data['gy'])
        self.gz_data.append(data['gz'])

        if len(self.seq_data) > self.maxpoints:
            self.seq_data = self.seq_data[-self.maxpoints:]
            
            self.press_data = self.press_data[-self.maxpoints:]

            self.ax_data = self.ax_data[-self.maxpoints:]
            self.ay_data = self.ay_data[-self.maxpoints:]
            self.az_data = self.az_data[-self.maxpoints:]

            self.gx_data = self.gx_data[-self.maxpoints:]
            self.gy_data = self.gy_data[-self.maxpoints:]
            self.gz_data = self.gz_data[-self.maxpoints:]
            
        self.update_counter += 1

        if self.update_counter % 5 == 0:
            self.pressure_curve.setData(self.seq_data, self.press_data)

            self.ax_curve.setData(self.seq_data, self.ax_data)
            self.ay_curve.setData(self.seq_data, self.ay_data)
            self.az_curve.setData(self.seq_data, self.az_data)

            self.gx_curve.setData(self.seq_data, self.gx_data)
            self.gy_curve.setData(self.seq_data, self.gy_data)
            self.gz_curve.setData(self.seq_data, self.gz_data)
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GroundStationGUI()
    window.show()
    sys.exit(app.exec())