#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_DPS310.h> // Pour le baromètre DPS310
#include <Adafruit_TMP117.h> // Pour le capteur TMP117
#include <DHT.h>            // Pour le Grove Temp/Humidity Sensor Pro
#include <ArduinoJson.h>    // Pour simplifier la gestion des JSON
#include <dimmable_light.h>


// Configuration resistance chauffante
const int syncPin = D7;
const int thyristorPin = 15; //D8

//Config vitesse commande vent 
float commandSpeed =0;

DimmableLight light(thyristorPin);

// Paramètres du correcteur PI
float Kp = 150.0; // Gain proportionnel
float Ki = 0.5; // Gain intégral
float setPoint = 0.0; // Consigne en degrés Celsius
float dt = 0.1; // Intervalle de temps entre les mises à jour (en secondes)

// Variables pour le PI
float integral = 0;
float lastError = 0;

// Configuration du capteur DHT
#define DHTPIN D3       // Pin où le capteur DHT est connecté
#define DHTTYPE DHT22  // Type de capteur : DHT11 ou DHT22
DHT dht(DHTPIN, DHTTYPE);

// Pin du capteur de flow
const int analogPin = A0;

// Constantes pour les conversions (ajustez selon la documentation du capteur ou expérimentation)
const float maxVoltage = 3.3;    // Tension maximale sur A0 (NodeMCU)
const int adcResolution = 1024; // Résolution ADC (0-1023)
const int maxFlowCapteur = 150; // Max Flow Capteur 
const float conversion = 0.0531;


// Configuration des broches pour les actionneurs
#define FAN_PIN 12       // Pin pour le contrôle du ventilateur
#define HEATER_PIN D8    // Pin pour le contrôle de la résistance chauffante

// Configuration des capteurs I2C
Adafruit_DPS310 dps310; // Capteur DPS310
Adafruit_TMP117 tmp117; // Capteur TMP117

// Configuration du réseau WiFi
const char* ssid = "nom de votre partage de connexion";
const char* password = "code de votre partage de connexion";

// Configuration du broker MQTT
const char* mqtt_server = "172.20.10.2";
const int mqtt_port = 1234;                 // Port par défaut du broker MQTT
const char* data_topic = "ESP2/data";       // Topic pour publier les données
const char* control_topic = "ESP2/control"; // Topic pour démarrer/arrêter l'acquisition
const char* command_topic = "ESP2/command"; // Topic pour recevoir les commandes pour les actionneurs
const char* status_topic = "ESP2/status";   // Topic pour envoyer l'état

WiFiClient espClient;
PubSubClient client(espClient);

bool acquisitionActive = false; // Flag pour savoir si l'acquisition est active

