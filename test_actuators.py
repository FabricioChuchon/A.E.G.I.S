import unittest
import numpy as np
from actuators import PropulsionSystem

class TestActuators(unittest.TestCase):
    def setUp(self):
        # Iniciamos con el tanque real de 150 kg
        self.propulsion = PropulsionSystem(initial_fuel_mass=150.0, dry_mass=180.0)

    def test_fuel_consumption(self):
        """Verifica que una maniobra reduzca el combustible."""
        initial_fuel = self.propulsion.fuel_mass
        thrust = np.array([0.01, 0.0, 0.0]) # Maniobra de 10 m/s
        self.propulsion.execute_burn(thrust)
        
        self.assertLess(self.propulsion.fuel_mass, initial_fuel)

    def test_percentage_accuracy(self):
        """Verifica que el porcentaje se calcule sobre 150kg y no sobre 40kg."""
        status = self.propulsion.get_status()
        # Al inicio (150/150) debe ser 100%
        self.assertEqual(status['percent'], 100.0)

if __name__ == '__main__':
    unittest.main()