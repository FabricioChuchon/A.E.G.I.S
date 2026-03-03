import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.gridspec import GridSpec
from telemetry import AegisTelemetry

class DynamicDashboard:
    def __init__(self, satellite, debris_list):
        self.sat = satellite
        self.debris_list = debris_list
        self.sensor = self.sat.sensor
        
        self.sensor_range = getattr(self.sensor, 'detection_range', 50.0) 
        self.collision_dist = 2.5   
        self.dt_simulation = 5.0    
        self.radar_max_range = 50.0 
        
        
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(16, 8))
        self.fig.tight_layout()
        self.fig.suptitle("MONITOR DE INTEGRIDAD A.E.G.I.S. (VISUALIZACIÓN VOLUMÉTRICA)", fontsize=16, color='white')
        
        gs = GridSpec(1, 2, figure=self.fig)

        # 1. RADAR 3D
        self.ax_3d = self.fig.add_subplot(gs[0, 0], projection='3d')
        self.ax_3d.set_facecolor('black') 
        
        l = 40 
        self.ax_3d.set_xlim(-l, l); self.ax_3d.set_ylim(-l, l); self.ax_3d.set_zlim(-l, l)
        self.ax_3d.view_init(elev=25, azim=-45) 
        self.ax_3d.set_box_aspect((1, 1, 1))
        self.ax_3d.dist = 8 
        
        self.ax_3d.xaxis.pane.fill = False
        self.ax_3d.yaxis.pane.fill = False
        self.ax_3d.zaxis.pane.fill = False

        # 2. RADAR PPI
        self.ax_radar = self.fig.add_subplot(gs[0, 1], projection='polar')
        self.ax_radar.set_title("SENSOR PPI", color='lime', pad=20)
        self.ax_radar.set_facecolor('black')
        self.ax_radar.set_theta_zero_location("N"); self.ax_radar.set_theta_direction(-1)      
        self.ax_radar.grid(True, color='#004400', linestyle='-', linewidth=0.8) 
        self.ax_radar.set_ylim(0, self.radar_max_range)
        self.ax_radar.set_yticklabels([]) 
        self.ax_radar.tick_params(axis='x', colors='#008800')

        self.hud_text = self.ax_3d.text2D(0.05, 0.95, "SYSTEM STANDBY", transform=self.ax_3d.transAxes, 
                                          color='lime', fontsize=10, family='monospace',
                                          bbox=dict(facecolor='black', alpha=0.7, edgecolor='lime'))
        is_connected = getattr(self.sensor, 'connected', True)

        if not is_connected:
            # Texto gigante en el centro de la pantalla
            self.ax_3d.text2D(0.5, 0.5, "⚠️ HARDWARE NO DETECTADO\nREVISA EL PUERTO USB (COM8)", 
                              transform=self.ax_3d.transAxes, 
                              color='red', fontsize=22, ha='center', va='center', weight='bold',
                              bbox=dict(facecolor='black', alpha=0.9, edgecolor='red', boxstyle='round,pad=1'))
            
            # Cambiamos el HUD pequeño de arriba a estado de error
            self.hud_text.set_text("SYSTEM ERROR\nNO SENSOR DATA")
            self.hud_text.set_color('red')
            self.hud_text.set_bbox(dict(facecolor='black', alpha=0.7, edgecolor='red'))


        # Elementos Gráficos
        self.sat_sphere_artist = None 
        self.sat_trail, = self.ax_3d.plot([], [], [], '-', color='lime', linewidth=1, alpha=0.5)
        self._draw_wire_sphere(self.ax_3d, [0,0,0], self.sensor_range, 'green', 0.03) 
        self.ghost_line, = self.ax_3d.plot([], [], [], '--', color='cyan', linewidth=2.0, alpha=0.9, label='Solución Guiado')

        self.proxies = []
        for i in range(len(debris_list)):
            l3, = self.ax_3d.plot([], [], [], '-', color='red', linewidth=0.5, alpha=0.5)
            p_radar, = self.ax_radar.plot([], [], 'o', color='#00FF00', markersize=6, alpha=0.8, markeredgecolor='white')
            p3_sensor, = self.ax_3d.plot([], [], [], 'x', color='white', markersize=4, alpha=0.6)
            
            self.proxies.append({
                'sphere_artist': None,
                'l3': l3, 'p_radar': p_radar, 'p3_sensor': p3_sensor, 
                'detected': False
            })

        self.telemetry = AegisTelemetry()
        self.telemetry.connect()
        self.telemetry_counter = 0 

    def _draw_wire_sphere(self, ax, pos, r, color, alpha):
        u, v = np.mgrid[0:2*np.pi:12j, 0:np.pi:12j]
        x = r * np.cos(u) * np.sin(v) + pos[0]
        y = r * np.sin(u) * np.sin(v) + pos[1]
        z = r * np.cos(v) + pos[2]
        return ax.plot_wireframe(x, y, z, color=color, alpha=alpha, linewidth=0.8)

    def _trigger_game_over(self, debris_idx, distance):
        if hasattr(self, 'anim') and self.anim:
            self.anim.event_source.stop() 
        print(f"\n!!! IMPACTO !!! Objeto {debris_idx} a {distance*1000:.1f} metros.")
        self.ax_3d.text(0, 0, 10, "¡IMPACTO FATAL!", color='red', fontsize=25, ha='center', weight='bold', backgroundcolor='black')
        self.hud_text.set_text("CRITICAL FAILURE\nCOLLISION DETECTED"); self.hud_text.set_color('red')

    def _update_hud(self, distance, risk_data, threat_count, thrust_vector, current_fuel, speed_ms, current_action):
        tca = risk_data['tca']
        prob = risk_data['probability']
        
        fuel_kg = current_fuel
        fuel_pct = (fuel_kg / 150.0) * 100 
        
        status = "TRACKING"
        color = "lime"
        
        if prob > 0.3 or distance < 20.0: status, color = "WARNING", "yellow"
        if prob > 0.8 or distance < 5.0: status, color = "CRITICAL", "red"
        if fuel_kg < 1.0: status, color = "LOW FUEL", "orange"
            
        time_msg = f"T-{tca:.0f}s" if tca > 0 else "SAFE"
        maneuver_msg = "ENGINES: IDLE"
        if thrust_vector is not None and np.linalg.norm(thrust_vector) > 0:
            dv = np.linalg.norm(thrust_vector) * 1000 
            maneuver_msg = f"BURN: {dv:.1f} m/s"

        hud_content = (
            f"SYSTEM:  [{status}]\n"
            f"ACTION:  {current_action}\n"
            f"SPEED:   {speed_ms:.1f} m/s\n"
            f"RANGE:   {distance:.2f} km\n"
            f"FUEL:    {fuel_kg:.1f} kg ({fuel_pct:.0f}%)\n"
            f"IMPACT:  {time_msg}\n"
            f"THREATS: {threat_count}"
        )
        self.hud_text.set_text(hud_content)
        self.hud_text.set_color(color)
        self.hud_text.set_bbox(dict(facecolor='black', alpha=0.7, edgecolor=color))

        self.telemetry_counter += 1
        if self.telemetry_counter % 5 == 0:
            self.telemetry.send_fuel(current_fuel)
            self.telemetry.send_status(status) 
            self.telemetry.send_threats(threat_count)
            self.telemetry.send_speed(speed_ms)
            self.telemetry.send_action(current_action)

    def update(self, frame):
        closest_dist = 999.0
        active_threats = 0
        highest_risk_data = {"tca": -1, "probability": 0}
        current_thrust = None
        best_ghost_path = None

        if frame < len(self.sat.history): safe_frame = frame
        else: safe_frame = len(self.sat.history) - 1
            
        sat_state = self.sat.history[safe_frame]
        sat_pos = sat_state[:3]
        
        sat_vel = sat_state[3:]
        speed_ms = np.linalg.norm(sat_vel) * 1000 
        dist_to_home = np.linalg.norm(sat_pos)
        
        fuel_idx = min(frame, len(self.sat.fuel_history) - 1)
        current_fuel = self.sat.fuel_history[fuel_idx]

        if self.sat_sphere_artist: self.sat_sphere_artist.remove()
        self.sat_sphere_artist = self._draw_wire_sphere(self.ax_3d, sat_pos, 0.8, 'cyan', 0.8)
        
        start_trail = max(0, frame - 50)
        hist_arr = np.array(self.sat.history)
        self.sat_trail.set_data(hist_arr[start_trail:safe_frame, 0], hist_arr[start_trail:safe_frame, 1])
        self.sat_trail.set_3d_properties(hist_arr[start_trail:safe_frame, 2])

        for i, debris in enumerate(self.debris_list):
            hist = np.array(debris.history)
            if frame >= len(hist): continue
            
            debris_state = hist[frame]
            debris_pos = debris_state[:3]
            vel_debris = debris_state[3:]
            
            dist_real_a_mi = np.linalg.norm(debris_pos - sat_pos)
            
            if dist_real_a_mi < self.collision_dist:
                self.ax_3d.scatter(sat_pos[0], sat_pos[1], sat_pos[2], s=1000, c='orange', marker='*', zorder=200)
                self._trigger_game_over(i, dist_real_a_mi)
                return []
            
            proxy = self.proxies[i]
            
            # --- OBJECT POOLING BYPASS ---
            if np.linalg.norm(debris_pos) > 1000.0:
                if proxy['sphere_artist']: 
                    proxy['sphere_artist'].remove()
                    proxy['sphere_artist'] = None
                continue 

            if proxy['sphere_artist']: proxy['sphere_artist'].remove()
            proxy['sphere_artist'] = self._draw_wire_sphere(self.ax_3d, debris_pos, self.collision_dist, 'red', 0.6)
            
            measured_rel = debris_pos - sat_pos
            has_fix = np.linalg.norm(debris_pos) < 5000.0

            dist_sensor = np.linalg.norm(measured_rel) if has_fix else 999.0
            measured_abs = sat_pos + measured_rel if has_fix else None

            if has_fix and dist_sensor > 0 and dist_sensor < self.sensor_range:
                proxy['detected'] = True
                active_threats += 1
                v_rel = vel_debris - sat_state[3:] 
                risk = self.sat.brain.calculate_risk(measured_rel, v_rel)
                
                if risk['probability'] > 0.3 and risk['tca'] > 0:
                    thrust, ghost_path = self.sat.calculate_avoidance(measured_rel, v_rel, risk['tca'])
                    if risk['probability'] > highest_risk_data['probability']:
                        highest_risk_data = risk
                        closest_dist = dist_sensor
                        current_thrust = thrust
                        best_ghost_path = ghost_path 
                elif risk['probability'] > highest_risk_data['probability']:
                     highest_risk_data = risk
                     closest_dist = dist_sensor

            if proxy['detected']:
                start = max(0, frame - 40)
                proxy['l3'].set_data(hist[start:frame, 0], hist[start:frame, 1])
                proxy['l3'].set_3d_properties(hist[start:frame, 2])
                proxy['p3_sensor'].set_data([measured_abs[0]], [measured_abs[1]])
                proxy['p3_sensor'].set_3d_properties([measured_abs[2]])
                
                # Radar PPI Limpio
                r_polar = dist_sensor
                theta_polar = np.arctan2(measured_rel[0], measured_rel[1]) 
                if r_polar < self.radar_max_range: 
                    proxy['p_radar'].set_data([theta_polar], [r_polar])
                else: 
                    proxy['p_radar'].set_data([], [])

        if best_ghost_path is not None:
            absolute_ghost_path = best_ghost_path + sat_pos 
            self.ghost_line.set_data(absolute_ghost_path[:, 0], absolute_ghost_path[:, 1])
            self.ghost_line.set_3d_properties(absolute_ghost_path[:, 2])
        else:
            self.ghost_line.set_data([], [])
            self.ghost_line.set_3d_properties([])

        if speed_ms == 0.0: current_action = "EN POSICIÓN ✅"
        elif speed_ms <= 40.0:
            if dist_to_home > 0.05: current_action = "RETORNANDO 🏠"
            else: current_action = "EN POSICIÓN ✅"
        else: current_action = "EVADIENDO ⚠️"

        self._update_hud(closest_dist, highest_risk_data, active_threats, current_thrust, current_fuel, speed_ms, current_action)
        return [self.sat_trail, self.ghost_line]

    
    def start_simulation(self, live_func=None):
        """Inicia el dashboard adaptándose dinámicamente al modo elegido en el menú."""
        print("Radar Activo. Renderizando entorno...")
        
        if live_func is not None:
            # MODO 2: LIVE (Arduino HIL) -> Bucle Infinito
            self.anim = FuncAnimation(self.fig, live_func, frames=None, interval=80, blit=False, repeat=True)
        else:
            # MODO 1: SIMULACIÓN PURA -> Bucle Finito (Termina cuando acaban los datos)
            total_frames = len(self.sat.history)
            self.anim = FuncAnimation(self.fig, self.update, frames=total_frames, interval=80, blit=False, repeat=False)
            
        plt.show()
