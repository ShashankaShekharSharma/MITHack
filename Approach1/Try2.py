import numpy as np
from qiskit import Aer, QuantumCircuit, transpile, assemble, execute
from qiskit.circuit.library import QFT
from qiskit.aqua.algorithms import Shor
from math import gcd
from random import randint

def classical_shors(n):
    """Classical portion of Shor's algorithm to check for easy factors."""
    a = randint(2, n - 1)
    d = gcd(a, n)
    if d > 1:
        return d, n // d  # Trivial factor found
    return a, None

def quantum_shors(n):
    """Quantum portion of Shor's algorithm using Qiskit's built-in function."""
    backend = Aer.get_backend('qasm_simulator')
    shor = Shor(n)
    result = shor.run(backend)
    factors = result['factors']
    if factors:
        return factors[0]
    return None

def shors_algorithm(n):
    """Complete implementation of Shor's Algorithm."""
    a, factor = classical_shors(n)
    if factor:
        return factor  # Return early if a factor is found classically
    
    print(f"Chosen a: {a}, proceeding with quantum order finding...")
    factors = quantum_shors(n)
    if factors:
        return factors
    else:
        return "Quantum method failed, try another run."

# Test with small semiprimes
semiprimes = {8: 143, 10: 899, 12: 3127, 14: 11009}
for bits, n in semiprimes.items():
    print(f"Factoring {n} (a {bits}-bit semiprime)...")
    try:
        factors = shors_algorithm(n)
        print(f"Factors of {n}: {factors}")
    except Exception as e:
        print(f"Error factoring {n}: {str(e)}")
    print("-" * 50)
