import math
import random
import numpy as np
from qiskit import Aer, QuantumCircuit, transpile, assemble, execute
from qiskit.aqua.algorithms import Shor
from qiskit.aqua import QuantumInstance

def factor_semiprime(n):
    # Check if the number is a semiprime
    if not is_semiprime(n):
        raise ValueError("The number is not a semiprime.")

    # Use Shor's algorithm to factor the semiprime
    shor = Shor(N=n)
    backend = Aer.get_backend('qasm_simulator')
    quantum_instance = QuantumInstance(backend, shots=1024)
    result = shor.run(quantum_instance)
    
    factors = result['factors']
    return factors

def is_semiprime(n):
    # A semiprime is a product of exactly two primes (not necessarily distinct)
    if n < 2:
        return False
    count = 0
    for i in range(2, int(math.sqrt(n)) + 1):
        while n % i == 0:
            n = n // i
            count += 1
            if count > 2:
                return False
    if n > 1:
        count += 1
    return count == 2

# Example usage
if __name__ == "__main__":
    semiprime = 15  # Example semiprime number
    print(f"Factoring {semiprime}...")
    factors = factor_semiprime(semiprime)
    print(f"Factors of {semiprime} are: {factors}")