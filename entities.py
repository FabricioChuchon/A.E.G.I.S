import numpy as np
from abc import ABC
from sensors import SpaceDebrisSensor 
from brain import AegisBrain
from guidance import GuidanceSystem
from actuators import PropulsionSystem 

class SpaceObject(ABC):
    def __init__(self, r_init, v_init, dynamics_engine):
        self._state = np.concatenate([r_init, v_init])
        self.dynamics = dynamics_engine
        self.history = [self._state.copy()]
        
    def propagate(self, dt):
        phi = self.dynamics.get_transition_matrix(dt)
        self._state = phi @ self._state
        self.history.append(self._state.copy())

    @property
    def position(self): return self._state[:3]
    @property
    def velocity(self): return self._state[3:]

class Satellite(SpaceObject):
    def __init__(self, dynamics_engine):
        # Iniciamos en el origen del marco LVLH
        super().__init__([0,0,0], [0,0,0], dynamics_engine)
        self.name = "A.E.G.I.S. Sat"
        self.radius_hitbox = 2.5
        self.brain = AegisBrain()
        self.sensor = SpaceDebrisSensor(position=[0,0,0], detection_range=200.0)       
        self.guidance = GuidanceSystem(dynamics_engine)
        self.propulsion = PropulsionSystem(initial_fuel_mass=150.0, dry_mass=180.0, isp=230.0)
        # Historial para telemetría IoT
        self.fuel_history = [self.propulsion.fuel_mass]

    def propagate(self, dt):
        super().propagate(dt)
        # Registramos el consumo para que el Dashboard pueda graficarlo
        self.fuel_history.append(self.propulsion.fuel_mass)

    def calculate_avoidance(self, r_rel, v_rel, tca):
        """Calcula el vector de empuje y la trayectoria fantasma de escape."""
        thrust = self.guidance.calculate_maneuver(r_rel, v_rel, tca)
        t_predict = tca * 1.2 if tca > 0 else 100
        ghost_path = self.guidance.predict_evasive_trajectory(r_rel, v_rel, thrust, t_predict)
        return thrust, ghost_path

    def maneuver(self, thrust_vector):
        """Aplica el cambio de velocidad (Delta-V) al estado del satélite."""
        real_thrust = self.propulsion.execute_burn(thrust_vector)
        if np.linalg.norm(real_thrust) > 0:
            self._state[3:6] += real_thrust

class Debris(SpaceObject):
    def __init__(self, r_init, v_init, dynamics_engine, debris_id):
        super().__init__(r_init, v_init, dynamics_engine)
        self.id = debris_id

    @classmethod
    def create_collision_threat(cls, dynamics, t_impact, debris_id):
        """Método de fábrica para generar amenazas que convergen hacia el satélite."""
        miss_offset = np.random.normal(0, 0.8, 3)
        r_final = miss_offset
        speed = np.random.uniform(0.1, 0.3)
        direction = np.random.randn(3)
        direction /= np.linalg.norm(direction)
        v_final = direction * speed
        phi_inv = dynamics.get_transition_matrix(-t_impact)
        state_final = np.concatenate([r_final, v_final])
        state_initial = phi_inv @ state_final
        return cls(state_initial[:3], state_initial[3:], dynamics, debris_id)