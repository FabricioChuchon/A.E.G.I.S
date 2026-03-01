import numpy as np

# Constantes Físicas (Tierra)
MU_EARTH = 398600.4418  # km^3/s^2
EARTH_RADIUS = 6378.137 # km

class RelativeDynamics:
    def __init__(self, altitude_km):
        # Calculamos el radio de la órbita y la velocidad angular media
        r_orbit = EARTH_RADIUS + altitude_km
        self.ang_v = np.sqrt(MU_EARTH / r_orbit**3) # rad/s
        self.period = 2 * np.pi / self.ang_v
        
        print(f"[FÍSICA] Motor HCW inicializado. Altura: {altitude_km} km.")
        print(f"[FÍSICA] Periodo orbital: {self.period/60:.2f} min.")

    def get_transition_matrix(self, dt):
       
        ang_v = self.ang_v
        c = np.cos(ang_v * dt)
        s = np.sin(ang_v * dt)

        # Ecuaciones HCW estándar (Matriz Phi)
        phi = np.array([
            [4 - 3*c         ,      0,          0,         (1/ang_v)*s,     (2/ang_v)*(1-c),              0],
            [6*(s - ang_v*dt),      1,          0,    -(2/ang_v)*(1-c),  (4/ang_v)*s - 3*dt,              0],
            [0               ,      0,          c,                   0,                   0,    (1/ang_v)*s],
            [3*ang_v*s       ,      0,          0,                   c,                 2*s,              0],
            [-6*ang_v*(1-c)  ,      0,          0,                -2*s,             4*c - 3,              0],
            [0               ,      0,   -ang_v*s,                   0,                   0,              c]
        ])
        
        return phi