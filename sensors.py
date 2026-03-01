import numpy as np
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