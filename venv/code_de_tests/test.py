import sys
import csv
import time
import random
import json
import paho.mqtt.client as mqtt  # Bibliothèque MQTT
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QLineEdit, QFormLayout, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
                             QScrollArea, QSplitter)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis
from PyQt5.QtGui import QPainter, QPen, QColor

class DataCollector(QThread):
    data_collected = pyqtSignal(dict)

    def __init__(self, broker_address="172.20.10.2", topic="ESP8266/DHT11", port=1234):
        super().__init__()
        self.running = False
        self.broker_address = broker_address
        self.port = port
        self.topic = topic
        self.client = mqtt.Client()

    def on_message(self, client, userdata, message):
        payload = message.payload.decode('utf-8')
        try:
            data = json.loads(payload)
            temperature = data.get('temperature', None)
            humidity = data.get('humidity', None)

            if temperature is not None and humidity is not None:
                self.data_collected.emit({
                    'temperature': temperature,
                    'humidity': humidity,
                    'pressure': random.uniform(950, 1050)
                })
        except json.JSONDecodeError:
            print("Erreur : Impossible de décoder le message JSON")

    def run(self):
        self.client.on_message = self.on_message
        self.client.connect(self.broker_address, port=self.port)
        self.client.subscribe(self.topic)
        self.client.loop_start()
        self.running = True

        while self.running:
            time.sleep(1)

        self.client.loop_stop()
        self.client.disconnect()

    def start_collecting(self):
        self.start()

    def stop_collecting(self):
        self.running = False
        self.wait()

class HomeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Menu Principal")
        self.setGeometry(100, 100, 1000, 800)
        self.setStyleSheet(self.get_stylesheet())

        layout = QVBoxLayout()

        title_label = QLabel("Banc de Test - Brique en Terre Cuite")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 10px; padding: 10px; border: 2px solid #c2988f; border-radius: 10px;")
        layout.addWidget(title_label)

        protocol_button = QPushButton("Protocoles et Connexion")
        protocol_button.setFixedSize(200, 50)
        protocol_button.clicked.connect(self.open_protocol_window)
        layout.addWidget(protocol_button, alignment=Qt.AlignCenter)

        acquisition_button = QPushButton("Acquisition")
        acquisition_button.setFixedSize(200, 50)
        acquisition_button.clicked.connect(self.open_acquisition_window)
        layout.addWidget(acquisition_button, alignment=Qt.AlignCenter)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def open_protocol_window(self):
        self.protocol_window = ProtocolWindow()
        self.protocol_window.show()
        self.close()

    def open_acquisition_window(self):
        self.acquisition_window = AcquisitionWindow()
        self.acquisition_window.show()
        self.close()

    def get_stylesheet(self):
        return """
        QPushButton {
            background-color: #c2988f;
            color: white;
            border: none;
            padding: 10px 15px;
            text-align: center;
            font-size: 14px;
            border-radius: 10px;
        }
        QPushButton:hover {
            background-color: #a0796f;
        }
        QPushButton:pressed {
            background-color: #8f6d63;
        }
        QLabel {
            font-size: 14px;
            margin: 10px;
        }
        QTableWidget {
            border: 1px solid #ccc;
            border-radius: 5px;
            background-color: #f9f9f9;
        }
        QHeaderView::section {
            background-color: #e0a96d;
            color: white;
            padding: 4px;
            font-size: 12px;
        }
        """

class ProtocolWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Protocoles et Connexion")
        self.setGeometry(100, 100, 1000, 800)
        self.setStyleSheet(HomeWindow.get_stylesheet(self))

        layout = QVBoxLayout()

        protocol_text = QLabel(
            "<b>Protocoles de fonctionnement :</b><br>"
            "1. Assurez-vous que le banc de test est correctement installé et connecté à l'alimentation.<br>"
            "2. Connectez la carte Arduino via USB et vérifiez la communication série.<br>"
            "3. Lancez l'interface utilisateur pour commencer l'acquisition.<br>"
        )
        protocol_text.setStyleSheet("font-size: 14px; margin: 10px;")
        protocol_text.setWordWrap(True)
        layout.addWidget(protocol_text)

        back_button = QPushButton("Retour au Menu")
        back_button.setFixedSize(200, 50)
        back_button.clicked.connect(self.open_home_window)
        layout.addWidget(back_button, alignment=Qt.AlignCenter)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def open_home_window(self):
        self.home_window = HomeWindow()
        self.home_window.show()
        self.close()

class AcquisitionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Acquisition des Données")
        self.setGeometry(100, 100, 1000, 800)
        self.setStyleSheet(HomeWindow.get_stylesheet(self))

        self.data_collector = DataCollector(broker_address="172.20.10.2", topic="ESP8266/DHT11")
        self.data_collector.data_collected.connect(self.update_data)

        layout = QVBoxLayout()

        title_label = QLabel("Acquisition des Données")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)

        self.data_table = QTableWidget()
        self.data_table.setColumnCount(3)
        self.data_table.setHorizontalHeaderLabels(["Température (°C)", "Pression (hPa)", "Humidité (%)"])
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.data_table)

        # Graphiques
        self.chart_container = QVBoxLayout()
        self.series_dict = {
            "temperature": QLineSeries(),
            "pressure": QLineSeries(),
            "humidity": QLineSeries()
        }
        self.chart_views = {}

        for metric, series in self.series_dict.items():
            chart = QChart()
            chart.addSeries(series)
            chart.setTitle(f"Graphique de {metric.capitalize()}")
            chart.setAnimationOptions(QChart.SeriesAnimations)

            axis_x = QValueAxis()
            axis_x.setTitleText("Temps (s)")
            axis_x.setRange(0, 100)
            chart.addAxis(axis_x, Qt.AlignBottom)
            series.attachAxis(axis_x)

            axis_y = QValueAxis()
            axis_y.setTitleText(metric.capitalize())
            axis_y.setRange(0, 100 if metric == "humidity" else 40 if metric == "temperature" else 1100)
            chart.addAxis(axis_y, Qt.AlignLeft)
            series.attachAxis(axis_y)

            chart_view = QChartView(chart)
            chart_view.setRenderHint(QPainter.Antialiasing)
            self.chart_views[metric] = chart_view
            self.chart_container.addWidget(chart_view)

        layout.addLayout(self.chart_container)

        # Formulaire pour ajouter des valeurs manuellement
        form_layout = QFormLayout()
        self.input_temp = QLineEdit()
        self.input_pressure = QLineEdit()
        self.input_humidity = QLineEdit()

        form_layout.addRow("Température (°C) :", self.input_temp)
        form_layout.addRow("Pression (hPa) :", self.input_pressure)
        form_layout.addRow("Humidité (%) :", self.input_humidity)
        layout.addLayout(form_layout)

        # Boutons
        buttons_layout = QHBoxLayout()

        start_button = QPushButton("Démarrer")
        start_button.clicked.connect(self.start_collecting)
        buttons_layout.addWidget(start_button)

        stop_button = QPushButton("Arrêter")
        stop_button.clicked.connect(self.stop_collecting)
        buttons_layout.addWidget(stop_button)

        clear_button = QPushButton("Nettoyer")
        clear_button.clicked.connect(self.clear_data)
        buttons_layout.addWidget(clear_button)

        export_button = QPushButton("Exporter")
        export_button.clicked.connect(self.export_data)
        buttons_layout.addWidget(export_button)

        back_button = QPushButton("Retour au Menu")
        back_button.clicked.connect(self.open_home_window)
        buttons_layout.addWidget(back_button)

        layout.addLayout(buttons_layout)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def start_collecting(self):
        self.data_collector.start_collecting()

    def stop_collecting(self):
        self.data_collector.stop_collecting()

    def update_data(self, new_data):
        row_position = self.data_table.rowCount()
        self.data_table.insertRow(row_position)
        self.data_table.setItem(row_position, 0, QTableWidgetItem(f"{new_data['temperature']:.2f}"))
        self.data_table.setItem(row_position, 1, QTableWidgetItem(f"{new_data['pressure']:.2f}"))
        self.data_table.setItem(row_position, 2, QTableWidgetItem(f"{new_data['humidity']:.2f}"))
        self.data_table.scrollToBottom()

        for metric, series in self.series_dict.items():
            if metric in new_data:
                series.append(series.count(), new_data[metric])

    def clear_data(self):
        self.data_table.setRowCount(0)
        for series in self.series_dict.values():
            series.clear()

    def export_data(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Exporter les données", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if file_name:
            with open(file_name, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Température (°C)", "Pression (hPa)", "Humidité (%)"])
                for row in range(self.data_table.rowCount()):
                    writer.writerow([
                        self.data_table.item(row, 0).text(),
                        self.data_table.item(row, 1).text(),
                        self.data_table.item(row, 2).text()
                    ])

    def open_home_window(self):
        self.data_collector.stop_collecting()
        self.home_window = HomeWindow()
        self.home_window.show()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    home_window = HomeWindow()
    home_window.show()
    sys.exit(app.exec_())