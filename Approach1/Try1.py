import numpy as np
from qiskit import Aer, QuantumCircuit, transpile, assemble, execute
from qiskit.circuit.library import QFT
from qiskit.tools.visualization import plot_histogram
from math import gcd
from random import randint

# Function to find the greatest common divisor (gcd)
def gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return a

# Function to find the modular inverse
def modular_inverse(a, m):
    def extended_gcd(a, b):
        if b == 0:
            return a, 1, 0
        else:
            g, x, y = extended_gcd(b, a % b)
            return g, y, x - (a // b) * y

    g, x, _ = extended_gcd(a, m)
    if g != 1:
        return None  # Modular inverse doesn't exist
    else:
        return x % m

# Function to implement the quantum part of Shor's algorithm
def quantum_order_finding(a, n):
    # Number of qubits required
    n_qubits = n.bit_length()

    # Create a quantum circuit
    qc = QuantumCircuit(2 * n_qubits, n_qubits)

    # Apply Hadamard gates to the first n_qubits
    qc.h(range(n_qubits))

    # Apply modular exponentiation (a^x mod n)
    # This is a placeholder; a full implementation requires a detailed circuit
    qc.append(QFT(n_qubits, do_swaps=False).inverse(), range(n_qubits))

    # Measure the first n_qubits
    qc.measure(range(n_qubits), range(n_qubits))

    # Simulate the circuit
    backend = Aer.get_backend('qasm_simulator')
    compiled_circuit = transpile(qc, backend)
    qobj = assemble(compiled_circuit)
    result = execute(qc, backend, shots=1024).result()

    # Extract the measurement result
    counts = result.get_counts(qc)
    measured_value = max(counts, key=counts.get)
    r = int(measured_value, 2)

    return r

# Function to implement Shor's algorithm
def shors_algorithm(n):
    # Step 1: Choose a random number a < n
    a = randint(2, n - 1)
    print(f"Chosen random number a: {a}")

    # Step 2: Compute the greatest common divisor (gcd) of a and n
    common_divisor = gcd(a, n)
    if common_divisor != 1:
        return common_divisor, n // common_divisor

    # Step 3: Find the order r of a modulo n
    r = quantum_order_finding(a, n)
    print(f"Found order r: {r}")

    # Step 4: Check if r is even and a^(r/2) != -1 mod n
    if r % 2 == 0 and pow(a, r // 2, n) != n - 1:
        factor1 = gcd(pow(a, r // 2, n) - 1, n)
        factor2 = gcd(pow(a, r // 2, n) + 1, n)
        return factor1, factor2
    else:
        return None

# Sample list of semiprimes
semiprimes = {
    8: 143,
    10: 899,
    12: 3127,
    14: 11009,
    16: 47053,
    18: 167659,
    20: 744647,
    22: 3036893,
    24: 11426971,
    26: 58949987,
    28: 208241207,
    30: 857830637,
    32: 2776108693,
    34: 11455067797,
    36: 52734393667,
    38: 171913873883,
    40: 862463409547
}

# Test Shor's algorithm on the sample semiprimes
for bits, n in semiprimes.items():
    print(f"Factoring {n} (a {bits}-bit semiprime)...")
    try:
        factors = shors_algorithm(n)
        if factors:
            print(f"Factors of {n}: {factors}")
        else:
            print(f"Failed to find factors for {n}")
    except Exception as e:
        print(f"Error factoring {n}: {str(e)}")
    print("-" * 50)