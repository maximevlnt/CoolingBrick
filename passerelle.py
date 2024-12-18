import serial
import time

PORT = '/dev/ttyUSB0'  # Remplacez par le bon port série
BAUD_RATE = 9600       # Assurez-vous que cela correspond au paramétrage de l'ESP8266
CSV_FILE = 'data.csv'  # Nom du fichier CSV

def main():
    try:
        print("Connexion à l'ESP8266...")
        ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # Laisser le temps à l'ESP8266 de s'initialiser

        # Envoyer la commande pour démarrer l'acquisition
        ser.write(b'START\n')
        print("Commande START envoyée.")

        with open(CSV_FILE, 'w') as f:
            f.write('Temperature,Humidity\n')  # Écrire l'entête du CSV

            while True:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    print(f"Données reçues : {line}")
                    if line.startswith("temp:"):
                        # Extraire les valeurs de température et d'humidité
                        data = line.split(',')
                        temp = data[0].split(':')[1]
                        hum = data[1].split(':')[1]

                        # Écrire les données dans le fichier CSV
                        f.write(f'{temp},{hum}\n')
    except KeyboardInterrupt:
        print("\nArrêt du script.")
    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            # Envoyer la commande pour arrêter l'acquisition
            ser.write(b'STOP\n')
            ser.close()
            print("Connexion série fermée.")

if __name__ == "__main__":
    main()



