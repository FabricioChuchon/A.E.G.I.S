import numpy as np
import time
from physics import RelativeDynamics
from entities import Satellite, Debris
from telemetry import AegisTelemetry

class MonteCarloValidator:
    
    def __init__(self, iterations=100, altitude_km=800):
        # 1. Parámetros Principales
        self.iterations = iterations
        self.altitude = altitude_km
        self.leo_physics = RelativeDynamics(altitude_km=self.altitude) 
        # 2. Constantes de la Simulación Física
        self.t_min_impact = 400
        self.t_max_impact = 800
        self.dt = 5           
        self.total_time = self.t_max_impact + 4000 
        self.max_escape_speed = 0.008     
        self.return_cruise_speed = 0.015  
        self.collision_radius = 2.5 
        # 3. Métricas de Rendimiento
        self.success_count = 0
        self.total_fuel = 0.0
        self.total_evasions = 0
        # 4. Módulo de Telecomunicaciones
        self.centro_control = AegisTelemetry()

    def _run_single_mission(self):
        """Ejecuta una sola misión simulada de principio a fin"""
        sat = Satellite(self.leo_physics) 
        debris_swarm = []
        # --- CAOS 1: LLUVIA DE BASURA EXTREMA ---
        num_threats = np.random.randint(15, 30)
        for j in range(num_threats):
            random_step = np.random.randint(int(self.t_min_impact / self.dt), int(self.t_max_impact / self.dt))
            my_impact_time = random_step * self.dt 
            d = Debris.create_collision_threat(self.leo_physics, my_impact_time, debris_id=j)
            debris_swarm.append(d)

        steps = int(self.total_time / self.dt)
        evasions_count = 0
        survived = True

        for step in range(steps):
            sat.propagate(self.dt)
            sat.sensor.position = sat.position
            for debris in debris_swarm:
                debris.propagate(self.dt)

            # Verificación de Fallos
            for debris in debris_swarm:
                if np.linalg.norm(debris.position - sat.position) < self.collision_radius:
                    survived = False
                    break 
            if not survived:
                break

            active_threats = 0       
            for debris in debris_swarm:
                # --- CAOS 2: PUNTO CIEGO DEL RADAR (15% de fallo) ---
                if np.random.rand() < 0.15:
                    continue # El sensor parpadeó y "perdió" el paquete de datos este segundo
                
                measured_pos = sat.sensor.measure(debris.position)
                if np.linalg.norm(measured_pos) > 0:
                    v_rel_estimate = debris.velocity - sat.velocity
                    risk = sat.brain.calculate_risk(measured_pos, v_rel_estimate)
                    
                    if risk['probability'] > 0.5:
                        active_threats += 1
                        # --- CAOS 3: REACCIÓN TARDÍA (TCA < 100s en vez de 200s) ---
                        if 0 < risk['tca'] < 100: 
                            thrust_vector, _ = sat.calculate_avoidance(measured_pos, v_rel_estimate, risk['tca'])
                            mag = np.linalg.norm(thrust_vector)
                            if mag > self.max_escape_speed:
                                thrust_vector = thrust_vector / mag * self.max_escape_speed
                            # --- CAOS 4: FALLA CRÍTICA DE MOTOR (Pierde fuerza y apunta mal) ---
                            eficiencia_mecanica = np.random.uniform(0.50, 0.90) # Rinde entre 50% y 90%
                            ruido_direccional = np.random.normal(0, 0.002, 3)   # El cohete vibra y se desvía
                            
                            thrust_vector = (thrust_vector * eficiencia_mecanica) + ruido_direccional
                            
                            sat.maneuver(thrust_vector)
                            evasions_count += 1

            dist_to_home = np.linalg.norm(sat.position)
            if active_threats == 0 and dist_to_home > 0.05:
                direction_home = -sat.position / dist_to_home
                target_speed = self.return_cruise_speed if dist_to_home > 0.5 else max(dist_to_home * 0.01, 0.001)
                desired_velocity = direction_home * target_speed
                delta_v = (desired_velocity - sat.velocity) * 0.2 
                sat.maneuver(delta_v)
                
        return survived, sat.propulsion.fuel_mass, evasions_count

    def _generate_report(self):
        """Calcula estadísticas y envía el reporte final a consola e IoT"""
        survival_rate = (self.success_count / self.iterations) * 100
        avg_fuel = round(self.total_fuel / self.iterations, 2)
        print("\n=================================")
        print(" 📊 REPORTE FINAL")
        print("=================================")
        print(f"Misiones exitosas     : {self.success_count}/{self.iterations}")
        print(f"Tasa de Supervivencia : {survival_rate}%")
        print(f"Combustible Promedio  : {avg_fuel} kg restantes")
        print(f"Maniobras Totales     : {self.total_evasions}")
        print("=================================\n")
        
        # Telemetría final al celular
        self.centro_control.send_status(f"VALIDADO: {survival_rate}% ÉXITO ✅")
        self.centro_control.send_fuel(avg_fuel)
        self.centro_control.send_action("MONTE CARLO FINALIZADO")
        self.centro_control.send_speed(0.0)
        
        try:
            self.centro_control.send_montecarlo_report(survival_rate, avg_fuel, self.total_evasions)
        except Exception as e:
            print(f"(Aviso: Widget de reporte JSON no recibido: {e})")

    def execute(self):
        """Método principal que orquesta toda la validación"""
        print(r"""
           ___   ______  _______ .________. ___  _______
          /   \ |   ___||     __||  ___   ||   ||   ____|
         /  ^  \|  |__  |  |__   | |   |__||   ||  |____
        /  /_\  \   __| |   __|  | |  ____ |   ||____   |
       /  _____  \  |___|  |____ | | |__  ||   | ____|  |
      /__/     \__\_____|_______||________||___||_______|
        """)
        print("--- INICIANDO SIMULACIONES (MONTE CARLO) ---")
        
        # Conexión IoT y espera del gatillo
        self.centro_control.connect()
        self.centro_control.wait_for_launch()
        print(f"\n[MONTE CARLO] Ejecutando {self.iterations} simulaciones a máxima velocidad...")
        self.centro_control.send_status(f"EJECUTANDO MONTE CARLO ({self.iterations}x)")
        
        # Bucle de validación masiva
        for i in range(self.iterations):
            survived, fuel_left, evasions = self._run_single_mission()
            
            if survived:
                self.success_count += 1
            self.total_fuel += fuel_left
            self.total_evasions += evasions
            
            # Telemetría de progreso (cada 10%)
            if (i + 1) % 10 == 0:
                print(f" -> Progreso: {i + 1} / {self.iterations} misiones completadas")
                self.centro_control.send_status(f"PROCESANDO... {i + 1}/{self.iterations}")
                self.centro_control.send_fuel((self.total_fuel / (i + 1)))

        # Finalizar
        self._generate_report()
        time.sleep(2)
        self.centro_control.disconnect()


if __name__ == "__main__":
    # Instanciamos el validador
    validador = MonteCarloValidator(iterations=100, altitude_km=800)
    validador.execute()