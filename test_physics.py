import unittest
import numpy as np
from physics import RelativeDynamics

class TestPhysics(unittest.TestCase):
    def setUp(self):
        # Usamos la altura estándar de 800 km
        self.dynamics = RelativeDynamics(altitude_km=800)

    def test_identity_matrix(self):
        """Si dt=0, la matriz de transición debe ser la Identidad."""
        phi = self.dynamics.get_transition_matrix(dt=0)
        identity = np.eye(6)
        # Verificamos que la diferencia sea casi cero
        self.assertTrue(np.allclose(phi, identity, atol=1e-8))

    def test_orbital_period(self):
        """Verifica que el periodo orbital sea coherente (aprox 100 min para 800km)."""
        periodo_minutos = self.dynamics.period / 60
        self.assertAlmostEqual(periodo_minutos, 100.9, places=1)

if __name__ == '__main__':
    unittest.main()