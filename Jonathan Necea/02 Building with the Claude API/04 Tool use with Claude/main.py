def greeting():
    print("Hi there")


def calculate_pi_to_5th_digit():
    """
    Calculate pi to the 5th decimal digit (3.14159).
    Uses the Machin formula for better convergence.
    
    Machin's formula: pi/4 = 4*arctan(1/5) - arctan(1/239)
    
    Returns:
        float: Pi calculated to at least 5 decimal places
    """
    def arctan(x, num_terms=50):
        """
        Calculate arctan(x) using Taylor series expansion.
        arctan(x) = x - x^3/3 + x^5/5 - x^7/7 + ...
        """
        result = 0
        x_squared = x * x
        numerator = x
        
        for n in range(num_terms):
            denominator = 2 * n + 1
            if n % 2 == 0:
                result += numerator / denominator
            else:
                result -= numerator / denominator
            numerator *= x_squared
        
        return result
    
    # Machin's formula: pi/4 = 4*arctan(1/5) - arctan(1/239)
    pi = 4 * (4 * arctan(1/5, 100) - arctan(1/239, 100))
    
    # Round to 5 decimal places
    return round(pi, 5)