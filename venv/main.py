import sys
import csv
import random  # Simuler des données (à remplacer par les vraies données des capteurs)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QLineEdit, QFormLayout, QFileDialog, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis
from PyQt5.QtGui import QPainter

# --- Partie Backend : Simuler des données de capteurs ---
class DataCollector(QThread):
    data_collected = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.running = False

    def run(self):
        while self.running:
            # Simuler des données pour température, pression, humidité
            data = {
                "temperature": random.uniform(20, 30),
                "pressure": random.uniform(950, 1050),
                "humidity": random.uniform(30, 70),
            }
            self.data_collected.emit(data)
            self.msleep(1000)  # Attendre 1 seconde entre les lectures

    def start_collecting(self):
        self.running = True
        self.start()

    def stop_collecting(self):
        self.running = False
        self.wait()

# --- Partie Interface graphique ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Banc de Test - Brique en Terre Cuite")
        self.resize(900, 700)

        

        # Appliquer des styles globaux
        self.setStyleSheet("""
            QPushButton {
                background-color: #c2988f;
                color: white;
                border: none;
                padding: 10px 15px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #b99188;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 5px;
                max-width: 150px;
            }
        """)

        # Widgets principaux
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Formulaire pour les paramètres
        self.param_form = QFormLayout()
        self.param_form.setSpacing(15)  # Espacement entre les lignes

        self.input_temp = QLineEdit()
        self.input_wind = QLineEdit()
        self.input_humidity = QLineEdit()
        self.param_form.addRow("Température (°C):", self.input_temp)
        self.param_form.addRow("Vitesse du Vent (m/s):", self.input_wind)
        self.param_form.addRow("Humidité (%):", self.input_humidity)

        param_widget = QWidget()
        param_layout = QVBoxLayout()
        param_layout.addLayout(self.param_form)
        param_widget.setLayout(param_layout)
        self.layout.addWidget(param_widget)

        # Boutons de contrôle
        self.control_layout = QHBoxLayout()
        self.start_button = QPushButton("Démarrer")
        self.stop_button = QPushButton("Arrêter")
        self.export_button = QPushButton("Exporter les données")

        self.control_layout.addWidget(self.start_button)
        self.control_layout.addWidget(self.stop_button)
        self.control_layout.addWidget(self.export_button)

        control_widget = QWidget()
        control_layout = QVBoxLayout()
        control_layout.addLayout(self.control_layout)
        control_widget.setLayout(control_layout)
        self.layout.addWidget(control_widget)

        # Tableau pour afficher les données
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(3)
        self.data_table.setHorizontalHeaderLabels(["Température (°C)", "Pression (hPa)", "Humidité (%)"])
        self.layout.addWidget(self.data_table)

        # Graphique
        self.chart = QChart()
        self.series_temp = QLineSeries()
        self.series_pressure = QLineSeries()
        self.series_humidity = QLineSeries()
        self.chart.addSeries(self.series_temp)
        self.chart.addSeries(self.series_pressure)
        self.chart.addSeries(self.series_humidity)

        self.axis_x = QValueAxis()
        self.axis_x.setTitleText("Temps (s)")
        self.axis_x.setRange(0, 10)
        self.axis_y = QValueAxis()
        self.axis_y.setTitleText("Valeurs")
        self.axis_y.setRange(0, 100)

        self.chart.setAxisX(self.axis_x, self.series_temp)
        self.chart.setAxisY(self.axis_y, self.series_temp)
        self.chart.setAxisX(self.axis_x, self.series_pressure)
        self.chart.setAxisY(self.axis_y, self.series_pressure)
        self.chart.setAxisX(self.axis_x, self.series_humidity)
        self.chart.setAxisY(self.axis_y, self.series_humidity)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.layout.addWidget(self.chart_view)

        # Redimensionner le graphique
        self.chart_view.setMinimumHeight(300)

        # Connecter les boutons
        self.start_button.clicked.connect(self.start_collecting)
        self.stop_button.clicked.connect(self.stop_collecting)
        self.export_button.clicked.connect(self.export_data)

        # Backend
        self.collector = DataCollector()
        self.collector.data_collected.connect(self.update_data)

        # Stocker les données
        self.data = []
        self.time_counter = 0

    def start_collecting(self):
        self.collector.start_collecting()

    def stop_collecting(self):
        self.collector.stop_collecting()

    def update_data(self, new_data):
        # Ajouter les nouvelles données
        self.data.append(new_data)

        # Mettre à jour le tableau
        row_position = self.data_table.rowCount()
        self.data_table.insertRow(row_position)
        self.data_table.setItem(row_position, 0, QTableWidgetItem(f"{new_data['temperature']:.2f}"))
        self.data_table.setItem(row_position, 1, QTableWidgetItem(f"{new_data['pressure']:.2f}"))
        self.data_table.setItem(row_position, 2, QTableWidgetItem(f"{new_data['humidity']:.2f}"))

        # Mettre à jour le graphique
        self.series_temp.append(self.time_counter, new_data['temperature'])
        self.series_pressure.append(self.time_counter, new_data['pressure'])
        self.series_humidity.append(self.time_counter, new_data['humidity'])
        self.time_counter += 1

    def export_data(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Exporter les Données", "", "CSV Files (*.csv)", options=options)
        if file_path:
            with open(file_path, mode='w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=["temperature", "pressure", "humidity"])
                writer.writeheader()
                writer.writerows(self.data)

# --- Lancer l'application ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
