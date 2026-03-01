import numpy as np

class AegisBrain:
    def __init__(self, sigma=10.0):
        # Desviación estándar de la incertidumbre (en metros/km según escala)
        self.sigma = sigma

    def calculate_risk(self, r_rel, v_rel):
        """Analiza el vector de posición y velocidad relativa para predecir impactos."""
        r_dot_v = np.dot(r_rel, v_rel)
        v_mag_sq = np.dot(v_rel, v_rel)
        if v_mag_sq == 0:
            return {"tca": -1, "miss_distance": 9999, "probability": 0.0}
        tca = - r_dot_v / v_mag_sq
        # Distancia de fallo (Miss Distance)
        if tca < 0:
            # Si el TCA es negativo, el objeto ya pasó o se aleja
            miss_distance = np.linalg.norm(r_rel)
            probability = 0.0
        else:
            # Proyectamos la posición lineal en el futuro usando el TCA
            r_at_tca = r_rel + v_rel * tca
            miss_distance = np.linalg.norm(r_at_tca)
            #  Probabilidad de Colisión
            probability = np.exp(-(miss_distance**2) / (2 * self.sigma**2))
        return {
            "tca": tca,
            "miss_distance": miss_distance,
            "probability": probability
        }