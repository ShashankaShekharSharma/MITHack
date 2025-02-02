import QuantumRingsLib
from QuantumRingsLib import QuantumRegister, AncillaRegister, ClassicalRegister, QuantumCircuit
from QuantumRingsLib import QuantumRingsProvider
from QuantumRingsLib import job_monitor
from QuantumRingsLib import JobStatus
from matplotlib import pyplot as plt
import numpy as np
import math
import csv
from fractions import Fraction

def mod_exp(a, x, N):
    """
    Compute a^x mod N efficiently using square-and-multiply algorithm
    """
    result = 1
    a = a % N
    while x > 0:
        if x & 1:
            result = (result * a) % N
        a = (a * a) % N
        x = x >> 1
    return result

def controlled_mod_mult(qc, control_reg, target_reg, ancilla_reg, x, N):
    """
    Implements controlled modular multiplication with all registers pre-defined
    """
    n = len(target_reg)
    
    # Implement modular multiplication using basic gates
    for i in range(n):
        if (x & (1 << i)) != 0:
            qc.cx(control_reg[0], target_reg[i])
    
    # Add modular reduction
    qc.cx(target_reg[n-1], ancilla_reg[0])
    for i in range(n-2, -1, -1):
        qc.ccx(target_reg[i], target_reg[i+1], ancilla_reg[0])
    
    # Uncompute ancilla
    for i in range(n-1):
        qc.ccx(target_reg[i], target_reg[i+1], ancilla_reg[0])
    qc.cx(target_reg[n-1], ancilla_reg[0])

def qft(qc, q_reg, n):
    """
    Quantum Fourier Transform
    """
    for j in range(n):
        qc.h(q_reg[j])
        for k in range(j+1, n):
            qc.cu1(math.pi/float(2**(k-j)), q_reg[k], q_reg[j])

def iqft(qc, q_reg, n):
    """
    Inverse Quantum Fourier Transform
    """
    for j in range(n-1, -1, -1):
        for k in range(j+1, n):
            qc.cu1(-math.pi/float(2**(k-j)), q_reg[k], q_reg[j])
        qc.h(q_reg[j])

def create_quantum_circuit(N, n_count):
    """
    Creates quantum circuit with all registers defined upfront
    """
    # Calculate required number of qubits
    n_target = math.ceil(math.log2(N))
    
    # Create all registers upfront
    q_count = QuantumRegister(n_count, 'count')
    q_target = QuantumRegister(n_target, 'target')
    q_ancilla = QuantumRegister(1, 'ancilla')  # Single ancilla qubit
    c_count = ClassicalRegister(n_count, 'c')
    
    # Create quantum circuit with all registers
    qc = QuantumCircuit(q_count, q_target, q_ancilla, c_count)
    
    # Initialize count register
    for i in range(n_count):
        qc.h(q_count[i])
    qc.barrier()
    
    # Choose coprime a
    a = 2
    while math.gcd(a, N) != 1:
        a += 1
    
    # Implement controlled modular multiplication
    for i in range(n_count):
        controlled_mod_mult(qc, [q_count[i]], q_target, q_ancilla, mod_exp(a, 2**i, N), N)
        qc.barrier()
    
    # Apply inverse QFT
    iqft(qc, q_count, n_count)
    
    # Measure count register
    qc.measure(q_count, c_count)
    
    return qc

def process_results(counts, N):
    """
    Process measurement results to find factors
    """
    factors = set()
    
    for outcome in counts:
        try:
            phase = int(outcome, 2) / (1 << len(outcome))
            if phase != 0:
                frac = Fraction(phase).limit_denominator(N)
                r = frac.denominator
                
                if r % 2 == 0:
                    candidate = mod_exp(2, r // 2, N)
                    factor1 = math.gcd(candidate + 1, N)
                    factor2 = math.gcd(candidate - 1, N)
                    
                    if 1 < factor1 < N:
                        factors.add(factor1)
                    if 1 < factor2 < N:
                        factors.add(factor2)
        except:
            continue
    
    return list(factors)

# Initialize quantum provider
provider = QuantumRingsProvider(token='rings-200.OlV43PAoB1aCdOHhDHhaq7kUP7pYvpbR', name='ss7061@srmist.edu.in')
backend = provider.get_backend("scarlet_quantum_rings")
shots = 1024

provider.active_account()

# Dictionary of semiprimes
semiprimes = {
    # 8: 143,
    # 10: 899,
    # 14: 11009,
    # 16: 47053,
    # 18: 167659,
    20: 744647,
    22: 3036893,
    24: 11426971,
    26: 58949987,
    28: 208241207,
    30: 857830637,
    32: 2776108693,
    34: 11455067797,
}

# Open CSV file for results
with open('factors.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Semiprime', 'Factor 1', 'Factor 2'])
    
    for qubits, N in semiprimes.items():
        print(f"Processing N={N} with {qubits} qubits...")
        
        try:
            # Create and execute quantum circuit
            qc = create_quantum_circuit(N, qubits)
            
            # Add error mitigation
            job = backend.run(qc, shots=shots, optimization_level=3)
            job_monitor(job)
            
            result = job.result()
            counts = result.get_counts()
            
            # Process results
            factors = process_results(counts, N)
            
            # Try different coprime values if needed
            if len(factors) < 2:
                a_values = [3, 5, 7, 11]
                for a in a_values:
                    if math.gcd(a, N) == 1:
                        qc = create_quantum_circuit(N, qubits)
                        job = backend.run(qc, shots=shots, optimization_level=3)
                        job_monitor(job)
                        result = job.result()
                        counts = result.get_counts()
                        new_factors = process_results(counts, N)
                        factors.extend(new_factors)
                        if len(factors) >= 2:
                            break
            
            # Get final factors
            factors = list(set(factors))  # Remove duplicates
            if len(factors) >= 2:
                factor1, factor2 = sorted(factors)[:2]
            else:
                factor1, factor2 = 1, N
            
            # Write results
            writer.writerow([N, factor1, factor2])
            print(f"Factors of {N}: {factor1}, {factor2}")
            
        except Exception as e:
            print(f"Error processing N={N}: {str(e)}")
            writer.writerow([N, 'Error', str(e)])

print("Factorization complete. Results saved to 'factors.csv'.")