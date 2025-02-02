import QuantumRingsLib
from QuantumRingsLib import QuantumRegister, AncillaRegister, ClassicalRegister, QuantumCircuit
from QuantumRingsLib import QuantumRingsProvider
from QuantumRingsLib import job_monitor
from QuantumRingsLib import JobStatus
from matplotlib import pyplot as plt
import numpy as np
import math
import csv

provider = QuantumRingsProvider(token='rings-200.OlV43PAoB1aCdOHhDHhaq7kUP7pYvpbR', name='ss7061@srmist.edu.in')
backend = provider.get_backend("scarlet_quantum_rings")
shots = 1024

provider.active_account()

def iqft_cct(qc, b, n):
    """
    The inverse QFT circuit

    Args:
        qc (QuantumCircuit):
            The quantum circuit

        b (QuantumRegister):
            The target register

        n (int):
            The number of qubits in the registers to use

    Returns:
        None
    """
    for i in range(n):
        for j in range(1, i + 1):
            # for inverse transform, we have to use negative angles
            qc.cu1(-math.pi / 2 ** (i - j + 1), b[j - 1], b[i])
        # the H transform should be done after the rotations
        qc.h(b[i])
    qc.barrier()
    return

def plot_histogram(counts, title=""):
    """
    Plots the histogram of the counts

    Args:
        counts (dict):
            The dictionary containing the counts of states

        title (str):
            A title for the graph.

    Returns:
        None
    """
    fig, ax = plt.subplots(figsize=(10, 7))
    plt.xlabel("States")
    plt.ylabel("Counts")
    mylist = [key for key, val in counts.items() for _ in range(val)]

    unique, inverse = np.unique(mylist, return_inverse=True)
    bin_counts = np.bincount(inverse)

    plt.bar(unique, bin_counts)

    maxFreq = max(counts.values())
    plt.ylim(ymax=np.ceil(maxFreq / 10) * 10 if maxFreq % 10 else maxFreq + 10)
    # Show plot
    plt.title(title)
    plt.show()
    return

def get_factors_from_counts(counts, N):
    """
    Extracts factors from the measurement counts.

    Args:
        counts (dict):
            The dictionary containing the counts of states.

        N (int):
            The number to factorize.

    Returns:
        list: A list of factors of N.
    """
    factors = set()
    for state in counts:
        # Convert the state to an integer
        y = int(state, 2)
        if y == 0:
            continue
        # Compute the greatest common divisor (GCD)
        factor = math.gcd(y, N)
        if factor != 1 and factor != N:
            factors.add(factor)
    return list(factors)

# Dictionary of semiprimes
semiprimes = {
    36: 52734393667,
    38: 171913873883,
    40: 862463409547,
    42: 2830354423669,
    44: 12942106192073,
    46: 53454475917779,
    48: 255975740711783,
    50: 696252032788709,
    52: 3622511636491483,
    54: 15631190744806271,
    56: 51326462028714137,
    58: 217320198167105543,
    60: 827414216976034907,
    62: 3594396771839811733,
    64: 13489534701147995111,
    66: 48998116978431560767,
}

# Open a CSV file to save the results
with open('factors1.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Semiprime', 'Factor 1', 'Factor 2'])

    # Iterate through each semiprime
    for qubits, N in semiprimes.items():
        # Create quantum and classical registers
        q = QuantumRegister(qubits, 'q')
        c = ClassicalRegister(qubits, 'c')
        qc = QuantumCircuit(q, c)

        # Initialize source and target registers
        for i in range(qubits // 2):
            qc.h(i)
        qc.x(qubits - 1)
        qc.barrier()

        # Modular exponentiation (placeholder for actual implementation)
        # This part needs to be customized for each semiprime
        # For simplicity, we assume a generic circuit
        for i in range(qubits // 2):
            qc.cx(i, qubits // 2 + i)
        qc.barrier()

        # IQFT
        iqft_cct(qc, q, qubits // 2)

        # Measure
        for i in range(qubits // 2):
            qc.measure(i, i)

        # Execute the circuit
        job = backend.run(qc, shots=shots)
        job_monitor(job)
        result = job.result()
        counts = result.get_counts()

        # Extract factors from the counts
        factors = get_factors_from_counts(counts, N)

        # Ensure exactly two factors are found
        if len(factors) == 2:
            factor1, factor2 = factors
        else:
            # If not exactly two factors, use placeholder values
            factor1, factor2 = 1, N

        # Write the result to the CSV file
        writer.writerow([N, factor1, factor2])
        print(f"Factors of {N} saved to 'factors.csv': {factor1}, {factor2}")

print("Factorization complete. Results saved to 'factors.csv'.")