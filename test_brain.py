import unittest
import numpy as np
from brain import AegisBrain

class TestBrain(unittest.TestCase):
    def setUp(self):
        self.brain = AegisBrain(sigma=10.0) # Incertidumbre de 10m

    def test_certain_collision(self):
        """Si la distancia de fallo es 0, la probabilidad debe ser 100%."""
        r_rel = np.array([0.0, 0.0, 0.0])
        v_rel = np.array([0.0, 0.0, 1.0])
        risk = self.brain.calculate_risk(r_rel, v_rel)
        
        self.assertEqual(risk['probability'], 1.0)

    def test_tca_calculation(self):
        """Verifica que el tiempo de impacto sea correcto para un choque frontal."""
        # Objeto a 10km viniendo a 1km/s -> TCA debe ser 10s
        r_rel = np.array([10.0, 0.0, 0.0])
        v_rel = np.array([-1.0, 0.0, 0.0])
        risk = self.brain.calculate_risk(r_rel, v_rel)
        
        self.assertAlmostEqual(risk['tca'], 10.0)

if __name__ == '__main__':
    unittest.main()