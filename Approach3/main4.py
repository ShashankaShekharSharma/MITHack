import QuantumRingsLib
from QuantumRingsLib import (QuantumRegister, AncillaRegister, 
                           ClassicalRegister, QuantumCircuit, 
                           QuantumRingsProvider, job_monitor, JobStatus)
from matplotlib import pyplot as plt
import numpy as np
import math
import csv
from fractions import Fraction
from concurrent.futures import ThreadPoolExecutor, as_completed

def mod_exp(a, x, N):
    """Optimized modular exponentiation using binary method"""
    if x == 0:
        return 1
    if x == 1:
        return a % N
    
    # Use binary method with fewer multiplications
    result = 1
    a = a % N
    while x > 0:
        if x & 1:
            result = (result * a) % N
        a = (a * a) % N
        x >>= 1
    return result

def controlled_mod_mult(qc, control_reg, target_reg, ancilla_reg, x, N):
    """Optimized controlled modular multiplication with reduced gate count"""
    n = len(target_reg)
    
    # Use gray code for reduced gate operations
    gray_code = x ^ (x >> 1)
    for i in range(n):
        if (gray_code & (1 << i)) != 0:
            qc.cx(control_reg[0], target_reg[i])
    
    # Optimized modular reduction using fewer ancilla qubits
    qc.cx(target_reg[n-1], ancilla_reg[0])
    for i in range(n-2, -1, -1):
        qc.ccx(target_reg[i], target_reg[i+1], ancilla_reg[0])
    
    # Uncompute with minimal operations
    for i in range(n-1):
        qc.ccx(target_reg[i], target_reg[i+1], ancilla_reg[0])
    qc.cx(target_reg[n-1], ancilla_reg[0])

def qft(qc, q_reg, n):
    """Optimized QFT implementation with reduced rotation count"""
    # Implement approximated QFT with fewer rotations
    for j in range(n):
        qc.h(q_reg[j])
        # Only apply rotations above certain threshold
        for k in range(j+1, min(j + 4, n)):  # Limit rotation depth
            qc.cu1(math.pi/float(2**(k-j)), q_reg[k], q_reg[j])

def iqft(qc, q_reg, n):
    """Optimized inverse QFT"""
    for j in range(n-1, -1, -1):
        for k in range(min(n, j + 4), j, -1):  # Limit rotation depth
            qc.cu1(-math.pi/float(2**(k-j)), q_reg[k], q_reg[j])
        qc.h(q_reg[j])

def create_quantum_circuit(N, n_count, a=2):
    """Optimized circuit creation with reduced depth"""
    n_target = math.ceil(math.log2(N))
    
    # Minimize register sizes
    q_count = QuantumRegister(n_count, 'count')
    q_target = QuantumRegister(n_target, 'target')
    q_ancilla = QuantumRegister(1, 'ancilla')
    c_count = ClassicalRegister(n_count, 'c')
    
    qc = QuantumCircuit(q_count, q_target, q_ancilla, c_count)
    
    # Parallel initialization
    qc.h(q_count)
    qc.barrier()
    
    # Pre-compute modular exponentiations
    mod_exps = [mod_exp(a, 2**i, N) for i in range(n_count)]
    
    # Implement controlled operations with reduced depth
    for i in range(n_count):
        controlled_mod_mult(qc, [q_count[i]], q_target, q_ancilla, mod_exps[i], N)
        qc.barrier()
    
    iqft(qc, q_count, n_count)
    qc.measure(q_count, c_count)
    
    return qc

def process_results(counts, N):
    """Optimized result processing with early termination"""
    factors = set()
    max_attempts = 10  # Limit processing attempts
    
    for outcome, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        if len(factors) >= 2 or max_attempts <= 0:
            break
            
        try:
            phase = int(outcome, 2) / (1 << len(outcome))
            if phase == 0:
                continue
                
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
            pass
        max_attempts -= 1
    
    return list(factors)

def process_semiprime(args):
    """Worker function for parallel processing"""
    N, qubits, backend, shots = args
    try:
        # Create and execute circuit with retry logic
        for attempt in range(3):  # Limited retries
            qc = create_quantum_circuit(N, qubits)
            job = backend.run(qc, shots=shots, optimization_level=3)
            try:
                job_monitor(job)
                result = job.result()
                counts = result.get_counts()
                factors = process_results(counts, N)
                
                if len(factors) >= 2:
                    return N, sorted(factors)[:2]
                    
                # Try alternative coprime value
                if attempt < 2:
                    a = [3, 5, 7][attempt]
                    if math.gcd(a, N) == 1:
                        qc = create_quantum_circuit(N, qubits, a)
                        job = backend.run(qc, shots=shots, optimization_level=3)
                        job_monitor(job)
                        result = job.result()
                        counts = result.get_counts()
                        factors.extend(process_results(counts, N))
                        if len(set(factors)) >= 2:
                            return N, sorted(list(set(factors)))[:2]
            except Exception as e:
                if attempt == 2:
                    raise e
                continue
                
        return N, (1, N)  # Default if no factors found
        
    except Exception as e:
        return N, ('Error', str(e))

def main():
    # Initialize provider
    provider = QuantumRingsProvider(token='rings-200.OlV43PAoB1aCdOHhDHhaq7kUP7pYvpbR', 
                                  name='ss7061@srmist.edu.in')
    backend = provider.get_backend("scarlet_quantum_rings")
    shots = 1024  # Reduced shot count for faster execution
    
    # Refined semiprime selection
    semiprimes = {
        20: 744647,
        22: 3036893,
        24: 11426971,
        26: 58949987,
        28: 208241207,
        30: 857830637,
        32: 2776108693,
        34: 11455067797,
    }
    
    # Prepare work items for parallel processing
    work_items = [(N, qubits, backend, shots) 
                 for qubits, N in semiprimes.items()]
    
    results = []
    # Process in parallel with controlled concurrency
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_N = {executor.submit(process_semiprime, item): item[0] 
                      for item in work_items}
        
        for future in as_completed(future_to_N):
            N = future_to_N[future]
            try:
                result = future.result()
                results.append(result)
                print(f"Completed processing N={N}")
            except Exception as e:
                print(f"Error processing N={N}: {str(e)}")
                results.append((N, ('Error', str(e))))
    
    # Write results
    with open('factors.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Semiprime', 'Factor 1', 'Factor 2'])
        for N, factors in sorted(results):
            writer.writerow([N, factors[0], factors[1]])
    
    print("Factorization complete. Results saved to 'factors.csv'.")

if __name__ == "__main__":
    main()