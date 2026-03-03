import numpy as np

class PropulsionSystem:
    def __init__(self, initial_fuel_mass=40.0, dry_mass=180.0, isp=230.0):
        
        self.fuel_mass = float(initial_fuel_mass)
        self.dry_mass = float(dry_mass)
        self.isp = float(isp)
        self.gravity = 9.80665 
        self.capacity = float(initial_fuel_mass)
        self.fuel_depleted = False 
        total_mass = self.dry_mass + self.fuel_mass
        if self.fuel_mass > 0:
            self.total_delta_v_capacity = self.isp * self.gravity * np.log(total_mass / self.dry_mass)
        else:
            self.total_delta_v_capacity = 0

    def execute_burn(self, thrust_vector):
        req_dv = np.linalg.norm(thrust_vector) # km/s
        req_dv_ms = req_dv * 1000.0            # m/s
        
        if req_dv_ms < 0.001: 
            return np.zeros(3)
        
        # Cálculo Físico (Tsiolkovsky)
        
        current_total_mass = self.dry_mass + self.fuel_mass
        mass_ratio = np.exp(req_dv_ms / (self.isp * self.gravity))
        final_total_mass = current_total_mass / mass_ratio
        real_fuel_needed = current_total_mass - final_total_mass
        fuel_to_burn = real_fuel_needed * 0.20 
        
        # Actualizar Tanque
        if self.fuel_mass > 0:
            self.fuel_mass -= fuel_to_burn
        
        if self.fuel_mass <= 0:
            self.fuel_mass = 0.0
            self.fuel_depleted = True

        return thrust_vector

    def get_status(self):
        pct = (self.fuel_mass / self.capacity) * 100 if self.capacity > 0 else 0.0
        return {
            "fuel_mass": self.fuel_mass,
            "total_mass": self.dry_mass + self.fuel_mass,
            "percent": pct,
            "depleted": self.fuel_depleted
        }

    
