import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit import Aer, execute, transpile
from qiskit.circuit.library import QFT
from qiskit.primitives import Sampler
from math import gcd
from fractions import Fraction
import logging
from typing import List, Tuple, Optional
import time

class OptimizedShorAlgorithm:
    def __init__(self, shots: int = 2048, optimization_level: int = 3):
        """
        Initialize Shor's Algorithm implementation with configurable parameters.
        
        Args:
            shots: Number of shots for quantum execution
            optimization_level: Circuit optimization level (0-3)
        """
        self.shots = shots
        self.optimization_level = optimization_level
        self.backend = Aer.get_backend('qasm_simulator')
        self.sampler = Sampler()
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _create_quantum_circuit(self, n: int, a: int) -> QuantumCircuit:
        """
        Create the quantum circuit for period finding.
        
        Args:
            n: Number to factor
            a: Random coprime number for period finding
            
        Returns:
            QuantumCircuit: Configured quantum circuit
        """
        # Calculate required qubits
        n_count = len(bin(n)[2:])
        n_count = 2 * n_count  # Double for QPE
        
        # Create registers
        qr_count = QuantumRegister(n_count, 'count')
        qr_aux = QuantumRegister(n_count, 'aux')
        cr = ClassicalRegister(n_count, 'c')
        
        # Create circuit
        qc = QuantumCircuit(qr_count, qr_aux, cr)
        
        # Initialize counting register to superposition
        qc.h(qr_count)
        
        # Initialize auxiliary register
        qc.x(qr_aux[0])
        
        # Apply controlled operations
        for i in range(n_count):
            angle = 2 * np.pi * 2**i
            qc.cp(angle, qr_count[i], qr_aux[0])
            
        # Apply inverse QFT
        qc.append(QFT(n_count).inverse(), qr_count)
        
        # Measure counting register
        qc.measure(qr_count, cr)
        
        return qc

    def _quantum_period_finding(self, n: int, a: int) -> Optional[int]:
        """
        Perform quantum period finding for Shor's algorithm.
        
        Args:
            n: Number to factor
            a: Random coprime number
            
        Returns:
            Optional[int]: Period if found, None otherwise
        """
        try:
            # Create and execute quantum circuit
            circuit = self._create_quantum_circuit(n, a)
            transpiled_circuit = transpile(circuit, self.backend, 
                                        optimization_level=self.optimization_level)
                                        
            # Use Sampler primitive instead of QuantumInstance
            job = execute(transpiled_circuit, self.backend, shots=self.shots)
            result = job.result()
            
            # Process measurement results
            counts = result.get_counts()
            measured_phases = []
            
            for output in counts:
                decimal = int(output, 2)  # Convert to decimal
                phase = decimal / (2 ** len(output))
                measured_phases.append(phase)
            
            # Find period from phases
            for phase in measured_phases:
                frac = Fraction(phase).limit_denominator(n)
                r = frac.denominator
                if r % 2 == 0 and 1 < pow(a, r, n) < n:
                    return r
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Error in period finding: {str(e)}")
            return None

    def factor(self, n: int, max_attempts: int = 10) -> List[Tuple[int, int]]:
        """
        Factor a semiprime number using Shor's algorithm.
        
        Args:
            n: Number to factor
            max_attempts: Maximum number of attempts for period finding
            
        Returns:
            List[Tuple[int, int]]: List of prime factor pairs
        """
        if n % 2 == 0:
            return [(2, n // 2)]
            
        if n < 3:
            return [(n, 1)]
            
        factors = []
        attempt = 0
        
        while attempt < max_attempts:
            # Choose random number coprime to n
            a = np.random.randint(2, n)
            if gcd(a, n) != 1:
                factors.append((gcd(a, n), n // gcd(a, n)))
                break
                
            # Find period
            r = self._quantum_period_finding(n, a)
            
            if r is not None:
                # Check if period is useful
                if r % 2 != 0:
                    attempt += 1
                    continue
                    
                # Calculate potential factors
                p = gcd(pow(a, r//2, n) + 1, n)
                q = gcd(pow(a, r//2, n) - 1, n)
                
                if p * q == n:
                    factors.append((p, q))
                    break
                    
            attempt += 1
            
        return factors

def benchmark_shor_algorithm(semiprimes: dict):
    """
    Benchmark Shor's algorithm implementation on a set of semiprimes.
    
    Args:
        semiprimes: Dictionary of bit length to semiprime number
    """
    shor = OptimizedShorAlgorithm()
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
        
    return results

# Example usage
if __name__ == "__main__":
    # Sample semiprimes dictionary
    test_semiprimes = {
        8: 143,
        10: 899,
        12: 3127,
        14: 11009,
        16: 47053
    }
    
    # Run benchmark
    print("Starting Shor's Algorithm benchmark...")
    results = benchmark_shor_algorithm(test_semiprimes)
    
    # Print results
    for result in results:
        print(f"\nFactoring {result['number']} ({result['bits']} bits):")
        if result['success']:
            p, q = result['factors']
            print(f"Factors found: {p} × {q}")
            print(f"Verification: {p * q == result['number']}")
        else:
            print(f"Factorization failed: {result.get('error', 'No factors found')}")
        print(f"Time taken: {result['time']:.2f} seconds")