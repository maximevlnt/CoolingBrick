import sys
import csv
import zipfile
import statistics
import time
import random
import paho.mqtt.client as mqtt  # Bibliothèque MQTT

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QLineEdit, QFormLayout, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
                             QScrollArea, QSplitter)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis
from PyQt5.QtGui import QPainter, QPen, QColor, QPixmap

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

class DataCollector(QThread):
    data_collected = pyqtSignal(dict)

    def __init__(self, broker_address="localhost"):
        super().__init__()
        self.running = False
        self.broker_address = broker_address
        self.client = mqtt.Client()

    def on_message(self, client, userdata, message):
        # Traitement des messages reçus
        payload = message.payload.decode('utf-8')
        print(f"Données reçues : {payload}")
        if payload.startswith("temp:"):
            data = payload.split(',')
            temp = float(data[0].split(':')[1])
            hum = float(data[1].split(':')[1])
            pressure = random.uniform(950, 1050)

            self.data_collected.emit({
                'temperature': temp,
                'humidity': hum,
                'pressure': pressure
            })

    def run(self):
        self.client.on_message = self.on_message
        self.client.connect(self.broker_address, port=1234) ################################# à modifier de conf de mosquitto
        self.client.subscribe("sensor_data")  # Abonnez-vous au topic approprié
        self.client.loop_start()  # Démarre la boucle de traitement des messages
        self.running = True

        while self.running:
            time.sleep(1)  # Garder le thread actif

        self.client.loop_stop()  # Arrête la boucle de traitement des messages
        self.client.disconnect()  # Déconnexion du broker

    def start_collecting(self):
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
                background-color: #a0796f;
            }
            QPushButton:pressed {
                background-color: #8f6d63;
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

        # Initialisation des données
        self.data_history = []

        # Initialisation de la page principale
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # Initialiser le collecteur de données
        self.data_collector = DataCollector(broker_address="localhost")
        self.data_collector.data_collected.connect(self.update_data)

        self.setup_home_page()

    def export_data(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Exporter les données", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if file_name:
            with open(file_name, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Température (°C)", "Pression (hPa)", "Humidité (%)"])  # En-têtes
                for data in self.data_history:
                    writer.writerow([data['temperature'], data['pressure'], data['humidity']])
            print(f"Données exportées vers {file_name}")

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget() is not None:
                    item.widget().deleteLater()

    def setup_home_page(self):
        # Nettoyer l'interface actuelle
        self.clear_layout(self.main_layout)  # Appel sécuritaire
        self.central_widget.setLayout(self.main_layout)
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
        layout.addWidget(connect_text)
        layout.addWidget(connect_button)

        # Bouton retour au menu principal
        back_button = QPushButton("Retour au Menu")
        back_button.setFixedSize(200, 50)
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

        self.resize(1000, 1000)

        # Liste de toutes les métriques disponibles
        self.available_metrics = ["temperature", "pressure", "humidity"]
        self.current_metrics = self.available_metrics

        # Widgets principaux
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Formulaire pour les paramètres
        self.create_parameter_form()
        
        # Boutons de contrôle
        self.create_control_buttons()

        # Tableau pour afficher les données
        self.create_data_table()

        # Graphique
        self.create_chart_container()

        # --- Ajout d'un splitter vertical ---
        self.splitter = QSplitter(Qt.Vertical)

        # Ajouter le tableau de données et la zone des graphiques dans le splitter
        self.splitter.addWidget(self.data_table)       # Tableau des valeurs
        self.splitter.setStretchFactor(0, 1)  # Le tableau obtient moins d'espace
        self.splitter.setStretchFactor(1, 3)  # Les graphiques obtiennent plus d'espace

        # Ajouter le splitter à la mise en page principale
        self.layout.addWidget(self.splitter)

        # Connecter les boutons
        self.start_button.clicked.connect(self.start_collecting)
        self.stop_button.clicked.connect(self.stop_collecting)
        self.export_button.clicked.connect(self.export_data)
        self.clear_button.clicked.connect(self.clear_data)
        self.back_button.clicked.connect(self.setup_home_page)

    def start_collecting(self):
        self.data_collector.start_collecting()
        self.back_button.setEnabled(False)
        self.back_button.setStyleSheet("background-color: gray; color: white;")
        self.export_button.setEnabled(False)
        self.export_button.setStyleSheet("background-color: gray; color: white;")

    def stop_collecting(self):
        self.data_collector.stop_collecting()
        self.back_button.setEnabled(True)
        self.back_button.setStyleSheet("background-color: #c2988f; color: white;")
        self.export_button.setEnabled(True)
        self.export_button.setStyleSheet("background-color: #c2988f; color: white;")

    def clear_data(self):
        # Vider le tableau
        self.data_table.setRowCount(0)
        self.data_history.clear()

    def update_data(self, new_data):
        self.data_history.append(new_data)
        # Ajouter les nouvelles données au tableau
        row_position = self.data_table.rowCount()
        self.data_table.insertRow(row_position)
        self.data_table.setItem(row_position, 0, QTableWidgetItem(f"{new_data['temperature']:.2f}"))
        self.data_table.setItem(row_position, 1, QTableWidgetItem(f"{new_data['pressure']:.2f}"))
        self.data_table.setItem(row_position, 2, QTableWidgetItem(f"{new_data['humidity']:.2f}"))
        self.data_table.scrollToBottom()

    # Autres méthodes (export_data, create_parameter_form, etc.) restent inchangées...

    def create_parameter_form(self):
        # Formulaire pour les paramètres
        self.param_form = QFormLayout()
        self.param_form.setSpacing(15)

        h_layout = QHBoxLayout()

        self.input_temp = QLineEdit()
        self.input_pressure = QLineEdit()
        self.input_humidity = QLineEdit()

        label_temp = QLabel("Température (°C) :")
        label_pressure = QLabel("Pression (hPa) :")
        label_humidity = QLabel("Humidité (%) :")

        h_layout.addWidget(label_temp)
        h_layout.addWidget(self.input_temp)
        h_layout.addWidget(label_pressure)
        h_layout.addWidget(self.input_pressure)
        h_layout.addWidget(label_humidity)
        h_layout.addWidget(self.input_humidity)

        self.param_form.addRow(h_layout)

        param_widget = QWidget()
        param_layout = QVBoxLayout()
        param_layout.addLayout(self.param_form)
        param_widget.setLayout(param_layout)
        self.layout.addWidget(param_widget)

    def create_control_buttons(self):
        self.control_layout = QHBoxLayout()
        self.start_button = QPushButton("Démarrer")
        self.stop_button = QPushButton("Arrêter")
        self.clear_button = QPushButton("Nettoyer")
        self.export_button = QPushButton("Exporter les données")
        self.back_button = QPushButton("Retour au Menu")

        self.control_layout.addWidget(self.start_button)
        self.control_layout.addWidget(self.stop_button)
        self.control_layout.addWidget(self.clear_button)
        self.control_layout.addWidget(self.export_button)
        self.control_layout.addWidget(self.back_button)

        control_widget = QWidget()
        control_layout = QVBoxLayout()
        control_layout.addLayout(self.control_layout)
        control_widget.setLayout(control_layout)
        self.layout.addWidget(control_widget)

    def create_data_table(self):
        # Tableau pour afficher les données
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(3)
        self.data_table.setHorizontalHeaderLabels(["Température (°C)", "Pression (hPa)", "Humidité (%)"])
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.layout.addWidget(self.data_table)

    def create_chart_container(self):
        # Créer un conteneur de défilement pour les graphiques
        self.chart_scroll_area = QScrollArea()
        self.chart_container = QWidget()
        self.chart_layout = QVBoxLayout()
        self.chart_container.setLayout(self.chart_layout)
        
        self.chart_scroll_area.setWidgetResizable(True)
        self.chart_scroll_area.setWidget(self.chart_container)
        
        self.layout.addWidget(self.chart_scroll_area)

        # Initialiser les dictionnaires pour les graphiques
        self.chart_views = {}
        self.series_dict = {}
        
        # Créer le premier graphique initial
        self.initialize_charts()

    def initialize_charts(self):
        # Créer une série pour chaque métrique dès le départ
        self.series_dict = {}
        
        # Les 3 métriques et leurs configurations
        self.metrics = ["temperature", "pressure", "humidity"]
        self.metric_configs = {
            "temperature": {"color": QColor(255, 0, 0), "range": (15, 35), "title": "Température (°C)"},
            "pressure": {"color": QColor(0, 0, 255), "range": (900, 1100), "title": "Pression (hPa)"},
            "humidity": {"color": QColor(0, 255, 0), "range": (25, 80), "title": "Humidité (%)"}
        }

        # Créer les séries et les graphiques une seule fois
        for metric in self.metrics:
            metric_series = QLineSeries()
            metric_series.setName(metric.capitalize())
            metric_series.setPen(QPen(self.metric_configs[metric]['color'], 2))

            chart = QChart()
            chart.setTitle(self.metric_configs[metric]['title'])
            chart.addSeries(metric_series)

            axis_x = QValueAxis()
            axis_x.setTitleText("Temps (s)")
            axis_x.setRange(0, 100)
            chart.addAxis(axis_x, Qt.AlignBottom)

            axis_y = QValueAxis()
            axis_y.setTitleText(self.metric_configs[metric]['title'])
            axis_y.setRange(*self.metric_configs[metric]['range'])
            chart.addAxis(axis_y, Qt.AlignLeft)

            chart.setAxisX(axis_x, metric_series)
            chart.setAxisY(axis_y, metric_series)

            chart_view = QChartView(chart)
            chart_view.setRenderHint(QPainter.Antialiasing)
            chart_view.setMinimumHeight(300)

            self.chart_layout.addWidget(chart_view)
            self.chart_views[metric] = chart_view
            self.series_dict[metric] = metric_series
    
    
    def clear_layout(self, layout):
        # Supprimer les widgets du layout en toute sécurité
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()  # Supprimer correctement le widget, mais pas le layout
            elif child.layout():
                self.clear_layout(child.layout())  # Effacer récursivement les layouts imbriqués

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())