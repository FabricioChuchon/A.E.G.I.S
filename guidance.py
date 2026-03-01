import numpy as np

class GuidanceSystem:    
    def __init__(self, dynamics_engine):
        self.dynamics = dynamics_engine
        self.dv_magnitude = 0.010

    def calculate_maneuver(self, r_rel, v_rel, tca):  
      
        if tca <= 0:
            return np.zeros(3)            
        phi = self.dynamics.get_transition_matrix(tca)
        phi_rv = phi[0:3, 3:6]
        phi_rr = phi[0:3, 0:3]
        #  Predicción de la posición de colisión en el TCA
        r_collision_pred = phi_rr @ r_rel + phi_rv @ v_rel
        #  Determinación de la dirección de escape
        norm_pred = np.linalg.norm(r_collision_pred)
        
        if norm_pred == 0:
            u_escape = np.array([1.0, 0, 0])
        else:
            u_escape = - (r_collision_pred / norm_pred)
        # Optimización: El gradiente indica la dirección de mayor cambio en la posición final
        gradient = phi_rv.T @ u_escape
        grad_norm = np.linalg.norm(gradient)
        
        if grad_norm == 0:
            direction = u_escape
        else:
            direction = gradient / grad_norm
        #  Generación del vector de empuje final
        return direction * self.dv_magnitude

    def predict_evasive_trajectory(self, r_rel, v_rel, thrust_vector, t_duration):
      
        visual_duration = max(t_duration, 2000.0)
        # Estado inicial relativo (el satélite es el origen en el momento de la quema)
        state = np.concatenate([np.zeros(3), thrust_vector])
        points = []
        dt_step = 10.0
        steps = int(visual_duration / dt_step)
        
        for _ in range(steps):
            phi = self.dynamics.get_transition_matrix(dt_step)
            state = phi @ state
            points.append(state[:3])
        return np.array(points)
    