import QuantumRingsLib
from QuantumRingsLib import QuantumRegister, ClassicalRegister, QuantumCircuit
from QuantumRingsLib import QuantumRingsProvider
from QuantumRingsLib import job_monitor
from QuantumRingsLib import JobStatus
from matplotlib import pyplot as plt
import numpy as np
import math
from math import gcd

# Connect to Quantum Rings provider
provider = QuantumRingsProvider(token='rings-200.OlV43PAoB1aCdOHhDHhaq7kUP7pYvpbR', name='ss7061@srmist.edu.in')
backend = provider.get_backend("scarlet_quantum_rings")
shots = 1024

provider.active_account()

# Inverse Quantum Fourier Transform (IQFT)
def iqft_cct(qc, b, n):
    for i in range(n):
        for j in range(1, i + 1):
            qc.cu1(-math.pi / 2 ** (i - j + 1), b[j - 1], b[i])
        qc.h(b[i])
    qc.barrier()

# Plot measurement results
def plot_histogram(counts, title=""):
    fig, ax = plt.subplots(figsize=(10, 7))
    plt.xlabel("States")
    plt.ylabel("Counts")
    
    mylist = [key for key, val in counts.items() for _ in range(val)]
    unique, inverse = np.unique(mylist, return_inverse=True)
    bin_counts = np.bincount(inverse)
    
    plt.bar(unique, bin_counts)
    maxFreq = max(counts.values())
    plt.ylim(ymax=np.ceil(maxFreq / 10) * 10 if maxFreq % 10 else maxFreq + 10)
    
    plt.title(title)
    plt.show()

# Extract non-trivial factors from measurements
def find_factors(measured_values, N=15, base=7):
    factors = set()
    for result in measured_values:
        r = int(result, 2)  # Convert binary string to integer
        if r == 0:
            continue  # Ignore trivial case
        
        if r % 2 == 0:  # Only even periods are useful
            x = base ** (r // 2) - 1
            y = base ** (r // 2) + 1
            
            factor1 = gcd(x, N)
            factor2 = gcd(y, N)
            
            if 1 < factor1 < N:
                factors.add(factor1)
            if 1 < factor2 < N:
                factors.add(factor2)
    
    return list(factors)

# Define quantum circuit
numberofqubits = 7
q = QuantumRegister(numberofqubits, 'q')
c = ClassicalRegister(4, 'c')
qc = QuantumCircuit(q, c)

# Step 1: Superposition
qc.h(0)
qc.h(1)
qc.h(2)
qc.x(6)
qc.barrier()

# Step 2: Modular exponentiation for 7^x mod 15
qc.cx(q[2], q[4])
qc.cx(q[2], q[5])
qc.cx(q[6], q[4])
qc.ccx(q[1], q[5], q[3])
qc.cx(q[3], q[5])
qc.ccx(q[1], q[4], q[6])
qc.cx(q[6], q[4])
qc.barrier()

# Step 3: Inverse Quantum Fourier Transform (IQFT)
iqft_cct(qc, q, 3)

# Step 4: Measurement
qc.measure(q[0], c[0])
qc.measure(q[1], c[1])
qc.measure(q[2], c[2])

# Execute the circuit
job = backend.run(qc, shots=shots)
job_monitor(job)
result = job.result()
counts = result.get_counts()

# Plot results
plot_histogram(counts)

# Extract factors
measured_states = list(counts.keys())
factors = find_factors(measured_states)

# Print factors
if factors:
    print(f"Non-trivial factors of {15}: {factors}")
else:
    print("Failed to find non-trivial factors. Try rerunning the algorithm.")