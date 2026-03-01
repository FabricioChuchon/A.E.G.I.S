import paho.mqtt.client as mqtt
import random
import time
import json  

class AegisTelemetry:
    def __init__(self):
        self.broker = "test.mosquitto.org"
        self.port = 1883
        self.base_topic = "uni/aegis/fabricio/"
        
        client_id = f"AegisSat_{random.randint(1000, 9999)}"
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
        
        self.launch_signal = False
        self.client.on_message = self._on_message 

    def _on_message(self, client, userdata, msg):
        comando = msg.payload.decode("utf-8").strip().upper()
        if comando == "INICIAR":
            self.launch_signal = True

    def connect(self):
        print("\n[TELEMETRÍA] Alineando antena IoT con la Estación Terrena...")
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start() 
            print("[TELEMETRÍA] ✅ Enlace MQTT establecido.")
        except Exception as e:
            print(f"[TELEMETRÍA] ❌ Error de red: {e}")

    def wait_for_launch(self):
        comando_topic = self.base_topic + "comando"
        time.sleep(1) 
        self.client.subscribe(comando_topic) 
        
        print(f"\n[STANDBY] SISTEMA LISTO. Esperando comando en el canal: {comando_topic}")
        print(f">>> Presiona el botón 'INICIAR' en tu celular <<<\n")
        
        while not self.launch_signal:
            time.sleep(0.5)
            
        print("🚀 ¡COMANDO DE IGNICIÓN ACEPTADO! Iniciando secuencia de vuelo...")
        self.client.unsubscribe(comando_topic) 

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

    # --- FUNCIONES DE ENVÍO DE DATOS EN VIVO ---
    def send_fuel(self, fuel):
        self.client.publish(self.base_topic + "combustible", str(round(fuel, 1)))

    def send_status(self, status):
        self.client.publish(self.base_topic + "estado", status)

    def send_threats(self, count):
        self.client.publish(self.base_topic + "amenazas", count)

    def send_speed(self, speed):
        self.client.publish(self.base_topic + "velocidad", str(round(speed, 2)))

    def send_action(self, action):
        self.client.publish(self.base_topic + "accion", action)

    def send_montecarlo_report(self, survival_rate, avg_fuel, total_evasions):
        topic = self.base_topic + "reporte"
        payload = {
            "Supervivencia": f"{survival_rate}%",
            "Combustible Medio": f"{avg_fuel} kg",
            "Evasiones Totales": total_evasions
        }
        self.client.publish(topic, json.dumps(payload, indent=2))