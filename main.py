import numpy as np
from physics import RelativeDynamics
from entities import Satellite, Debris
from visualizer import DynamicDashboard
from telemetry import AegisTelemetry

def run_simulation():
    print("--- INICIANDO SIMULACIÓN ---")
    
    # --- MODULO IOT ---
    centro_control = AegisTelemetry()
    centro_control.connect()
    centro_control.wait_for_launch()  
    centro_control.disconnect()       
    # ------------------------------------
    # 1. Configuración
    altitude = 800 
    leo_physics = RelativeDynamics(altitude_km=altitude)
    
    t_min_impact = 400
    t_max_impact = 800
    dt = 5           
    total_time = t_max_impact + 4000 
    
    # Velocidades Visuales (Limitadores)
    MAX_ESCAPE_SPEED = 0.008     # 8 m/s
    RETURN_CRUISE_SPEED = 0.025  # 15 m/s 
    
    # 2. Actores
    # EL SATÉLITE SE CREA CON SU MOTOR REAL DE 40KG
    sat = Satellite(leo_physics) 
    
    # Verificación en consola al iniciar
    status = sat.propulsion.get_status()
    print(f">>> MOTOR CHECK: {status['fuel_mass']:.2f} kg de Hidrazina listos.")

    debris_swarm = []
    print(f"Generando amenazas...")
    for i in range(3):
        min_steps = int(t_min_impact / dt)
        max_steps = int(t_max_impact / dt)
        random_step = np.random.randint(min_steps, max_steps)
        my_impact_time = random_step * dt 
        d = Debris.create_collision_threat(leo_physics, my_impact_time, debris_id=i)
        debris_swarm.append(d)
        print(f" -> Debris {i}: Impacto en T={my_impact_time}s")

    print("Calculando simulación...")
    steps = int(total_time / dt)
    
    # --- BUCLE PRINCIPAL ---
    for step in range(steps):
        
        # A. Física
        sat.propagate(dt)
        sat.sensor.position = sat.position
        for debris in debris_swarm:
            debris.propagate(dt)

        # B. Lógica
        active_threats = 0       
        evasion_active = False   
        
        for debris in debris_swarm:
            measured_pos = sat.sensor.measure(debris.position)
            
            if np.linalg.norm(measured_pos) > 0:
                v_rel_estimate = debris.velocity - sat.velocity
                risk = sat.brain.calculate_risk(measured_pos, v_rel_estimate)
                
                if risk['probability'] > 0.5:
                    active_threats += 1
                    if 0 < risk['tca'] < 200:
                        evasion_active = True
                        
                        thrust_vector, _ = sat.calculate_avoidance(measured_pos, v_rel_estimate, risk['tca'])
                        
                        # Limitador de velocidad
                        mag = np.linalg.norm(thrust_vector)
                        if mag > MAX_ESCAPE_SPEED:
                            thrust_vector = thrust_vector / mag * MAX_ESCAPE_SPEED
                            
                        sat.maneuver(thrust_vector)

        # C. Retorno
        dist_to_home = np.linalg.norm(sat.position)
        
        if active_threats == 0 and dist_to_home > 0.05:
            direction_home = -sat.position / dist_to_home
            
            if dist_to_home > 0.5:
                target_speed = RETURN_CRUISE_SPEED
            else:
                target_speed = dist_to_home * 0.01 
                target_speed = max(target_speed, 0.001)
            
            desired_velocity = direction_home * target_speed
            
            delta_v = desired_velocity - sat.velocity
            delta_v = delta_v * 0.2 
            
            sat.maneuver(delta_v)
            
            if step % 50 == 0: 
                 s = sat.propulsion.get_status()
                 print(f"   [RETORNO] Dist: {dist_to_home:.2f} km | Fuel: {s['fuel_mass']:.2f} kg")

    # 4. Visualización
    print("Iniciando Dashboard...")
    dashboard = DynamicDashboard(sat, debris_swarm)
    dashboard.start_simulation()

if __name__ == "__main__":
    run_simulation()