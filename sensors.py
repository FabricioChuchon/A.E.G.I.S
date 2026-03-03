import numpy as np
import serial 
import time
from abc import ABC, abstractmethod

class ISensor(ABC):
    @abstractmethod
    def measure(self, true_position):
        pass

class SpaceDebrisSensor(ISensor): 
    def __init__(self, position, detection_range, noise_std_distance=1.0):
        """
        Sensor de Seguimiento Táctico:
        Provee coordenadas 3D con ruido gaussiano dentro de un rango específico.
        """
        self.position = np.array(position)
        self.detection_range = detection_range
        self.noise_std_distance = noise_std_distance

    def measure(self, true_position):
        """
        Simula un rastreo 3D para telemetría y guiado.
        Retorna: Array (x, y, z) con ruido o ceros si está fuera de rango.
        """
        # 1. Chequeo de rango esférico
        r_vector = true_position - self.position
        dist_real = np.linalg.norm(r_vector)
        if dist_real > self.detection_range:
            return np.array([0.0, 0.0, 0.0])
        # 2. Generar Ruido Vectorial 3D (Simula error de radar)
        noise_vector = np.random.normal(0, self.noise_std_distance, 3)
        return true_position + noise_vector
class HardwareRadarSensor(ISensor):
    def __init__(self, port='COM5', baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.detection_range = 50.0  
        self.current_pos = np.array([0.0, 0.0, 0.0])
        self.lecturas = []  # <-- Memoria circular ultra-rápida

        self.connected = False
        
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.05)
            self.ser.flushInput() 
            self.connected = True
            print(f"[HARDWARE] Radar A.E.G.I.S. activo en {self.port}")
        except Exception as e:
            self.connected = False
            print(f"[ERROR] No se detectó hardware en {self.port}. Revisa el cable USB")

    def measure(self, true_position=None):
        posicion_vacia = np.array([0.0, 0.0, 0.0])

        if self.ser and self.ser.in_waiting > 0:
            try:
                raw_data = self.ser.read_all().decode('utf-8', errors='ignore')
                lines = [line for line in raw_data.split('\n') if line.strip()] 
                
                if lines:
                    last_line = lines[-1].strip()
                    datos = last_line.split(',')

                    # Ahora sí usamos los 3 datos: pan, tilt y distancia
                    if len(datos) >= 3:
                        pan_deg_raw = float(datos[0])
                        tilt_deg_raw = float(datos[1])
                        dist_cm_raw = float(datos[2])

                        # Guardamos la tupla entera en nuestra memoria circular
                        self.lecturas.append((pan_deg_raw, tilt_deg_raw, dist_cm_raw))
                        if len(self.lecturas) > 3:
                            self.lecturas.pop(0) 
                            
                        if len(self.lecturas) == 3:
                            # Aplicamos mediana a TODO para evitar temblores del servo y saltos del sensor
                            pan_deg = np.median([lec[0] for lec in self.lecturas])
                            tilt_deg = np.median([lec[1] for lec in self.lecturas])
                            dist_cm = np.median([lec[2] for lec in self.lecturas])
                            
                            if 5.0 < dist_cm < 40.0:
                                r_km = dist_cm * 0.5 
                                
                                # Convertimos grados de Arduino (0 a 180) a radianes centrados
                                # Asumimos que 90° es el centro exacto (mirando al frente)
                                pan_rad = np.radians(pan_deg - 90.0)
                                tilt_rad = np.radians(tilt_deg - 90.0)
                                
                                # Trigonometría esférica real
                                x = r_km * np.cos(tilt_rad) * np.cos(pan_rad)
                                y = r_km * np.cos(tilt_rad) * np.sin(pan_rad)
                                z = r_km * np.sin(tilt_rad)

                                self.current_pos = np.array([x, y, z], dtype=float)
                                return self.current_pos
            except Exception:
                pass 
                
        self.current_pos = posicion_vacia
        return self.current_pos
