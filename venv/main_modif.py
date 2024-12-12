import sys
import random
import csv
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QWidget, QHeaderView, QFileDialog, QFormLayout
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis
from PyQt5.QtGui import QPainter

class DataCollector(QThread):
    data_collected = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.running = False

    def run(self):
        while self.running:
            data = {
                "temperature": random.uniform(20, 30),
                "pressure": random.uniform(950, 1050),
                "humidity": random.uniform(30, 70),
            }
            self.data_collected.emit(data)
            self.msleep(1000)

    def start_collecting(self):
        self.running = True
        self.start()

    def stop_collecting(self):
        self.running = False
        self.wait()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Banc de Test - Brique en Terre Cuite")
        self.setGeometry(100, 100, 1000, 800)

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
                background-color: #a0796f; /* Couleur plus sombre pour l'effet de survol */
            }
            QPushButton:pressed {
                background-color: #8f6d63; /* Couleur encore plus sombre lorsqu'on clique */
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 5px;
                max-width: 150px;
            }
            QTableWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                margin: 10px;
                background-color: #f9f9f9;
            }
            QHeaderView::section {
                background-color: #e0a96d;
                color: white;
                border: none;
                padding: 4px;
                font-size: 12px;
            }
        """)


        # Initialisation de la mémoire des données
        self.data_history = []

        # Initialisation de la page principale
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        self.data_collector = DataCollector()
        self.data_collector.data_collected.connect(self.update_data)

        self.setup_home_page()

    def setup_home_page(self):
        # Nettoyer l'interface actuelle
        self.clear_layout(self.main_layout)

        # Contenu du menu principal
        self.main_layout.setAlignment(Qt.AlignCenter)

        # Titre
        title_label = QLabel("Banc de Test - Brique en Terre Cuite")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; border: 2px solid #c2988f; border-radius: 10px; padding: 10px; margin: 20px;"
        )
        self.main_layout.addWidget(title_label)

        # Boutons de navigation
        button_layout = QVBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter)

        protocol_button = QPushButton("Protocoles et Connexion")
        acquisition_button = QPushButton("Acquisition")

        protocol_button.setFixedSize(200, 50)
        acquisition_button.setFixedSize(200, 50)

        #protocol_button.setStyleSheet("background-color: #E0A96D; border-radius: 10px; font-size: 14px;")
        #acquisition_button.setStyleSheet("background-color: #E0A96D; border-radius: 10px; font-size: 14px;")

        protocol_button.clicked.connect(self.setup_protocol_page)
        acquisition_button.clicked.connect(self.setup_acquisition_page)

        button_layout.addWidget(protocol_button)
        button_layout.addWidget(acquisition_button)

        self.main_layout.addLayout(button_layout)

    def setup_protocol_page(self):
        # Nettoyer l'interface actuelle
        self.clear_layout(self.main_layout)

        layout = QVBoxLayout()

        # Fonctionnement global
        protocol_text = QLabel(
            "<b>Protocoles de fonctionnement :</b><br>"
            "1. Assurez-vous que le banc de test est correctement installé et connecté à l'alimentation.<br>"
            "2. Connectez la carte Arduino via USB et vérifiez la communication série.<br>"
            "3. Lancez l'interface utilisateur pour commencer l'acquisition.<br>"
        )
        protocol_text.setStyleSheet("font-size: 14px; margin: 10px;")
        protocol_text.setWordWrap(True)
        layout.addWidget(protocol_text)

        # Connexion
        connect_text = QLabel(
            "<b>Connexion Arduino :</b><br>"
            "- Vérifiez que les drivers nécessaires sont installés.<br>"
            "- Configurez le port série à 9600 bauds.<br>"
        )
        connect_text.setStyleSheet("font-size: 14px; margin: 10px;")
        connect_text.setWordWrap(True)
        connect_button = QPushButton("Établir la connexion avec l'Arduino")
        #connect_button.setStyleSheet("background-color: #E0A96D; border-radius: 10px; padding: 10px; font-size: 14px;")
        layout.addWidget(connect_text)
        layout.addWidget(connect_button)

        # Bouton retour au menu principal
        back_button = QPushButton("Retour au Menu")
        back_button.setFixedSize(200, 50)
        #back_button.setStyleSheet("background-color: #E0A96D; border-radius: 10px; font-size: 14px;")
        back_button.clicked.connect(self.setup_home_page)

        layout.addWidget(back_button, alignment=Qt.AlignBottom | Qt.AlignHCenter)
        self.main_layout.addLayout(layout)

    def setup_acquisition_page(self):
        # Nettoyer l'interface actuelle
        self.clear_layout(self.main_layout)

        layout = QVBoxLayout()

        # Titre
        title_label = QLabel("Acquisition des Données")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)

        # Formulaire pour les paramètres
        param_form = QFormLayout()
        param_form.setSpacing(15)

        self.input_temp = QLineEdit()
        self.input_wind = QLineEdit()
        self.input_humidity = QLineEdit()
        param_form.addRow("Température (°C):", self.input_temp)
        param_form.addRow("Vitesse du Vent (m/s):", self.input_wind)
        param_form.addRow("Humidité (%):", self.input_humidity)

        param_widget = QWidget()
        param_layout = QVBoxLayout()
        param_layout.addLayout(param_form)
        param_widget.setLayout(param_layout)
        layout.addWidget(param_widget, alignment=Qt.AlignHCenter)

        # Boutons de contrôle
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Démarrer")
        self.stop_button = QPushButton("Arrêter")
        self.export_button = QPushButton("Exporter les données")

        for button in [self.start_button, self.stop_button, self.export_button]:
            #button.setStyleSheet("background-color: #E0A96D; border-radius: 10px; padding: 10px;")
            button_layout.addWidget(button)

        layout.addLayout(button_layout)

        # Tableau des données
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(["Température (°C)", "Pression (hPa)", "Humidité (%)"])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.setStyleSheet("margin-top: 10px;")
        self.table_widget.setFixedHeight(200)
        layout.addWidget(self.table_widget)

        # Graphiques
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
        layout.addWidget(self.chart_view)

        # Bouton retour au menu principal
        back_button = QPushButton("Retour au Menu")
        back_button.setFixedSize(200, 50)
        #back_button.setStyleSheet("background-color: #E0A96D; border-radius: 10px; font-size: 14px;")
        back_button.clicked.connect(self.setup_home_page)

        layout.addWidget(back_button, alignment=Qt.AlignCenter)
        self.main_layout.addLayout(layout)

        # Connecter les boutons
        self.start_button.clicked.connect(self.start_data_collection)
        self.stop_button.clicked.connect(self.stop_data_collection)
        self.export_button.clicked.connect(self.export_data)

        # Restaurer l'historique des données si disponible
        self.restore_previous_data()

    def start_data_collection(self):
        self.data_collector.start_collecting()

    def stop_data_collection(self):
        self.data_collector.stop_collecting()

    def update_data(self, data):
        # Ajouter à l'historique des données
        self.data_history.append(data)

        row_position = self.table_widget.rowCount()
        self.table_widget.insertRow(row_position)
        self.table_widget.setItem(row_position, 0, QTableWidgetItem(f"{data['temperature']:.2f}"))
        self.table_widget.setItem(row_position, 1, QTableWidgetItem(f"{data['pressure']:.2f}"))
        self.table_widget.setItem(row_position, 2, QTableWidgetItem(f"{data['humidity']:.2f}"))

        # Mise à jour des graphiques
        self.series_temp.append(row_position, data['temperature'])
        self.series_pressure.append(row_position, data['pressure'])
        self.series_humidity.append(row_position, data['humidity'])

    def restore_previous_data(self):
        # Restaurer l'historique des données dans le tableau et les graphiques
        for i, data in enumerate(self.data_history):
            self.table_widget.insertRow(i)
            self.table_widget.setItem(i, 0, QTableWidgetItem(f"{data['temperature']:.2f}"))
            self.table_widget.setItem(i, 1, QTableWidgetItem(f"{data['pressure']:.2f}"))
            self.table_widget.setItem(i, 2, QTableWidgetItem(f"{data['humidity']:.2f}"))

            self.series_temp.append(i, data['temperature'])
            self.series_pressure.append(i, data['pressure'])
            self.series_humidity.append(i, data['humidity'])

    def export_data(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exporter les Données", "", "CSV Files (*.csv)")
        if path:
            with open(path, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Température (°C)", "Pression (hPa)", "Humidité (%)"])
                for row in range(self.table_widget.rowCount()):
                    writer.writerow([
                        self.table_widget.item(row, 0).text(),
                        self.table_widget.item(row, 1).text(),
                        self.table_widget.item(row, 2).text(),
                    ])

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
