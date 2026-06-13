import unittest
import math
from main import calculate_pi_to_5th_digit


class TestPiCalculation(unittest.TestCase):
    """Test cases for the pi calculation function."""
    
    def test_pi_value(self):
        """Test that calculated pi matches expected value to 5 decimal places."""
        calculated_pi = calculate_pi_to_5th_digit()
        expected_pi = 3.14159
        self.assertEqual(calculated_pi, expected_pi)
    
    def test_pi_accuracy(self):
        """Test that calculated pi is close to math.pi."""
        calculated_pi = calculate_pi_to_5th_digit()
        # Check that the difference is less than 0.00001 (5th decimal place)
        self.assertAlmostEqual(calculated_pi, math.pi, places=5)
    
    def test_pi_type(self):
        """Test that the function returns a float."""
        calculated_pi = calculate_pi_to_5th_digit()
        self.assertIsInstance(calculated_pi, float)
    
    def test_pi_range(self):
        """Test that pi is in the expected range."""
        calculated_pi = calculate_pi_to_5th_digit()
        self.assertGreater(calculated_pi, 3.14)
        self.assertLess(calculated_pi, 3.15)
    
    def test_pi_string_representation(self):
        """Test the string representation of pi to 5 digits."""
        calculated_pi = calculate_pi_to_5th_digit()
        pi_str = str(calculated_pi)
        # Should be "3.14159"
        self.assertTrue(pi_str.startswith("3.14159"))


if __name__ == '__main__':
    unittest.main()
