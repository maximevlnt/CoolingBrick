#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <DHT.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_DPS310.h> // Pour le baromètre DPS310
#include <Adafruit_TMP117.h> // Pour le capteur TMP117

// Configuration du capteur DHT
#define DHTPIN D3       // Pin où le capteur DHT est connecté
#define DHTTYPE DHT22   // Type de capteur : DHT11 ou DHT22
DHT dht(DHTPIN, DHTTYPE);

// Configuration des capteurs I2C
Adafruit_DPS310 dps310; // Capteur DPS310
Adafruit_TMP117 tmp117; // Capteur TMP117

// Configuration du réseau WiFi
const char* ssid = "nom de votre partage de connexion";
const char* password = "code de votre partage de connexion";

// Configuration du broker MQTT
const char* mqtt_server = "172.20.10.2";
const int mqtt_port = 1234;
const char* topic = "ESP1/data";

WiFiClient espClient;
PubSubClient client(espClient);

bool acquisitionActive = false; // Flag pour savoir si l'acquisition est active

void setup() {
  // Initialisation du port série
  Serial.begin(9600);

  // Connexion au WiFi
  setup_wifi();

  // Configuration du client MQTT
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  // Initialisation des capteurs
  dht.begin();

  // Initialisation DPS310
  if (!dps310.begin_I2C()) {
    Serial.println("Erreur de connexion au baromètre DPS310 !");
  } else {
    Serial.println("Baromètre DPS310 initialisé !");
    dps310.configurePressure(DPS310_64HZ, DPS310_64SAMPLES);
    dps310.configureTemperature(DPS310_64HZ, DPS310_64SAMPLES);
  }

  // Initialisation TMP117
  if (!tmp117.begin()) {
    Serial.println("Erreur de connexion au capteur TMP117 !");
  } else {
    Serial.println("TMP117 initialisé !");
  }

  Serial.println("ESP8266 prêt. Envoyez 'START' ou 'STOP' via MQTT pour gérer l'acquisition.");
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Si l'acquisition est active, lire et publier les données
  if (acquisitionActive) {
    // Lecture des données DHT
    float dhtHumidity = dht.readHumidity();

    // Lecture des données DPS310
    sensors_event_t tempEvent, pressureEvent;
    float pressure = 0.0;
    if (dps310.temperatureAvailable() && dps310.pressureAvailable()) {
      dps310.getEvents(&tempEvent, &pressureEvent);
      pressure = pressureEvent.pressure; // Pression en hPa
    }

    // Lecture des données TMP117
    tmp117.getEvent(&tempEvent);
    float tmp117Temperature = tempEvent.temperature;

    // Vérification des valeurs
    if (isnan(dhtHumidity)) {
      Serial.println("Erreur de lecture du capteur DHT !");
    } else if (isnan(pressure) || pressure < 300 || pressure > 3000) {
      Serial.println("Erreur de lecture du baromètre !");
    } else if (isnan(tmp117Temperature)) {
      Serial.println("Erreur de lecture de la température TMP117 !");
    } else {
      // Création d'un message JSON pour les données
      String payload = "{";
      payload += "\"humidity\": " + String(dhtHumidity) + ", ";
      payload += "\"temperature\": " + String(tmp117Temperature) + ", ";
      payload += "\"pressure\": " + String(pressure);
      payload += "}";

      // Publication sur le topic MQTT
      client.publish(topic, payload.c_str());
      Serial.println("Données envoyées : " + payload);
    }

    delay(4000); // Pause entre les lectures
  }
}

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connexion au WiFi ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connecté");
  Serial.print("Adresse IP : ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message reçu [");
  Serial.print(topic);
  Serial.print("] ");
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  message.trim();
  Serial.println(message);

  if (message == "START") {
    acquisitionActive = true;
    Serial.println("Acquisition démarrée.");
  } else if (message == "STOP") {
    acquisitionActive = false;
    Serial.println("Acquisition arrêtée.");
  }
}

void reconnect() {
  // Boucle jusqu'à ce que la connexion soit rétablie
  while (!client.connected()) {
    Serial.print("Connexion au broker MQTT...");
    // Tentative de connexion
    if (client.connect("ESP8266Client")) {
      Serial.println("connecté");
      // S'abonner au topic de contrôle
      client.subscribe("ESP1/control");
    } else {
      Serial.print("échec, rc=");
      Serial.print(client.state());
      Serial.println(" nouvelle tentative dans 5 secondes");
      delay(5000);
    }
  }
}
