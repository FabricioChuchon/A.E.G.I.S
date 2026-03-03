import numpy as np
import time
from physics import RelativeDynamics
from entities import Satellite, Debris
from visualizer import DynamicDashboard
from sensors import HardwareRadarSensor

def run_live_aegis():
    print("--- INICIANDO SISTEMA A.E.G.I.S. (MODO RADAR DE ALERTA) ---")
    
    # 1. Configuración de Física
    leo_physics = RelativeDynamics(altitude_km=800)
    radar_arduino = HardwareRadarSensor(port ='COM5')
    sat = Satellite(leo_physics, sensor_equipado=radar_arduino)
    
    # 2. OBJECT POOLING: Creamos una "piscina" de 5 basuras espaciales dormidas.
    # Las inicializamos lejísimos (9999 km) para que el radar no las vea al inicio.
    POOL_SIZE = 10 #Numero de basuras espaciales
    debris_pool = []
    for i in range(POOL_SIZE):
        d = Debris(np.array([9999.0, 9999.0, 9999.0]), np.array([0.0, 0.0, 0.0]), leo_physics, debris_id=i)
        debris_pool.append(d)
    
    # 3. Inicializar el Dashboard con la piscina completa
    dashboard = DynamicDashboard(sat, debris_pool)
    
    # --- ESPERA DE COMANDO IOT ---
    # Lo dejamos comentado para que puedas probar el hardware instantáneamente
    # dashboard.telemetry.wait_for_launch()
    
    # --- VARIABLES DE CONTROL DEL RADAR ---
    cooldown_time = 1.5      # 1.5 segundos de bloqueo entre detecciones
    last_detect_time = 0.0   # Marca de tiempo de la última detección
    current_d_idx = 0        # Índice de la basura a despertar
    
    # --- LÓGICA DE TIEMPO REAL ---
    def real_time_loop(frame):
        nonlocal last_detect_time, current_d_idx
        dt = 0.5 
        current_time = time.time()
        
        pos_medida = sat.sensor.measure() 
        dist_sensor = np.linalg.norm(pos_medida)
        
        # B. DISPARO EN FILA INDIA
        if dist_sensor > 0.0001 and (current_time - last_detect_time) > cooldown_time:
            threat = debris_pool[current_d_idx]
            
            direccion_mano = pos_medida / dist_sensor 
            distancia_spawn = 45.0 
            abs_pos = sat.position + (direccion_mano * distancia_spawn)
            
            noise = np.random.normal(0, 0.02, 3) 
            attack_vector = -direccion_mano + noise
            velocidad_misil = 0.35 
            attack_vector = (attack_vector / np.linalg.norm(attack_vector)) * velocidad_misil
            
            threat._state[:3] = abs_pos
            threat._state[3:] = attack_vector
            
            last_detect_time = current_time
            current_d_idx = (current_d_idx + 1) % POOL_SIZE
            
        # C. PROPAGACIÓN
        closest_dist = 9999.0
        closest_threat = None
        
        for d in debris_pool:
            d.propagate(dt)
            rel_pos = d.position - sat.position
            d_dist = np.linalg.norm(rel_pos)
            
            if d_dist < 50.0 and d_dist < closest_dist:  
                closest_dist = d_dist
                closest_threat = d
                
        if closest_threat is not None and closest_dist < 50.0:
            rel_pos = closest_threat.position - sat.position
            rel_vel = closest_threat.velocity - sat.velocity
            risk = sat.brain.calculate_risk(rel_pos, rel_vel)
            
            if risk['probability'] > 0.4 and risk['tca'] > 0:
                thrust, _ = sat.calculate_avoidance(rel_pos, rel_vel, risk['tca'])
                sat.maneuver(thrust)
        
        sat.propagate(dt)
        return dashboard.update(frame)

    # 4. Lanzamos la simulación pasando nuestra nueva lógica
    dashboard.start_simulation(live_func=real_time_loop)

if __name__ == "__main__":
    run_live_aegis()