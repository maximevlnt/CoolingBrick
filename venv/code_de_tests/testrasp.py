import sys
import random  # Simuler des données si nécessaire
import paho.mqtt.client as mqtt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QSplitter
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis
from PyQt5.QtGui import QPainter, QPen, QColor


class MQTTClient(QThread):
    data_received = pyqtSignal(dict)

    def __init__(self, broker_address="localhost", port=1883, topic="testbench/sensors"):
        super().__init__()
        self.broker_address = broker_address
        self.port = port
        self.topic = topic
        self.client = mqtt.Client()
        self.running = False

    def run(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.broker_address, self.port, 60)
        self.client.loop_forever()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker.")
            self.client.subscribe(self.topic)
        else:
            print(f"Failed to connect, return code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            # Décoder le message reçu
            payload = msg.payload.decode("utf-8")
            print(f"Message reçu : {payload}")

            # Exemple de format : "temp:25.5,hum:60,press:1013"
            data_parts = payload.split(",")
            data = {part.split(":")[0]: float(part.split(":")[1]) for part in data_parts}
            self.data_received.emit(data)
        except Exception as e:
            print(f"Erreur lors du traitement des données MQTT : {e}")

    def start_collecting(self):
        self.running = True
        self.start()

    def stop_collecting(self):
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cooling Characterization Test Bench - Brick")
        self.setGeometry(100, 100, 1000, 800)

        # Initialisation des composants
        self.mqtt_client = MQTTClient(broker_address="localhost", port=1234, topic="testbench/sensors")
        self.mqtt_client.data_received.connect(self.update_data)

        self.data = []
        self.time_counter = 0

        # Initialisation de l'interface graphique
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Création de l'interface
        self.create_main_interface()

    def create_main_interface(self):
        # Formulaire pour les paramètres
        self.create_parameter_form()

        # Boutons de contrôle
        self.create_control_buttons()

        # Tableau pour afficher les données
        self.create_data_table()

        # Graphiques
        self.create_chart_container()

        # Ajout d'un splitter vertical
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(self.data_table)
        self.splitter.addWidget(self.chart_scroll_area)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 3)

        self.layout.addWidget(self.splitter)

    def create_parameter_form(self):
        # Formulaire pour afficher les valeurs en temps réel
        self.param_layout = QHBoxLayout()
        self.input_temp = QLineEdit()
        self.input_temp.setReadOnly(True)
        self.input_pressure = QLineEdit()
        self.input_pressure.setReadOnly(True)
        self.input_humidity = QLineEdit()
        self.input_humidity.setReadOnly(True)

        self.param_layout.addWidget(QLabel("Temperature (°C):"))
        self.param_layout.addWidget(self.input_temp)
        self.param_layout.addWidget(QLabel("Pressure (hPa):"))
        self.param_layout.addWidget(self.input_pressure)
        self.param_layout.addWidget(QLabel("Humidity (%):"))
        self.param_layout.addWidget(self.input_humidity)

        self.layout.addLayout(self.param_layout)

    def create_control_buttons(self):
        # Boutons de contrôle
        self.control_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.clear_button = QPushButton("Clear")
        self.export_button = QPushButton("Export Data")

        self.control_layout.addWidget(self.start_button)
        self.control_layout.addWidget(self.stop_button)
        self.control_layout.addWidget(self.clear_button)
        self.control_layout.addWidget(self.export_button)

        self.layout.addLayout(self.control_layout)

        # Connexion des boutons aux fonctions
        self.start_button.clicked.connect(self.start_acquisition)
        self.stop_button.clicked.connect(self.stop_acquisition)
        self.clear_button.clicked.connect(self.clear_data)
        self.export_button.clicked.connect(self.export_data)

    def create_data_table(self):
        # Tableau des données
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(3)
        self.data_table.setHorizontalHeaderLabels(["Temperature (°C)", "Pressure (hPa)", "Humidity (%)"])
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.data_table)

    def create_chart_container(self):
        # Conteneur pour les graphiques
        self.chart_scroll_area = QScrollArea()
        self.chart_container = QWidget()
        self.chart_layout = QVBoxLayout()
        self.chart_container.setLayout(self.chart_layout)

        self.chart_scroll_area.setWidgetResizable(True)
        self.chart_scroll_area.setWidget(self.chart_container)
        self.layout.addWidget(self.chart_scroll_area)

        # Initialisation des graphiques
        self.charts = {}
        self.series = {}
        self.metrics = ["temperature", "pressure", "humidity"]
        for metric in self.metrics:
            self.create_chart(metric)

    def create_chart(self, metric):
        # Création d'un graphique pour une métrique donnée
        chart = QChart()
        chart.setTitle(metric.capitalize())
        chart.legend().setVisible(False)

        series = QLineSeries()
        chart.addSeries(series)

        axis_x = QValueAxis()
        axis_x.setTitleText("Time (s)")
        axis_x.setRange(0, 100)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setTitleText(metric.capitalize())
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(300)

        self.chart_layout.addWidget(chart_view)
        self.charts[metric] = chart
        self.series[metric] = series

    def start_acquisition(self):
        self.mqtt_client.start_collecting()

    def stop_acquisition(self):
        self.mqtt_client.stop_collecting()

    def clear_data(self):
        self.data_table.setRowCount(0)
        for metric in self.metrics:
            self.series[metric].clear()
        self.time_counter = 0

    def update_data(self, new_data):
        # Mise à jour des données dans l'interface
        self.data.append(new_data)
        self.time_counter += 1

        # Mise à jour des champs de texte
        self.input_temp.setText(f"{new_data['temp']:.2f}")
        self.input_pressure.setText(f"{new_data['press']:.2f}")
        self.input_humidity.setText(f"{new_data['hum']:.2f}")

        # Ajout des données au tableau
        row_position = self.data_table.rowCount()
        self.data_table.insertRow(row_position)
        self.data_table.setItem(row_position, 0, QTableWidgetItem(f"{new_data['temp']:.2f}"))
        self.data_table.setItem(row_position, 1, QTableWidgetItem(f"{new_data['press']:.2f}"))
        self.data_table.setItem(row_position, 2, QTableWidgetItem(f"{new_data['hum']:.2f}"))

        # Mise à jour des graphiques
        for metric in self.metrics:
            self.series[metric].append(self.time_counter, new_data[metric])

    def export_data(self):
        # Exportation des données dans un fichier CSV (à implémenter)
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())