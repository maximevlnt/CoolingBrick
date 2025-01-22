import sys
import csv
import time
import random
import json

import zipfile
import statistics


import paho.mqtt.client as mqtt  # Bibliothèque MQTT
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QLineEdit, QFormLayout, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
                             QScrollArea, QSplitter, QSlider)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis
from PyQt5.QtGui import QPainter, QPen, QColor, QPixmap

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus.tables import TableStyle
from datetime import datetime





class DataCollector(QThread):
    data_collected = pyqtSignal(dict)

    def __init__(self, broker_address="172.20.10.2", topic="ESP1/data", port=1234):
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
        self.acquisition_window = ParametreAcquisitionWindow()
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

class ParametreAcquisitionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Paramètres d'acquisition")
        self.setGeometry(100, 100, 1000, 800)
        self.setStyleSheet(HomeWindow.get_stylesheet(self))

        # Liste de toutes les métriques disponibles
        self.available_metrics = ["temperature", "pressure", "humidity"]
        self.current_metrics = self.available_metrics

        # Widgets principaux
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        #Ajout d'un titre
        self.add_title()

        # Ajout du texte des protocoles
        self.create_protocole_text()

        # Ajout des sliders pour les paramètres
        self.create_parameter_sliders()

        # Boutons de navigation
        self.create_navigation_buttons()

    def add_title(self):
        title = QLabel("<h1>Paramètres d'Acquisition</h1>")
        title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title)

    def create_protocole_text(self):
        protocol_text = QLabel(
            "<b>Protocoles de lancement et de vérification :</b><br>" 
            "1. Assurez-vous que les valeurs des sliders sont bonnes.<br>" 
            "2. Vérifiez que les cartes ESP8266 d'acquisition et de commande sont alimentées.<br>" 
            "3. Lancez l'interface d'acquisition une fois prêt.<br>"
        )
        protocol_text.setStyleSheet("font-size: 14px; margin: 10px;")
        protocol_text.setWordWrap(True)
        self.layout.addWidget(protocol_text)

    

    def create_parameter_sliders(self):
        # Conteneur pour les sliders
        slider_layout = QVBoxLayout()

        SLIDER = """
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: #ddd;
                height: 6px;
                border-radius: 3px;
            }

            QSlider::handle:horizontal {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ff7f50, stop: 1 #ff4500
                );
                border: 1px solid #555;
                width: 14px;
                height: 14px;
                border-radius: 7px;
                margin: -5px 0; /* Déplace légèrement le handle pour qu'il soit centré */
            }

            QSlider::groove:horizontal:hover {
                background: #ccc;
            }

            QSlider::handle:horizontal:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ff6347, stop: 1 #ff0000
                );
                border: 1px solid #444;
            }
            """


        # Température
        self.temp_label = QLabel("Température (°C) : 25")
        self.temp_label.setAlignment(Qt.AlignCenter)
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setMinimum(20)
        self.temp_slider.setMaximum(50)
        self.temp_slider.setValue(25)
        self.temp_slider.setSingleStep(10)
        self.temp_slider.setTickPosition(QSlider.TicksBelow)
        self.temp_slider.setTickInterval(5)

        self.temp_slider.setStyleSheet(SLIDER)
        
        self.temp_slider.valueChanged.connect(lambda: self.update_slider_label(self.temp_slider, self.temp_label, "Température (°C)"))
        self.temp_slider.setFixedWidth(600)

        temp_layout = QVBoxLayout()
        temp_layout.addWidget(self.temp_label)
        temp_layout.addWidget(self.temp_slider)
        temp_layout.setAlignment(Qt.AlignCenter)

        slider_layout.addLayout(temp_layout)

        # Vitesse du vent
        self.wind_label = QLabel("Vitesse du vent (km/h) : 10")
        self.wind_label.setAlignment(Qt.AlignCenter)
        self.wind_slider = QSlider(Qt.Horizontal)
        self.wind_slider.setMinimum(0)
        self.wind_slider.setMaximum(60)
        self.wind_slider.setValue(10)
        self.wind_slider.setTickPosition(QSlider.TicksBelow)
        self.wind_slider.setTickInterval(10)
        self.wind_slider.setSingleStep(10) 
        self.wind_slider.valueChanged.connect(lambda: self.update_slider_label(self.wind_slider, self.wind_label, "Vitesse du vent (km/h)"))
        self.wind_slider.setFixedWidth(600)

        self.wind_slider.setStyleSheet(SLIDER)

        wind_layout = QVBoxLayout()
        wind_layout.addWidget(self.wind_label)
        wind_layout.addWidget(self.wind_slider)
        wind_layout.setAlignment(Qt.AlignCenter)

        slider_layout.addLayout(wind_layout)

        # Humidité
        self.humidity_label = QLabel("Humidité (%) : 50")
        self.humidity_label.setAlignment(Qt.AlignCenter)
        self.humidity_slider = QSlider(Qt.Horizontal)
        self.humidity_slider.setMinimum(0)
        self.humidity_slider.setMaximum(100)
        self.humidity_slider.setValue(50)
        self.humidity_slider.setTickPosition(QSlider.TicksBelow)
        self.humidity_slider.setTickInterval(10)
        self.humidity_slider.setSingleStep(10) 
        self.humidity_slider.valueChanged.connect(lambda: self.update_slider_label(self.humidity_slider, self.humidity_label, "Humidité (%)"))
        self.humidity_slider.setFixedWidth(600)

        self.humidity_slider.setStyleSheet(SLIDER)

        humidity_layout = QVBoxLayout()
        humidity_layout.addWidget(self.humidity_label)
        humidity_layout.addWidget(self.humidity_slider)
        humidity_layout.setAlignment(Qt.AlignCenter)

        slider_layout.addLayout(humidity_layout)

        # Ajouter au layout principal
        self.layout.addLayout(slider_layout)


        

    def update_slider_label(self, slider, label, text):
        label.setText(f"{text} : {slider.value()}")

    def create_navigation_buttons(self):
        # Boutons de navigation
        button_layout = QHBoxLayout()
        self.layout.addSpacing(50)

        back_button = QPushButton("Retour au Menu")
        back_button.setFixedSize(200, 50)
        back_button.clicked.connect(self.open_home_window)
        button_layout.addWidget(back_button)

        start_button = QPushButton("Lancer l'Acquisition")
        start_button.setFixedSize(200, 50)
        start_button.clicked.connect(self.open_acquisition_window)
        button_layout.addWidget(start_button)

        # Ajouter un espacement entre les boutons
        button_layout.setSpacing(50)

        # Ajouter les boutons au layout principal
        self.layout.addLayout(button_layout)


    def open_home_window(self):
        self.home_window = HomeWindow()
        self.home_window.show()
        self.close()

    def open_acquisition_window(self):
        self.acquisition_window = AcquisitionWindow()
        self.acquisition_window.show()
        self.close()

    

class AcquisitionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Banc de Test - Brique en Terre Cuite")
        self.resize(1000, 1000)

          # Liste de toutes les métriques disponibles
        self.available_metrics = ["temperature", "pressure", "humidity"]
        self.current_metrics = self.available_metrics


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
            QPushButton:pressed {
                background-color: #a27f6e; 
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

        # Formulaire pour les paramètres (identique à votre code précédent)
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
        self.splitter.addWidget(self.chart_scroll_area)  # Graphiques (conteneur défilable)

        # Ajuster les proportions initiales entre les widgets
        self.splitter.setStretchFactor(0, 1)  # Le tableau (index 0) obtient moins d'espace
        self.splitter.setStretchFactor(1, 3)  # Les graphiques (index 1) obtiennent plus d'espace

        # Ajouter le splitter à la mise en page principale
        self.layout.addWidget(self.splitter)


        # Connecter les boutons
        self.start_button.clicked.connect(self.start_collecting)
        self.stop_button.clicked.connect(self.stop_collecting)
        self.export_button.clicked.connect(self.export_data)
        self.clear_button.clicked.connect(self.open_acquisition_window)
        self.back_button.clicked.connect(self.open_home_window)

        # Backend
        self.collector = DataCollector()
        self.collector.data_collected.connect(self.update_data)

        # Stocker les données
        self.data = []
        self.time_counter = 0


    def start_collecting(self):
        self.collector.start_collecting()
        self.export_button.setEnabled(False)
        self.export_button.setStyleSheet("background-color: gray; color: white;")


    def stop_collecting(self):
        self.collector.stop_collecting()
        self.export_button.setEnabled(True)
        self.export_button.setStyleSheet("background-color: #c2988f; color: white;")

      
    def clear_data(self):
        # Vider le tableau
        self.data_table.setRowCount(0)
        
        # Réinitialiser tous les graphiques
        for chart_metrics in list(self.series_dict.keys()):
            # Supprimer tous les graphiques existants
            for series in self.series_dict[chart_metrics].values():
                series.clear()
        
        # Réinitialiser le compteur de temps
        self.time_counter = 0
        self.data.clear()

    def initialize_charts(self):
        # Créer une série pour chaque métrique dès le départ
        self.series_dict = {}
        self.chart_views = {}
        
        self.chart_layout.setSpacing(0)  # Espacement global entre tous les graphiques

        # Les 3 métriques et leurs configurations
        self.metrics = ["temperature", "pressure", "humidity"]
        self.metric_configs = {
            "temperature": {"color": QColor(255, 0, 0), "range": (15, 35), "title": "Température (°C)"},
            "pressure": {"color": QColor(0, 0, 255), "range": (900, 1100), "title": "Pression (hPa)"},
            "humidity": {"color": QColor(0, 255, 0), "range": (25, 80), "title": "Humidité (%)"}
        }

        # Créer les séries et les graphiques une seule fois
        for metric in self.metrics:
            # Créer la série pour cette métrique
            metric_series = QLineSeries()
            metric_series.setName(metric.capitalize())
            metric_series.setPen(QPen(self.metric_configs[metric]['color'], 2))
            
            # Créer le graphique pour cette métrique
            chart = QChart()
            chart.setTitle(self.metric_configs[metric]['title'])
            chart.addSeries(metric_series)
            
            # Créer les axes
            axis_x = QValueAxis()
            axis_x.setTitleText("Temps (s)")
            axis_x.setRange(0, 100)  # Plage du temps à ajuster au besoin
            chart.addAxis(axis_x, Qt.AlignBottom)

            axis_y = QValueAxis()
            axis_y.setTitleText(self.metric_configs[metric]['title'])
            axis_y.setRange(*self.metric_configs[metric]['range'])
            chart.addAxis(axis_y, Qt.AlignLeft)

            chart.setAxisX(axis_x, metric_series)
            chart.setAxisY(axis_y, metric_series)

            # Créer la vue du graphique
            chart_view = QChartView(chart)
            chart_view.setRenderHint(QPainter.Antialiasing)
            chart_view.setMinimumHeight(300)

            # Ajouter la vue à la disposition et stocker
            self.chart_layout.addWidget(chart_view)
            self.chart_views[metric] = chart_view
            self.series_dict[metric] = metric_series

    def update_data(self, new_data):
        self.data.append(new_data)
        # Ajouter les nouvelles données au tableau
        row_position = self.data_table.rowCount()
        self.data_table.insertRow(row_position)
        self.data_table.setItem(row_position, 0, QTableWidgetItem(f"{new_data['temperature']:.2f}"))
        self.data_table.setItem(row_position, 1, QTableWidgetItem(f"{new_data['pressure']:.2f}"))
        self.data_table.setItem(row_position, 2, QTableWidgetItem(f"{new_data['humidity']:.2f}"))
        self.data_table.scrollToBottom()

        # Ajouter les nouvelles données à chaque série
        for metric in self.metrics:
            self.series_dict[metric].append(self.time_counter, new_data[metric])

        # Mettre à jour la plage des axes X pour tous les graphiques
        for chart_view in self.chart_views.values():
            chart = chart_view.chart()
            min_time = max(self.time_counter - 50000, 0)
            max_time = self.time_counter
            chart.axisX().setRange(min_time, max_time)

        # Incrémenter le compteur de temps
        self.time_counter += 1

    def export_data(self):
        # Ouvrir une boîte de dialogue pour choisir l'emplacement du fichier zip
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Exporter les Données et Graphique", "", "Zip Files (*.zip)", options=options)
        
        if file_path:
            # Vérifier si le chemin sélectionné a l'extension .zip
            if not file_path.endswith('.zip'):
                file_path += '.zip'

            # Créer un fichier zip
            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Exporter les données dans un fichier CSV
                csv_file_path = "temp_data.csv"
                with open(csv_file_path, mode='w', newline='') as file:
                    writer = csv.DictWriter(file, fieldnames=["temperature", "pressure", "humidity"])
                    writer.writeheader()
                    
                    # Vérifier si les données existent avant de les écrire
                    if self.data:
                        writer.writerows(self.data)
                    else:
                        print("Aucune donnée à exporter dans le fichier CSV.")

                # Ajouter le fichier CSV dans le zip
                zipf.write(csv_file_path, "data.csv")

                # Capturer et ajouter une image de chaque graphique
                captured_graph_paths = []
                for metric, chart_view in self.chart_views.items():
                    # Sauvegarder la taille d'origine du graphique
                    original_size = chart_view.size()

                    # Définir la taille souhaitée pour l'image du graphique
                    export_width = 1920  # Largeur en pixels
                    export_height = 1080  # Hauteur en pixels

                    # Créer un QPixmap avec la taille spécifiée
                    chart_pixmap = QPixmap(export_width, export_height)
                    chart_pixmap.fill(Qt.transparent)  # Remplir l'arrière-plan avec la transparence

                    # Redimensionner le graphique dans QChartView pour occuper l'espace complet
                    chart_view.setRenderHint(QPainter.Antialiasing)
                    chart_view.setRenderHint(QPainter.SmoothPixmapTransform)

                    # Ajuster la taille temporairement pour l'exportation
                    chart_view.setFixedSize(export_width, export_height)

                    # Rendre le graphique dans le QPixmap
                    chart_painter = QPainter(chart_pixmap)
                    chart_view.render(chart_painter)
                    chart_painter.end()

                    # Sauvegarder le graphique redimensionné dans une image PNG
                    image_path = f"{metric}_graph.png"
                    chart_pixmap.save(image_path, 'PNG')
                    captured_graph_paths.append(image_path)

                    # Ajouter l'image du graphique dans le zip
                    zipf.write(image_path, f"{metric}_graph.png")

                    # Rétablir la taille d'origine du graphique après l'exportation
                    chart_view.setFixedSize(original_size)


                # Générer un rapport PDF détaillé
                pdf_report_path = "rapport_mesures.pdf"
                self.generate_pdf_report(pdf_report_path)
                
                # Ajouter le PDF au zip
                zipf.write(pdf_report_path, "rapport_mesures.pdf")

                print(f"Les données et les graphiques ont été exportés dans le fichier zip: {file_path}")

    def generate_pdf_report(self, pdf_path):
        # Créer un PDF avec des statistiques détaillées
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Éléments du rapport
        elements = []
        
        # Titre du rapport
        title = Paragraph("Rapport de Mesures du Banc de Test", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))

        # Date et heure de la mesure
        from datetime import datetime
        now = datetime.now()
        date_time = Paragraph(f"Date et heure de la mesure : {now.strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal'])
        elements.append(date_time)
        elements.append(Spacer(1, 12))

        # Informations supplémentaires
        info_text = Paragraph(f"Durée de la mesure : {len(self.data)} secondes", styles['Normal'])
        elements.append(info_text)
        elements.append(Spacer(1, 12))

        # Informations générales
        if self.data:
            # Calculs statistiques (comme précédemment)
            temps_mesure = len(self.data)
            stats = {
                "temperature": {
                    "moyenne": statistics.mean([d['temperature'] for d in self.data]),
                    "min": min([d['temperature'] for d in self.data]),
                    "max": max([d['temperature'] for d in self.data])
                },
                "pressure": {
                    "moyenne": statistics.mean([d['pressure'] for d in self.data]),
                    "min": min([d['pressure'] for d in self.data]),
                    "max": max([d['pressure'] for d in self.data])
                },
                "humidity": {
                    "moyenne": statistics.mean([d['humidity'] for d in self.data]),
                    "min": min([d['humidity'] for d in self.data]),
                    "max": max([d['humidity'] for d in self.data])
                }
            }

            # Tableau des statistiques résumées
            stats_data = [
                ['Métrique', 'Moyenne', 'Minimum', 'Maximum'],
                ['Température (°C)', 
                f"{stats['temperature']['moyenne']:.2f}", 
                f"{stats['temperature']['min']:.2f}", 
                f"{stats['temperature']['max']:.2f}"],
                ['Pression (hPa)', 
                f"{stats['pressure']['moyenne']:.2f}", 
                f"{stats['pressure']['min']:.2f}", 
                f"{stats['pressure']['max']:.2f}"],
                ['Humidité (%)', 
                f"{stats['humidity']['moyenne']:.2f}", 
                f"{stats['humidity']['min']:.2f}", 
                f"{stats['humidity']['max']:.2f}"]
            ]

            stats_table = Table(stats_data)
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c2988f')),  # Fond gris clair pour la première ligne (titre)
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Texte en blanc pour les en-têtes
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Alignement du texte centré
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Police en gras pour les en-têtes
                ('FONTSIZE', (0, 0), (-1, 0), 12),  # Taille de police des en-têtes
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),  # Espacement en bas des en-têtes
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5e3d2')),  # Fond beige pour le reste du tableau
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#b99188')),  # Bordure noire et épaisse
                ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#a27f6e')),  # Ligne au-dessus des en-têtes pour le séparateur
                ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#a27f6e')),  # Ligne sous les données pour le séparateur
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#5a4e41')),  # Texte gris pour les autres lignes
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),  # Police Helvetica pour le reste des lignes
                ('FONTSIZE', (0, 1), (-1, -1), 10),  # Taille de la police pour le reste des lignes
                ('PADDING', (0, 0), (-1, -1), 8),  # Padding uniforme pour le tableau
            ]))

            
            elements.append(Paragraph("Résumé des Statistiques", styles['Heading2']))
            elements.append(stats_table)
            elements.append(Spacer(1, 12))

            # Nouveau tableau avec TOUTES les mesures
            full_data = [
                ['N°', 'Température (°C)', 'Pression (hPa)', 'Humidité (%)']
            ]
            for index, entry in enumerate(self.data, 1):
                full_data.append([
                    str(index),
                    f"{entry['temperature']:.2f}", 
                    f"{entry['pressure']:.2f}", 
                    f"{entry['humidity']:.2f}"
                ])

            full_table = Table(full_data, repeatRows=1)
            full_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c2988f')),  # Fond gris clair pour la première ligne (titre)
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Texte en blanc pour les en-têtes
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Alignement du texte centré
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Police en gras pour les en-têtes
                ('FONTSIZE', (0, 0), (-1, 0), 12),  # Taille de police des en-têtes
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),  # Espacement en bas des en-têtes
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5e3d2')),  # Fond beige pour le reste du tableau
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#b99188')),  # Bordure noire et épaisse
                ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#a27f6e')),  # Ligne au-dessus des en-têtes pour le séparateur
                ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#a27f6e')),  # Ligne sous les données pour le séparateur
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#5a4e41')),  # Texte gris pour les autres lignes
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),  # Police Helvetica pour le reste des lignes
                ('FONTSIZE', (0, 1), (-1, -1), 10),  # Taille de la police pour le reste des lignes
                ('PADDING', (0, 0), (-1, -1), 8),  # Padding uniforme pour le tableau
            ]))
            
            elements.append(Paragraph("Tableau Détaillé des Mesures", styles['Heading2']))
            elements.append(full_table)
            elements.append(Spacer(1, 12))

            # Le reste du code reste identique (graphiques, etc.)
            # Ajouter les graphiques au rapport
            elements.append(Spacer(1, 12))
            graphs_title = Paragraph("Graphiques des Mesures", styles['Heading2'])
            elements.append(graphs_title)

            # Ajouter chaque graphique
            for metric in ['temperature', 'pressure', 'humidity']:
                graph_path = f"{metric}_graph.png"
                try:
                    img = Image(graph_path, width=400, height=250)
                    img.hAlign = 'CENTER'
                    graph_label = Paragraph(f"Graphique de {metric.capitalize()}", styles['Heading3'])
                    graph_label.hAlign = 'CENTER'
                    elements.append(graph_label)
                    elements.append(img)
                    elements.append(Spacer(1, 12))
                except Exception as e:
                    print(f"Erreur lors de l'ajout du graphique {metric}: {e}")

        else:
            # Pas de données
            no_data = Paragraph("Aucune donnée n'a été collectée.", styles['Normal'])
            elements.append(no_data)

        # Construire le PDF
        doc.build(elements)






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
        self.control_layout2 = QHBoxLayout()
        self.start_button = QPushButton("Démarrer")
        self.stop_button = QPushButton("Arrêter")
        self.clear_button = QPushButton("Nettoyer")
        self.export_button = QPushButton("Exporter les données")
        self.back_button = QPushButton("Retour au menu")

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
    
    def create_chart(self):
        # Configurer le graphique avec des séries de couleurs différentes
        self.chart = QChart()
        self.chart.setTitle("Données des Capteurs")
        self.chart.legend().setVisible(True)
        
        # Créer des séries pour chaque métrique
        self.series = {
            "temperature": QLineSeries(),
            "pressure": QLineSeries(),
            "humidity": QLineSeries(),
        }
        
        # Personnaliser les couleurs et les noms des séries
        colors = {
            "temperature": QColor(255, 0, 0),     # Rouge
            "pressure": QColor(0, 0, 255),        # Bleu
            "humidity": QColor(0, 255, 0),        # Vert
        }
        
        for metric, series in self.series.items():
            series.setName(metric.replace('_', ' ').capitalize())
            series.setPen(QPen(colors[metric], 2))
            self.chart.addSeries(series)
        
        # Configuration des axes
        self.axis_x = QValueAxis()
        self.axis_x.setTitleText("Temps (s)")
        self.axis_x.setRange(0, 50)
        
        self.axis_y = QValueAxis()
        self.axis_y.setTitleText("Valeurs")
        self.axis_y.setRange(0, 100)
        
        # Associer les axes à toutes les séries
        for series in self.series.values():
            self.chart.setAxisX(self.axis_x, series)
            self.chart.setAxisY(self.axis_y, series)
        
        # Vue du graphique
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.chart_view.setMinimumHeight(300)
        
        # Ajouter le graphique à la disposition
        self.layout.addWidget(self.chart_view)

    def open_home_window(self):
        self.home_window = HomeWindow()
        self.home_window.show()
        self.close()

    def open_acquisition_window(self):
        self.acquisition_window = AcquisitionWindow()
        self.acquisition_window.show()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    home_window = HomeWindow()
    home_window.show()
    sys.exit(app.exec_())