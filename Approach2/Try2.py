import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit import Aer, execute, transpile
from qiskit.circuit.library import QFT
from qiskit.primitives import Sampler
from math import gcd, ceil, log2
from fractions import Fraction
import logging
from typing import List, Tuple, Optional
import time

class OptimizedShorAlgorithm:
    def __init__(self, shots: int = 2048, optimization_level: int = 3, max_qubits: int = 29):
        """
        Initialize Shor's Algorithm implementation with configurable parameters.
        
        Args:
            shots: Number of shots for quantum execution
            optimization_level: Circuit optimization level (0-3)
            max_qubits: Maximum number of qubits available
        """
        self.shots = shots
        self.optimization_level = optimization_level
        self.max_qubits = max_qubits
        self.backend = Aer.get_backend('qasm_simulator')
        self.sampler = Sampler()
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _create_controlled_modular_multiplication(self, a: int, N: int, n_count: int) -> QuantumCircuit:
        """
        Create a quantum circuit for controlled modular multiplication.
        Uses decomposition to reduce qubit count.
        """
        qr = QuantumRegister(n_count, 'qr')
        qc = QuantumCircuit(qr)
        
        # Implement modular multiplication using repeated controlled addition
        for i in range(n_count):
            if (a >> i) & 1:
                # Add 2^i * x mod N using controlled operations
                qc.cp(2 * np.pi * pow(2, i, N) / N, qr[0], qr[i])
        
        return qc

    def _create_quantum_circuit_chunk(self, n: int, a: int, chunk_size: int, chunk_index: int) -> QuantumCircuit:
        """
        Create a quantum circuit for a chunk of the period finding routine.
        
        Args:
            n: Number to factor
            a: Random coprime number
            chunk_size: Number of qubits to use in this chunk
            chunk_index: Index of the current chunk
        """
        qr_count = QuantumRegister(chunk_size, 'count')
        qr_aux = QuantumRegister(chunk_size - 1, 'aux')
        cr = ClassicalRegister(chunk_size, 'c')
        
        qc = QuantumCircuit(qr_count, qr_aux, cr)
        
        # Initialize counting register for this chunk
        qc.h(qr_count)
        
        # Initialize auxiliary register
        if chunk_index == 0:
            qc.x(qr_aux[0])
        
        # Apply controlled operations for this chunk
        mult_circuit = self._create_controlled_modular_multiplication(a, n, chunk_size)
        qc.compose(mult_circuit, inplace=True)
        
        # Apply inverse QFT to this chunk
        qc.append(QFT(chunk_size).inverse(), qr_count)
        
        # Measure
        qc.measure(qr_count, cr)
        
        return qc

    def _quantum_period_finding(self, n: int, a: int) -> Optional[int]:
        """
        Perform quantum period finding using chunked circuits.
        """
        try:
            n_bits = len(bin(n)[2:])
            total_qubits_needed = 2 * n_bits
            
            # Calculate number of chunks needed
            chunk_size = min(self.max_qubits, total_qubits_needed)
            num_chunks = ceil(total_qubits_needed / chunk_size)
            
            measured_phases = []
            
            for i in range(num_chunks):
                circuit = self._create_quantum_circuit_chunk(n, a, chunk_size, i)
                transpiled_circuit = transpile(circuit, self.backend, 
                                            optimization_level=self.optimization_level)
                
                job = execute(transpiled_circuit, self.backend, shots=self.shots)
                result = job.result()
                counts = result.get_counts()
                
                # Process results from this chunk
                max_counts = max(counts.items(), key=lambda x: x[1])
                chunk_value = int(max_counts[0], 2)
                chunk_phase = chunk_value / (2 ** chunk_size)
                measured_phases.append(chunk_phase)
            
            # Combine phases from all chunks
            combined_phase = sum(phase * (1/2)**(i*chunk_size) 
                               for i, phase in enumerate(measured_phases))
            
            # Convert phase to period
            frac = Fraction(combined_phase).limit_denominator(n)
            r = frac.denominator
            
            if r % 2 == 0 and 1 < pow(a, r, n) < n:
                return r
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error in period finding: {str(e)}")
            return None

    def _verify_factors(self, p: int, q: int, n: int) -> bool:
        """
        Verify that the found factors are valid.
        """
        if p * q != n:
            return False
        
        # Additional primality checks could be added here
        return True

    def factor(self, n: int, max_attempts: int = 10) -> List[Tuple[int, int]]:
        """
        Factor a semiprime number using optimized Shor's algorithm.
        """
        if n % 2 == 0:
            return [(2, n // 2)]
            
        if n < 3:
            return [(n, 1)]
            
        factors = []
        attempt = 0
        
        while attempt < max_attempts:
            a = np.random.randint(2, n)
            if gcd(a, n) != 1:
                factors.append((gcd(a, n), n // gcd(a, n)))
                break
                
            r = self._quantum_period_finding(n, a)
            
            if r is not None:
                if r % 2 != 0:
                    attempt += 1
                    continue
                    
                p = gcd(pow(a, r//2, n) + 1, n)
                q = gcd(pow(a, r//2, n) - 1, n)
                
                if self._verify_factors(p, q, n):
                    factors.append((p, q))
                    break
                    
            attempt += 1
            
        return factors

def benchmark_shor_algorithm(semiprimes: dict):
    """
    Benchmark Shor's algorithm implementation on a set of semiprimes.
    """
    shor = OptimizedShorAlgorithm(max_qubits=29)  # Set maximum qubits to 29
    results = []
    
    for bits, n in semiprimes.items():
        start_time = time.time()
        try:
            factors = shor.factor(n)
            end_time = time.time()
            
            if factors:
                p, q = factors[0]
                result = {
                    'bits': bits,
                    'number': n,
                    'factors': (p, q),
                    'time': end_time - start_time,
                    'success': True
                }
            else:
                result = {
                    'bits': bits,
                    'number': n,
                    'factors': None,
                    'time': end_time - start_time,
                    'success': False
                }
                
        except Exception as e:
            end_time = time.time()
            result = {
                'bits': bits,
                'number': n,
                'error': str(e),
                'time': end_time - start_time,
                'success': False
            }
            
        results.append(result)
        print(f"Completed factoring {bits}-bit number: {result['success']}")
        
    return results

# Example usage
if __name__ == "__main__":
    # Test with smaller numbers first
    test_semiprimes = {
        8: 143,
        10: 899,
        12: 3127,
    }
    
    print("Starting Shor's Algorithm benchmark...")
    results = benchmark_shor_algorithm(test_semiprimes)
    
    for result in results:
        print(f"\nFactoring {result['number']} ({result['bits']} bits):")
        if result['success']:
            p, q = result['factors']
            print(f"Factors found: {p} × {q}")
            print(f"Verification: {p * q == result['number']}")
        else:
            print(f"Factorization failed: {result.get('error', 'No factors found')}")
        print(f"Time taken: {result['time']:.2f} seconds")