void setup() {
  // Initialisation des broches
  pinMode(FAN_PIN, OUTPUT);
  pinMode(HEATER_PIN, OUTPUT);
  
  // Définir la résolution de la PWM (0 à 1023 = 10 bits)
  analogWriteRange(1023);

  // Définir la fréquence de la PWM à 1 kHz
  analogWriteFreq(100);

  
  // Initialisation du port série
  Serial.begin(9600);

  // Connexion au WiFi
  setup_wifi();

  // Configuration du client MQTT
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  // Initialisation des capteurs
  dht.begin();

  Serial.print("Initializing DimmableLight library... ");
  DimmableLight::setSyncPin(syncPin);
  // VERY IMPORTANT: Call this method to activate the library
  DimmableLight::begin();
  Serial.println("Done!");


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

  Serial.println("ESP8266 prêt. Envoyez 'START' ou 'STOP' sur ESP2/control pour gérer l'acquisition.");
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

   // Lire et publier les températures sur ESP2/temp en continu
  float tmp117Temperature = 0.0;
  sensors_event_t tempEvent;

  // Lecture des données TMP117
  if (tmp117.begin()) {
    tmp117.getEvent(&tempEvent);
    tmp117Temperature = tempEvent.temperature;
  }

  float dhttemperature = dht.readTemperature();

  // Vérification de la validité des données
  if (isnan(tmp117Temperature) || tmp117Temperature < -40 || tmp117Temperature > 80) {
    Serial.println("Erreur ou température TMP117 hors plage !");
    tmp117Temperature = 0.0;
  }

  // Publier la température sur le topic MQTT
  String tempPayload = "{";
  tempPayload += "\"temperature\": " + String(dhttemperature);
  tempPayload += "}";

  client.publish("ESP2/temp", tempPayload.c_str());
  Serial.println("Température envoyée sur ESP2/temp : " + tempPayload);

  // Mesure de la température
  float temperature = dhttemperature; // Fonction pour lire la température

  // Période de chauffe
  if (temperature<=setPoint-1){


    Serial.println("Préchauffage");
    
    //commande du vent pour le prechauffage
    int fanSpeed = 10;
    int fanCommand = fanSpeed*100/35;
    fanCommand = 1024 - fanCommand*1024/100;
    Serial.print("Valeur de fan :");
    Serial.println(fanCommand);
    
    analogWrite(FAN_PIN,fanCommand);

 
    // Application de la commande de chauffe au maximum
    light.setBrightness((int)255);

    
  }



  // lancement des commandes 

  if (temperature>setPoint-1){

    //commande du vent pour le prechauffage
    int fanSpeed = commandSpeed;
    Serial.print("valeur de vitesse à envoyer :");
    Serial.println(commandSpeed);
    int fanCommand = fanSpeed*100/35;
    fanCommand = 1024 - fanCommand*1024/100;
    analogWrite(FAN_PIN,fanCommand);

    // calcul du chauffage 

    float error = setPoint - temperature;
    Serial.print("Valeur de l'erreur :");
    Serial.println(error);

    // Calcul du terme proportionnel
    float P = Kp * error;

    Serial.print("Valeur de P :");
    Serial.println(P);


    // Calcul du terme intégral
    integral += error * dt;
    float I = Ki * integral;

    Serial.print("Valeur de I :");
    Serial.println(I);

    // Calcul de la commande PI
    float output = P + I;

    Serial.print("Valeur de commande avant modif :");
    Serial.println(output);


    // Limitation de la commande entre 0 et 255 (valeurs PWM)
    output = constrain(output, 0, 255);

    output = output +170;

    Serial.print("Valeur de commande :");
    Serial.println(output);

    Serial.print("Valeur de commande int :");
    Serial.println((int)output);
  
    // Application de la commande
    light.setBrightness((int)output);
    Serial.println(light.getBrightness());
  }
  

  

  // Lire la valeur brute analogique capteur flow
  int rawValue = analogRead(analogPin);

  float flow_value = rawValue*maxFlowCapteur/adcResolution;  

  float flow_speed = flow_value*0.0531;

  // Publier la température sur le topic MQTT
  String flowPayload = "{";
  flowPayload += "\"flow\": " + String(flow_speed);
  flowPayload += "}";

  client.publish("ESP2/flow", flowPayload.c_str());
  Serial.println("Température envoyée sur ESP2/flow : " + flowPayload);

  

  delay(2000);



  // Si l'acquisition est active, lire et publier les données
  if (acquisitionActive) {
    // Lecture des données DHT
    float dhtHumidity = dht.readHumidity();
  
    
     // Lecture des données DPS310
    sensors_event_t pressureEvent;
    float pressure = 0.0;
    if (dps310.temperatureAvailable() && dps310.pressureAvailable()) {
      dps310.getEvents(&tempEvent, &pressureEvent);
      pressure = pressureEvent.pressure; // Pression en hPa
    }

       // Vérification des valeurs
    if (isnan(dhtHumidity) || dhtHumidity < 0 || dhtHumidity > 100) {
      Serial.println("Erreur ou humidité hors plage !");
      dhtHumidity = 0.0;
    }

    if (isnan(pressure)) {
      Serial.println("Erreur de lecture du baromètre DPS310 !");
    } else {
      // Création d'un message JSON pour les données
      String payload = "{";
      payload += "\"humidity\": " + String(dhtHumidity) + ", ";
      payload += "\"temperature\": " + String(dhttemperature) + ", ";
      payload += "\"pressure\": " + String(pressure);
      payload += "}";

      // Publication sur le topic MQTT
      client.publish(data_topic, payload.c_str());
      Serial.println("Données envoyées : " + payload);

    }

    delay(2000); // Pause entre les lectures
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
    yield(); // Prévenir le blocage
  }
  message.trim();
  Serial.println(message);

  if (String(topic) == control_topic) {
    // Commandes de contrôle : START/STOP
    if (message == "START") {
      acquisitionActive = true;
      Serial.println("Acquisition démarrée.");
    } else if (message == "STOP") {
      acquisitionActive = false;
      Serial.println("Acquisition arrêtée.");
    }
  } else if (String(topic) == command_topic) {
    // Commandes pour les actionneurs
    StaticJsonDocument<128> doc;
    DeserializationError error = deserializeJson(doc, message);
    if (error) {
      Serial.println("Erreur : JSON invalide.");
      return;
    }

    if (doc.containsKey("wind_speed")) {
      commandSpeed = doc["wind_speed"];

      
      //analogWrite(FAN_PIN,fanCommand);
      Serial.print("Ventilateur vitesse voulu pour expériementation : ");
      Serial.println(commandSpeed);
    }

    if (doc.containsKey("temperature")) {
      int heaterState = doc["temperature"];
      setPoint = heaterState;
      Serial.print("Résistance chauffante température voulu : ");
      Serial.println(heaterState);
    }
  }

  // Envoyer l'état actuel
  send_status();
}

void send_status() {
  String status = "{";
  status += "\"fan_speed\": " + String(analogRead(FAN_PIN)) + ", ";
  status += "\"heater_state\": " + String(digitalRead(HEATER_PIN));
  status += "}";
  client.publish(status_topic, status.c_str());
}

void reconnect() {
  // Boucle jusqu'à ce que la connexion soit rétablie
  while (!client.connected()) {
    Serial.print("Connexion au broker MQTT...");
    if (client.connect("ESP8266Control")) {
      Serial.println("connecté");
      client.subscribe(control_topic);
      client.subscribe(command_topic);
    } else {
      Serial.print("échec, rc=");
      Serial.print(client.state());
      Serial.println(" nouvelle tentative dans 5 secondes");
      delay(5000);
    }
  }
}
