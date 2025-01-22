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
                             QScrollArea, QSplitter, QSlider, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QObject
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis
from PyQt5.QtGui import QPainter, QPen, QColor, QPixmap

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus.tables import TableStyle

from datetime import datetime


# Configuration des topics MQTT
BROKER_ADDRESS = "172.20.10.2"  # Adresse du broker MQTT
ESP1_TOPIC_DATA = "ESP1/data"          # Topic pour l'ESP 1 (données uniquement)
ESP2_TOPIC_DATA = "ESP2/data"     # Topic pour les données de l'ESP 2
ESP2_TOPIC_DATATEMP = "ESP2/temp"
ESP2_TOPIC_COMMAND = "ESP2/command"  # Topic pour les commandes à l'ESP 2

ESP1_TOPIC_CONTROL = "ESP1/control"
ESP2_TOPIC_CONTROL = "ESP2/control"


class DataCollector(QObject):
    data_collected = pyqtSignal(dict)

    def __init__(self, broker_address, topic):
        super().__init__()
        self.broker_address = broker_address
        self.topic = topic
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.broker_address, 1234, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected to MQTT broker at {self.broker_address}")
        self.client.subscribe(self.topic)

    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            self.data_collected.emit(data)
        except json.JSONDecodeError:
            print("Error decoding JSON")




class HomeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Menu")
        self.setGeometry(100, 100, 1000, 800)
        self.setStyleSheet(self.get_stylesheet())

        # Main layout with margins for better spacing
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Header section
        header_widget = QWidget()
        header_layout = QHBoxLayout()
        
        # Logo/Icon (you can replace with your own)
        logo_label = QLabel("🧱")
        logo_label.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(logo_label)

        # Title section with subtitle
        title_widget = QWidget()
        title_layout = QVBoxLayout()
        
        title_label = QLabel("Test Bench")
        title_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #2D3748;")
        
        subtitle_label = QLabel("Earth Brick Characterisation.")
        subtitle_label.setStyleSheet("font-size: 16px; color: #718096;")
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        title_layout.setSpacing(5)
        
        title_widget.setLayout(title_layout)
        header_layout.addWidget(title_widget)
        header_layout.addStretch()
        
        header_widget.setLayout(header_layout)
        layout.addWidget(header_widget)

        # Cards container
        cards_widget = QWidget()
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        # Protocol Card
        protocol_card = QWidget()
        protocol_layout = QVBoxLayout()
        protocol_card.setProperty("class", "card")
        
        protocol_icon = QLabel("📋")
        protocol_icon.setAlignment(Qt.AlignCenter)
        protocol_icon.setStyleSheet("font-size: 48px; margin-bottom: 20px;")
        
        protocol_title = QLabel("Protocols")
        protocol_title.setAlignment(Qt.AlignCenter)
        protocol_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2D3748; margin-bottom: 10px;")
        
        protocol_desc = QLabel()
        protocol_desc.setAlignment(Qt.AlignCenter)
        protocol_desc.setWordWrap(True)
        protocol_desc.setText(
            "<p style='line-height: 1.6; margin: 0;'>See the steps required to perform the<br>experiment and characterization.</p>"
        )
        protocol_desc.setStyleSheet("font-size: 15px; color: #718096; margin-bottom: 20px;")
        
        protocol_button = QPushButton("See steps")
        protocol_button.setFixedSize(200, 50)
        protocol_button.clicked.connect(self.open_protocol_window)
        
        protocol_layout.addWidget(protocol_icon)
        protocol_layout.addWidget(protocol_title)
        protocol_layout.addWidget(protocol_desc)
        protocol_layout.addWidget(protocol_button, alignment=Qt.AlignCenter)
        protocol_card.setLayout(protocol_layout)

        # Acquisition Card
        acquisition_card = QWidget()
        acquisition_layout = QVBoxLayout()
        acquisition_card.setProperty("class", "card")
        
        acquisition_icon = QLabel("📊")
        acquisition_icon.setAlignment(Qt.AlignCenter)
        acquisition_icon.setStyleSheet("font-size: 48px; margin-bottom: 20px;")
        
        acquisition_title = QLabel("Acquisition")
        acquisition_title.setAlignment(Qt.AlignCenter)
        acquisition_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2D3748; margin-bottom: 10px;")
        
        acquisition_desc = QLabel("Start a new data acquisition.")
        acquisition_desc.setAlignment(Qt.AlignCenter)
        acquisition_desc.setWordWrap(True)
        acquisition_desc.setStyleSheet("font-size: 15px; color: #718096; margin-bottom: 20px;")
        
        acquisition_button = QPushButton("Start")
        acquisition_button.setFixedSize(200, 50)
        acquisition_button.clicked.connect(self.open_acquisition_window)
        
        acquisition_layout.addWidget(acquisition_icon)
        acquisition_layout.addWidget(acquisition_title)
        acquisition_layout.addWidget(acquisition_desc)
        acquisition_layout.addWidget(acquisition_button, alignment=Qt.AlignCenter)
        acquisition_card.setLayout(acquisition_layout)

        # Add cards to container
        cards_layout.addWidget(protocol_card)
        cards_layout.addWidget(acquisition_card)
        cards_widget.setLayout(cards_layout)
        
        layout.addWidget(cards_widget)
        layout.addStretch()

        # Footer
        footer_label = QLabel("© 2025 - INSA Toulouse")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("color: #A0AEC0; font-size: 12px;")
        layout.addWidget(footer_label)

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
        QWidget {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        
        QWidget[class="card"] {
            background-color: white;
            border-radius: 15px;
            min-width: 300px;
            max-width: 400px;
            min-height: 400px;
            padding: 30px;
        }
        
        QPushButton {
            background-color: #C17817;
            color: white;
            border: none;
            padding: 12px 20px;
            text-align: center;
            font-size: 16px;
            border-radius: 10px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #D7891B;
        }
        
        QPushButton:pressed {
            background-color: #9C5F13;
        }
        
        QMainWindow {
            background-color: #fcfaf7;
        }
        
        QLabel {
            font-size: 14px;
        }
        
        QTableWidget {
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            background-color: white;
            gridline-color: #EDF2F7;
        }
        
        QHeaderView::section {
            background-color: #4A5568;
            color: white;
            padding: 8px;
            font-size: 14px;
            border: none;
            font-weight: bold;
        }
        
        QTableWidget::item {
            padding: 8px;
        }
        """

class ProtocolWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Protocols")
        self.setGeometry(100, 100, 1000, 800)
        self.setStyleSheet(self.get_stylesheet())

        # Main layout with margins for better spacing
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Header section
        header_widget = QWidget()
        header_layout = QHBoxLayout()
        
        # Logo/Icon
        logo_label = QLabel("📋")
        logo_label.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(logo_label)

        # Title section with subtitle
        title_widget = QWidget()
        title_layout = QVBoxLayout()
        
        title_label = QLabel("Protocols")
        title_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #2D3748;")
        
        subtitle_label = QLabel("Installation and characterisation guide.")
        subtitle_label.setStyleSheet("font-size: 16px; color: #718096;")
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        title_layout.setSpacing(5)
        
        title_widget.setLayout(title_layout)
        header_layout.addWidget(title_widget)
        header_layout.addStretch()
        
        header_widget.setLayout(header_layout)
        layout.addWidget(header_widget)

        # Cards container
        cards_widget = QWidget()
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(30)

        # Installation Protocol Card
        install_card = QWidget()
        install_card.setProperty("class", "card")

        install_layout = QVBoxLayout()
        install_layout.setContentsMargins(10, 20, 10, 10)
        install_layout.setSpacing(20)

        # Title
        install_title = QLabel("Installation protocol")
        install_title.setStyleSheet("font-size: 20px; "
                                    "font-weight: bold; "
                                    "color: #2D3748; "
                                    "margin-left: 25px")
        install_layout.addWidget(install_title)

        # Steps for Installation Protocol
        steps = [
            "1. Make sure the test bench is properly installed.",
            "2. Make sure that the ESP acquisition cards are powered.",
            "3. Make sure that the sensors are properly connected to the ESP acquisition cards.",
            "4. Start the configuration of the data acquisition."
        ]

        for step in steps:
            step_label = QLabel(step)
            step_label.setWordWrap(True)
            step_label.setText(f"<p style='line-height: 1.6; margin: 0;'>{step}</p>")
            step_label.setStyleSheet("color: #718096; font-size: 14px; margin-bottom: 5px; margin-left: 10px; margin-right: 10px;")
            install_layout.addWidget(step_label)  # Correctly adding to install_layout

        install_card.setLayout(install_layout)

        # Characterisation Protocol Card
        charac_card = QWidget()
        charac_card.setProperty("class", "card")

        charac_layout = QVBoxLayout()
        charac_layout.setContentsMargins(10, 20, 10, 10)
        charac_layout.setSpacing(20)

        # Title for Characterisation Protocol
        charac_title = QLabel("Characterisation protocol")
        charac_title.setStyleSheet("font-size: 20px; "
                                    "font-weight: bold; "
                                    "color: #2D3748; "
                                    "margin-left: 25px")
        charac_layout.addWidget(charac_title)

        # Protocol Steps for Characterisation
        protocol = [
            "1. Set brick humidity level from 0% (completely dry) to 100% (fully water saturated) based on the characterisation requirements.",
            "2. Position the brick in the center of the test chamber.",
            "3. Ensure complete chamber sealing by firmly closing all latches.",
            "4. Configure acquisition parameters and initiate the data collection sequence"
        ]

        for step in protocol:
            protocol_label = QLabel(step)
            protocol_label.setWordWrap(True)
            protocol_label.setText(f"<p style='line-height: 1.6; margin: 0;'>{step}</p>")
            protocol_label.setStyleSheet("color: #718096; font-size: 14px; margin-bottom: 3px; margin-left: 10px; margin-right: 10px;")
            charac_layout.addWidget(protocol_label)  # Add to charac_layout instead of install_layout

        charac_card.setLayout(charac_layout)

        # Add cards to container
        cards_layout.addWidget(install_card)
        cards_layout.addWidget(charac_card)
        cards_widget.setLayout(cards_layout)

        layout.addWidget(cards_widget)
        layout.addStretch()


        # Back Button
        back_button = QPushButton("Back to Menu")
        back_button.setFixedSize(200, 50)
        back_button.clicked.connect(self.open_home_window)
        layout.addWidget(back_button, alignment=Qt.AlignCenter)

        # Footer
        footer_label = QLabel("© 2025 - INSA Toulouse")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("color: #A0AEC0; font-size: 12px;")
        layout.addWidget(footer_label)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def open_home_window(self):
        self.home_window = HomeWindow()
        self.home_window.show()
        self.close()

    def get_stylesheet(self):
        return """
        QWidget {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        
        QWidget[class="card"] {
            background-color: white;
            border-radius: 15px;
            min-width: 300px;
            max-width: 400px;
            min-height: 300px;
            padding: 30px;
        }
        
        QPushButton {
            background-color: #C17817;
            color: white;
            border: none;
            padding: 12px 20px;
            text-align: center;
            font-size: 16px;
            border-radius: 10px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #D7891B;
        }
        
        QPushButton:pressed {
            background-color: #9C5F13;
        }
        
        QMainWindow {
            background-color: #fcfaf7;
        }
        
        QLabel {
            font-size: 14px;
        }
        
        QTableWidget {
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            background-color: white;
            gridline-color: #EDF2F7;
        }
        
        QHeaderView::section {
            background-color: #4A5568;
            color: white;
            padding: 8px;
            font-size: 14px;
            border: none;
            font-weight: bold;
        }
        
        QTableWidget::item {
            padding: 8px;
        }
        """

class ParametreAcquisitionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Acquisition parameters")
        self.setGeometry(100, 100, 1000, 800)
        self.setStyleSheet(self.get_stylesheet())

        # Main layout with margins for better spacing
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(10)

        # Header section
        header_widget = QWidget()
        header_layout = QHBoxLayout()
        
        # Logo/Icon
        logo_label = QLabel("🎛️")
        logo_label.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(logo_label)

        # Title section with subtitle
        title_widget = QWidget()
        title_layout = QVBoxLayout()
        
        title_label = QLabel("Acquisition parameters")
        title_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #2D3748;")
        
        subtitle_label = QLabel("Configuration of settings for data acquisition.")
        subtitle_label.setStyleSheet("font-size: 16px; color: #718096;")
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        title_layout.setSpacing(5)
        
        title_widget.setLayout(title_layout)
        header_layout.addWidget(title_widget)
        header_layout.addStretch()
        
        header_widget.setLayout(header_layout)
        layout.addWidget(header_widget)

        # Protocol Card
        protocol_card = QWidget()
        protocol_card.setProperty("class", "card")
        protocol_layout = QVBoxLayout()
        protocol_layout.setSpacing(10)
        protocol_layout.setContentsMargins(10, 20, 10, 25)  # ltrb
        
        protocol_title = QLabel("Start and verification protocols")
        protocol_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2D3748; margin-bottom: 20px; margin-left: 25px;")
        protocol_layout.addWidget(protocol_title)

        steps = [
            "1. Make sure the slider values the one wanted for the characterisation.",
            "2. Check that the ESP acquisition cards are powered.",
            "3. Launch the acquisition interface when ready."
        ]

        
        for step in steps:
            step_label = QLabel(step)
            step_label.setWordWrap(True)
            step_label.setStyleSheet("color: #718096; font-size: 14px; margin-bottom: 10px; margin-left: 5px;")
            protocol_layout.addWidget(step_label)

        protocol_card.setLayout(protocol_layout)
        layout.addWidget(protocol_card)

        # Parameters Card
        params_card = QWidget()
        params_card.setProperty("class", "card")
        params_layout = QVBoxLayout()
        params_layout.setSpacing(10)
        params_layout.setContentsMargins(10, 20, 10, 25)  # ltrb
        
        params_title = QLabel("Parameters")
        params_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2D3748; margin-bottom: 20px; margin-left: 25px;")
        params_layout.addWidget(params_title)

        # Temperature Slider
        self.temp_label = QLabel("Temperature (°C): 25°C")
        self.temp_label.setStyleSheet("color: #718096; font-size: 14px; margin-bottom: 5px;")
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setMinimum(20)
        self.temp_slider.setMaximum(50)
        self.temp_slider.setValue(25)
        self.temp_slider.setTickPosition(QSlider.TicksBelow)
        self.temp_slider.setTickInterval(5)
        self.temp_slider.setSingleStep(5)
        self.temp_slider.setPageStep(5)
        self.temp_slider.valueChanged.connect(self.on_slider_value_changed_temp)
        params_layout.addWidget(self.temp_label)
        params_layout.addWidget(self.temp_slider)

        # Wind Speed Slider
        self.wind_label = QLabel("Wind speed (km/h): 10 km/h")
        self.wind_label.setStyleSheet("color: #718096; font-size: 14px; margin-bottom: 5px; margin-top: 20px;")
        self.wind_slider = QSlider(Qt.Horizontal)
        self.wind_slider.setMinimum(0)
        self.wind_slider.setMaximum(35)
        self.wind_slider.setValue(10)
        self.wind_slider.setTickPosition(QSlider.TicksBelow)
        self.wind_slider.setTickInterval(10)
        self.wind_slider.setSingleStep(5)
        self.wind_slider.setPageStep(5)
        self.wind_slider.valueChanged.connect(self.on_slider_value_changed_wind)
        params_layout.addWidget(self.wind_label)
        params_layout.addWidget(self.wind_slider)

        # Humidity Slider
        self.humidity_label = QLabel("Humidity (%): 50%")
        self.humidity_label.setStyleSheet("color: #718096; font-size: 14px; margin-bottom: 5px; margin-top: 20px;")
        self.humidity_slider = QSlider(Qt.Horizontal)
        self.humidity_slider.setMinimum(0)
        self.humidity_slider.setMaximum(100)
        self.humidity_slider.setValue(50)
        self.humidity_slider.setTickPosition(QSlider.TicksBelow)
        self.humidity_slider.setTickInterval(10)
        self.humidity_slider.setSingleStep(5)
        self.humidity_slider.setPageStep(5)
        self.humidity_slider.valueChanged.connect(self.on_slider_value_changed_humidity)
        params_layout.addWidget(self.humidity_label)
        params_layout.addWidget(self.humidity_slider)

        spacer_widget = QWidget()
        spacer_widget.setFixedHeight(10)
        params_layout.addWidget(spacer_widget)

        params_card.setLayout(params_layout)
        layout.addWidget(params_card)

        # Navigation Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        back_button = QPushButton("Back to Menu")
        back_button.setFixedSize(200, 50)
        back_button.clicked.connect(self.open_home_window)
        button_layout.addWidget(back_button)

        start_button = QPushButton("Start Acquisition")
        start_button.setFixedSize(200, 50)
        start_button.clicked.connect(self.initialize_acquisition)
        button_layout.addWidget(start_button)

        layout.addLayout(button_layout)

        layout.addStretch()

        # Footer
        footer_label = QLabel("© 2025 - INSA Toulouse")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("color: #A0AEC0; font-size: 12px;")
        layout.addWidget(footer_label)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def on_slider_value_changed_temp(self, value):
        rounded_value = round(value / 5) * 5
        self.temp_slider.setValue(rounded_value)
        self.temp_label.setText(f"Temperature (°C): {rounded_value}°C")

    def on_slider_value_changed_wind(self, value):
        rounded_value = round(value / 5) * 5
        self.wind_slider.setValue(rounded_value)
        self.wind_label.setText(f"Wind speed (km/h): {rounded_value} km/h")

    def on_slider_value_changed_humidity(self, value):
        rounded_value = round(value / 5) * 5
        self.humidity_slider.setValue(rounded_value)
        self.humidity_label.setText(f"Humidity (%): {rounded_value}%")
        
    def open_home_window(self):
        self.home_window = HomeWindow()
        self.home_window.show()
        self.close()

    def initialize_acquisition(self):
        self.send_command()
        self.open_acquisition_window()

    def send_command(self):
        # Get the slider values
        temperature = self.temp_slider.value()
        wind_speed = self.wind_slider.value()
        
        # Prepare the JSON payload
        command_payload = {
            "temperature": temperature,
            "wind_speed": wind_speed
        }
        
        # Convert the payload to a JSON string
        command_json = json.dumps(command_payload)
        
        # Publish the JSON to the MQTT topic
        client = mqtt.Client()
        client.connect(BROKER_ADDRESS,1234)
        client.publish(ESP2_TOPIC_COMMAND, command_json)
        client.disconnect()

        print(f"Sent command: {command_json}")

    def open_acquisition_window(self):
        temperature = self.get_temperature()
        self.acquisition_window = AcquisitionWindow(temperature)
        self.acquisition_window.show()
        self.close()

    def get_temperature(self):
        return self.temp_slider.value()
    

    def get_stylesheet(self):
        return """
        QWidget {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        
        QWidget[class="card"] {
            background-color: white;
            border-radius: 15px;
            min-width: 300px;
            padding: 30px;
            margin-bottom: 20px;
        }
        
        QPushButton {
            background-color: #C17817;
            color: white;
            border: none;
            padding: 12px 20px;
            text-align: center;
            font-size: 16px;
            border-radius: 10px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #D7891B;
        }
        
        QPushButton:pressed {
            background-color: #9C5F13;
        }
        
        QMainWindow {
            background-color: #fcfaf7;
        }
        
        QLabel {
            font-size: 14px;
        }
        
        QSlider::groove:horizontal {
            border: none;
            height: 6px;  /* Plus épais pour permettre plus d'arrondi */
            background: #E2E8F0;
            border-radius: 3px;  /* Arrondi plus prononcé */
        }

        QSlider::sub-page:horizontal {
            background: #C17817;
            border-radius: 3px;  /* Arrondi identique à la groove */
        }

        QSlider::add-page:horizontal {
            background: #E2E8F0;
            border-radius: 3px;  /* Arrondi identique à la groove */
        }

        QSlider::handle:horizontal {
            background: #C17817;
            width: 16px;
            height: 16px;
            margin: -5px 0;
            border-radius: 8px;  /* La moitié de width/height pour garantir un cercle parfait */
        }

        QSlider::handle:horizontal:hover {
            background: #D89234;
        }

        QSlider::handle:horizontal:pressed {
            background: #9C5F13;
            border-radius: 8px;  /* Maintient l'arrondi même en état pressé */
        }

        QSlider::sub-page:horizontal:disabled {
            background: #E2E8F0;
            border-radius: 3px;
        }

        QSlider::add-page:horizontal:disabled {
            background: #F7FAFC;
            border-radius: 3px;
        }

        QSlider::handle:horizontal:disabled {
            background: #CBD5E0;
            border-radius: 8px;
        }     
        """
    
class AcquisitionWindow(QMainWindow):
    def __init__(self, temperature):
        super().__init__()
        self.chosen_temperature = temperature
        self.init_ui(temperature)

    def init_ui(self, temperature):
        super().__init__()
        self.setWindowTitle("Data Acquisition")
        self.setGeometry(100, 100, 1000, 800)
        self.setStyleSheet(self.get_stylesheet())

        # Main layout with margins
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(10)
        
        # Title section with subtitle
        title_widget = QWidget()
        title_layout = QVBoxLayout()

        # Logo/Icon
        logo_label = QLabel("📊")
        logo_label.setStyleSheet("font-size: 32px;")
        title_layout.addWidget(logo_label)

        title_label = QLabel("Data Acquisition")
        title_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #2D3748;")

        subtitle_label = QLabel("Real-time data collection and visualization")
        subtitle_label.setStyleSheet("font-size: 16px; color: #718096;")

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        title_layout.setSpacing(5)

        title_widget.setLayout(title_layout)

        # Temperature display section
        temperature_widget = QWidget()
        temperature_layout = QHBoxLayout()

        temperature_label = QLabel("Temperature in the pipe:")
        temperature_label.setStyleSheet("font-size: 16px; color: #2D3748;")

        self.current_temperature_label = QLabel(f"{temperature}°C")
        self.current_temperature_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #E53E3E;")

        temperature_layout.addWidget(temperature_label)
        temperature_layout.addWidget(self.current_temperature_label)
        temperature_layout.addStretch()  # Pushes everything to the left
        temperature_widget.setLayout(temperature_layout)

        # Combine title and temperature sections in a single horizontal layout
        header_layout = QHBoxLayout()
        header_layout.addWidget(title_widget)
        header_layout.addStretch()  # Adds spacing between title and temperature
        header_layout.addWidget(temperature_widget)

        # Add the header layout to the main widget
        header_widget = QWidget()
        header_widget.setLayout(header_layout)

        layout.addWidget(header_widget)

        # Charts card
        charts_card = QWidget()
        charts_card.setProperty("class", "card")
        charts_layout = QVBoxLayout()
        charts_layout.setSpacing(10)
        charts_layout.setContentsMargins(10, 20, 10, 25)

        charts_title = QLabel("Real-time temperature graph")
        charts_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2D3748; margin-bottom: 20px; margin-left: 25px;")
        charts_layout.addWidget(charts_title)

        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.chart_view.setMinimumHeight(300)
        charts_layout.addWidget(self.chart_view)

        charts_card.setLayout(charts_layout)
        layout.addWidget(charts_card)

        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        self.back_button = QPushButton("Back to Menu")
        self.start_button = QPushButton("Start")

        for button in [self.back_button, self.start_button]:
            button.setFixedSize(200, 50)
            button_layout.addWidget(button)

        layout.addLayout(button_layout)

        # Footer
        footer_label = QLabel("© 2025 - INSA Toulouse")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("color: #A0AEC0; font-size: 12px;")
        layout.addWidget(footer_label)

        # Set up central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Initialize charts and connect buttons
        self.initialize_chart()
        self.connect_buttons()
        
        # Backend setup
        self.collector = DataCollector(BROKER_ADDRESS,ESP2_TOPIC_DATATEMP)
        self.collector.data_collected.connect(self.update_data)

        self.data = []
        self.time_counter = 0

    def get_stylesheet(self):
        return """
        QWidget {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        
        QWidget[class="card"] {
            background-color: white;
            border-radius: 15px;
            min-width: 300px;
            padding: 30px;
            margin-bottom: 20px;
        }
        
        QPushButton {
            background-color: #C17817;
            color: white;
            border: none;
            padding: 12px 20px;
            text-align: center;
            font-size: 16px;
            border-radius: 10px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #D7891B;
        }
        
        QPushButton:pressed {
            background-color: #9C5F13;
        }
        
        QMainWindow {
            background-color: #fcfaf7;
        }
        
        QLabel {
            font-size: 14px;
        }

        QLineEdit {
            padding: 8px;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            background-color: white;
            color: #2D3748;
            font-size: 14px;
        }

        QLineEdit:focus {
            border: 2px solid #C17817;
            outline: none;
        }

        QTableWidget {
            border: none;
            background-color: white;
            gridline-color: #E2E8F0;
        }

        QTableWidget::item {
            padding: 8px;
            border-bottom: 1px solid #E2E8F0;
        }

        QHeaderView::section {
            background-color: #F7FAFC;
            padding: 8px;
            border: none;
            border-bottom: 2px solid #E2E8F0;
            font-weight: bold;
            color: #2D3748;
        }

        QScrollArea {
            border: none;
            background-color: transparent;
        }

        QScrollBar:vertical {
            border: none;
            background: #E2E8F0;
            width: 10px;
            border-radius: 5px;
        }

        QScrollBar::handle:vertical {
            background: #CBD5E0;
            border-radius: 5px;
        }

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            border: none;
            background: none;
        }
        """

    def open_acquisition_after_brick_window(self):
        self.acquisition_after_brick_window = AcquisitionWindowAfterBrick()
        self.acquisition_after_brick_window.show()
        #self.close()
      
    def initialize_chart(self):
        # Créer la série pour la température
        self.temperature_series = QLineSeries()
        self.temperature_series.setName("Temperature in the pipe")
        self.temperature_series.setPen(QPen(QColor(255, 0, 0), 2))

        # Créer la ligne pour la température choisie
        self.chosen_temp_series = QLineSeries()
        self.temperature_series.setName("Wanted Temperature")
        self.chosen_temp_series.setPen(QPen(QColor(0, 0, 255), 2, Qt.DashLine))

        # Créer le graphique
        chart = QChart()
        chart.setTitle("Temperature (°C)")
        chart.addSeries(self.temperature_series)
        chart.addSeries(self.chosen_temp_series)

        # Créer les axes
        axis_x = QValueAxis()
        axis_x.setTitleText("Time (s)")
        axis_x.setRange(0, 100)  # Plage du temps à ajuster au besoin
        chart.addAxis(axis_x, Qt.AlignBottom)

        axis_y = QValueAxis()
        axis_y.setTitleText("Température (°C)")
        axis_y.setRange(15, 55)  # Ajustez cette plage selon vos besoins
        chart.addAxis(axis_y, Qt.AlignLeft)

        chart.setAxisX(axis_x, self.temperature_series)
        chart.setAxisY(axis_y, self.temperature_series)
        chart.setAxisX(axis_x, self.chosen_temp_series)
        chart.setAxisY(axis_y, self.chosen_temp_series)

        # Ajouter la ligne de température choisie
        self.chosen_temp_series.append(0, self.chosen_temperature)
        self.chosen_temp_series.append(100, self.chosen_temperature)

        # Définir le graphique pour la vue
        self.chart_view.setChart(chart)


    def update_data(self, new_data):
        print(f"Données reçues pour le graphe : {new_data}")
        if 'temperature' in new_data:
            temperature = new_data['temperature']
            self.temperature_series.append(self.time_counter, temperature)
            chart = self.chart_view.chart()
            chart.axisX().setRange(max(0, self.time_counter - 100), self.time_counter)
            self.time_counter += 1


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
    
    def connect_buttons(self):
        self.start_button.clicked.connect(self.open_acquisition_after_brick_window)
        self.back_button.clicked.connect(self.open_home_window)

    def open_home_window(self):
        self.home_window = HomeWindow()
        self.home_window.show()
        self.close()

    def open_acquisition_window(self):
        self.acquisition_window = AcquisitionWindow()
        self.acquisition_window.show()
        self.close()

class AcquisitionWindowAfterBrick(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Acquisition")
        self.setGeometry(100, 100, 1500, 1200)
        self.setStyleSheet(self.get_stylesheet())

        # Main layout with margins
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(10)

        # Header section
        header_widget = QWidget()
        header_layout = QHBoxLayout()
        
        # Logo/Icon
        logo_label = QLabel("📊")
        logo_label.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(logo_label)

        # Title section with subtitle
        title_widget = QWidget()
        title_layout = QVBoxLayout()
        
        title_label = QLabel("Data Acquisition")
        title_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #2D3748;")
        
        subtitle_label = QLabel("Real-time data collection and visualization")
        subtitle_label.setStyleSheet("font-size: 16px; color: #718096;")
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        title_layout.setSpacing(5)
        
        title_widget.setLayout(title_layout)
        header_layout.addWidget(title_widget)
        header_layout.addStretch()
        
        header_widget.setLayout(header_layout)
        layout.addWidget(header_widget)

        # Create a horizontal splitter for data tables and charts
        content_splitter = QSplitter(Qt.Horizontal)

        # Left side: Two data cards
        left_widget = QWidget()
        left_layout = QVBoxLayout()

        # Update the first table (index 0)
        # experiment_window.update_data(0, {'temperature': 26.0, 'pressure': 1014.0, 'humidity': 51.0})

        # Update the second table (index 1)
        # experiment_window.update_data(1, {'temperature': 27.0, 'pressure': 1015.0, 'humidity': 52.0})

        # First data card
        self.data_table_before_brick = self.create_data_card("Collected Data Before Brick")
        left_layout.addWidget(self.data_table_before_brick)

        # Second data card
        self.data_table_after_brick = self.create_data_card("Collected Data After Brick")
        left_layout.addWidget(self.data_table_after_brick)
        left_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        left_widget.setLayout(left_layout)
        content_splitter.addWidget(left_widget)

        # Right side: Charts card
        charts_card = QWidget()
        charts_card.setProperty("class", "card")
        charts_layout = QVBoxLayout()
        charts_layout.setSpacing(10)
        charts_layout.setContentsMargins(10, 20, 10, 25)

        charts_title = QLabel("Real-time Charts")
        charts_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2D3748; margin-bottom: 20px; margin-left: 25px;")
        charts_layout.addWidget(charts_title)

        self.chart_scroll_area = QScrollArea()
        self.chart_container = QWidget()
        self.chart_layout = QVBoxLayout()
        self.chart_container.setLayout(self.chart_layout)
        self.chart_scroll_area.setWidgetResizable(True)
        self.chart_scroll_area.setWidget(self.chart_container)
        charts_layout.addWidget(self.chart_scroll_area)

        charts_card.setLayout(charts_layout)
        charts_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        content_splitter.addWidget(charts_card)

        # Set initial sizes for the splitter
        content_splitter.setSizes([int(self.width() * 0.4), int(self.width() * 0.6)])
        content_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addWidget(content_splitter)

        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.clear_button = QPushButton("Clear")
        self.export_button = QPushButton("Export Data")
        self.back_button = QPushButton("Close")

        for button in [self.back_button, self.export_button, 
                        self.clear_button, self.stop_button, self.start_button]:
            button.setFixedSize(150, 40)
            button_layout.addWidget(button)

        layout.addLayout(button_layout)

        # Footer
        footer_label = QLabel("© 2025 - INSA Toulouse")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("color: #A0AEC0; font-size: 12px;")
        layout.addWidget(footer_label)

        # Set up central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Initialize charts and connect buttons
        self.initialize_charts()
        self.connect_buttons()
        self.initialize_backend()
        

    def get_stylesheet(self):
        return """
        QWidget {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        
        QWidget[class="card"] {
            background-color: white;
            border-radius: 15px;
            min-width: 300px;
            padding: 30px;
            margin-bottom: 20px;
        }
        
        QPushButton {
            background-color: #C17817;
            color: white;
            border: none;
            padding: 12px 20px;
            text-align: center;
            font-size: 16px;
            border-radius: 10px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #D7891B;
        }
        
        QPushButton:pressed {
            background-color: #9C5F13;
        }
        
        QMainWindow {
            background-color: #fcfaf7;
        }
        
        QLabel {
            font-size: 14px;
        }

        QLineEdit {
            padding: 8px;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            background-color: white;
            color: #2D3748;
            font-size: 14px;
        }

        QLineEdit:focus {
            border: 2px solid #C17817;
            outline: none;
        }

        QTableWidget {
            border: none;
            background-color: white;
            gridline-color: #E2E8F0;
        }

        QTableWidget::item {
            padding: 8px;
            border-bottom: 1px solid #E2E8F0;
        }

        QHeaderView::section {
            background-color: #F7FAFC;
            padding: 8px;
            border: none;
            border-bottom: 2px solid #E2E8F0;
            font-weight: bold;
            color: #2D3748;
        }

        QScrollArea {
            border: none;
            background-color: transparent;
        }

        QScrollBar:vertical {
            border: none;
            background: #E2E8F0;
            width: 10px;
            border-radius: 5px;
        }

        QScrollBar::handle:vertical {
            background: #CBD5E0;
            border-radius: 5px;
        }

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            border: none;
            background: none;
        }
        """
    def create_data_card(self, title):
        data_card = QTableWidget()
        data_card.setProperty("class", "card")
        data_card.setColumnCount(3)
        data_card.setHorizontalHeaderLabels(["Temperature (°C)", "Pressure (hPa)", "Humidity (%)"])
        data_card.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        return data_card
    # def create_data_card(self, title):
    #     data_card = QWidget()
    #     data_card.setProperty("class", "card")


    #     data_title = QLabel(title)
    #     data_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2D3748; margin-bottom: 20px; margin-left: 25px;")
    #     data_layout.addWidget(data_title)

    #     data_table = QTableWidget()
    #     data_table.setColumnCount(3)
    #     data_table.setHorizontalHeaderLabels(["Temperature (°C)", "Pressure (hPa)", "Humidity (%)"])
    #     data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    #     data_layout.addWidget(data_table)
    #     data_card.setLayout(data_layout)
    #     return data_card

    def initialize_charts(self):
        self.series_before = {}
        self.series_after = {}

        self.chart_layout.setSpacing(0)  # Espacement global entre tous les graphiques

        metrics = ["temperature", "pressure", "humidity"]

        self.metric_configs = {
            "temperature": {"color": QColor(255, 0, 0), "range": (15, 35), "title": "Température (°C)"},
            "pressure": {"color": QColor(0, 0, 255), "range": (900, 1100), "title": "Pression (hPa)"},
            "humidity": {"color": QColor(0, 255, 0), "range": (25, 80), "title": "Humidité (%)"}
        }

        for metric in metrics:
            # Create series for before and after brick
            self.series_before[metric] = QLineSeries()
            self.series_after[metric] = QLineSeries()


            chart = QChart()
            chart.setTitle(self.metric_configs[metric]['title'])
            chart.addSeries(self.series_before[metric])
            chart.addSeries(self.series_after[metric])
            chart.setTitle(f"{metric.capitalize()} Over Time")

            axis_x = QValueAxis()
            axis_x.setTitleText("Time (s)")
            axis_x.setRange(0, 100)
            chart.addAxis(axis_x, Qt.AlignBottom)

            axis_y = QValueAxis()
            axis_y.setTitleText(self.metric_configs[metric]['title'])
            axis_y.setRange(*self.metric_configs[metric]['range'])
            chart.addAxis(axis_y, Qt.AlignLeft)

            self.series_before[metric].attachAxis(axis_x)
            self.series_before[metric].attachAxis(axis_y)
            self.series_after[metric].attachAxis(axis_x)
            self.series_after[metric].attachAxis(axis_y)

            # Créer la vue du graphique
            chart_view = QChartView(chart)
            chart_view.setRenderHint(QPainter.Antialiasing)
            chart_view.setMinimumHeight(300)

            # Ajouter la vue à la disposition et stocker
            self.chart_layout.addWidget(chart_view)
            

    def initialize_backend(self):
        self.collector_before = DataCollector(BROKER_ADDRESS, ESP2_TOPIC_DATA)
        self.collector_after = DataCollector(BROKER_ADDRESS, ESP1_TOPIC_DATA)
        self.collector_before.data_collected.connect(lambda data: self.update_data("before", data))
        self.collector_after.data_collected.connect(lambda data: self.update_data("after", data))
        self.time_counter = 0

    def update_data(self, source, new_data):
        if source == "before":
            self.update_data_table(self.data_table_before_brick, new_data)
            self.update_chart(self.series_before, new_data)
        elif source == "after":
            self.update_data_table(self.data_table_after_brick, new_data)
            self.update_chart(self.series_after, new_data)

    def update_data_table(self, table, data):
        if not data:
            return
        row_position = table.rowCount()
        table.insertRow(row_position)
        table.setItem(row_position, 0, QTableWidgetItem(f"{data['temperature']:.2f}"))
        table.setItem(row_position, 1, QTableWidgetItem(f"{data['pressure']:.2f}"))
        table.setItem(row_position, 2, QTableWidgetItem(f"{data['humidity']:.2f}"))
        table.scrollToBottom()

    def update_chart(self, series_dict, data):
        if not data:
            return
        self.time_counter += 1
        for metric, series in series_dict.items():
            series.append(self.time_counter, data.get(metric, 0))

    def connect_buttons(self):
        self.start_button.clicked.connect(self.start_collecting)
        self.stop_button.clicked.connect(self.stop_collecting)
        self.clear_button.clicked.connect(self.clear_data)
        self.export_button.clicked.connect(self.export_data)
        self.back_button.clicked.connect(self.close)

    def start_collecting(self):
        client = mqtt.Client()
        client.connect(BROKER_ADDRESS, 1234)
        client.publish(ESP1_TOPIC_CONTROL, "START")
        client.publish(ESP2_TOPIC_CONTROL, "START")
        client.disconnect()
        print("Started collecting data")

    def stop_collecting(self):
        client = mqtt.Client()
        client.connect(BROKER_ADDRESS, 1234)
        client.publish(ESP1_TOPIC_CONTROL, "STOP")
        client.publish(ESP2_TOPIC_CONTROL, "STOP")
        client.disconnect()
        print("Stopped collecting data")

    def clear_data(self):
        self.data_table_before_brick.setRowCount(0)
        self.data_table_after_brick.setRowCount(0)
        for series in self.series_before.values():
            series.clear()
        for series in self.series_after.values():
            series.clear()

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
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )
        
        # Créer des styles personnalisés
        styles = getSampleStyleSheet()
        
        # Style du titre principal
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2D3748'),
            fontName='Helvetica-Bold'
        ))
        
        # Style des sous-titres
        styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=styles['Heading2'],
            fontSize=18,
            spaceBefore=20,
            spaceAfter=20,
            textColor=colors.HexColor('#2D3748'),
            fontName='Helvetica-Bold'
        ))
        
        # Style du texte normal
        styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#4A5568'),
            fontName='Helvetica',
            spaceBefore=6,
            spaceAfter=6
        ))
        
        # Elements du rapport
        elements = []
        
        # En-tête avec logo
        header = Table([[
            Paragraph("Rapport de Mesures du Banc de Test", styles['CustomTitle'])
        ]], colWidths=[None])
        header.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(header)
        elements.append(Spacer(1, 20))
        
        # Informations de base
        from datetime import datetime
        now = datetime.now()
        
        # Carte d'informations
        info_data = [
            [Paragraph("Date et heure :", styles['CustomNormal']),
            Paragraph(now.strftime('%d/%m/%Y %H:%M:%S'), styles['CustomNormal'])],
            [Paragraph("Durée de la mesure :", styles['CustomNormal']),
            Paragraph(f"{len(self.data)} secondes", styles['CustomNormal'])]
        ]
        
        info_table = Table(info_data, colWidths=[150, None])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F7FAFC')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROUNDEDCORNERS', [10, 10, 10, 10]),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 30))

        if self.data:
            # Calculs statistiques
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

            elements.append(Paragraph("Résumé des Statistiques", styles['CustomHeading']))
            
            # Tableau des statistiques
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
                # En-tête
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#C17817')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                # Corps du tableau
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFFFFF')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#4A5568')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 10),
                # Coins arrondis pour le tableau entier
                ('ROUNDEDCORNERS', [10, 10, 10, 10]),
            ]))
            
            elements.append(stats_table)
            elements.append(Spacer(1, 30))

            # Tableau détaillé
            elements.append(Paragraph("Données Détaillées", styles['CustomHeading']))
            
            full_data = [['N°', 'Température (°C)', 'Pression (hPa)', 'Humidité (%)']]
            for index, entry in enumerate(self.data, 1):
                full_data.append([
                    str(index),
                    f"{entry['temperature']:.2f}",
                    f"{entry['pressure']:.2f}",
                    f"{entry['humidity']:.2f}"
                ])

            data_table = Table(full_data, repeatRows=1)
            data_table.setStyle(TableStyle([
                # En-tête
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#C17817')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                # Corps du tableau
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#4A5568')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 8),
                # Style alterné pour les lignes
                *[('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F7FAFC')) for i in range(2, len(full_data), 2)],
            ]))
            
            elements.append(data_table)
            elements.append(Spacer(1, 30))

            # Graphiques
            elements.append(Paragraph("Visualisation des Données", styles['CustomHeading']))
            
            for metric in ['temperature', 'pressure', 'humidity']:
                graph_path = f"{metric}_graph.png"
                try:
                    img = Image(graph_path, width=450, height=280)
                    img.hAlign = 'CENTER'
                    elements.append(Paragraph(f"Graphique - {metric.capitalize()}", styles['CustomNormal']))
                    elements.append(img)
                    elements.append(Spacer(1, 20))
                except Exception as e:
                    print(f"Erreur lors de l'ajout du graphique {metric}: {e}")

        else:
            elements.append(Paragraph(
                "Aucune donnée n'a été collectée.",
                styles['CustomNormal']
            ))

        # Pied de page
        elements.append(Spacer(1, 30))
        footer = Paragraph(
            "© 2025 - INSA Toulouse",
            ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#A0AEC0'),
                alignment=1
            )
        )
        elements.append(footer)

        # Construire le PDF
        doc.build(elements)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    home_window = HomeWindow()
    home_window.show()
    sys.exit(app.exec_())
