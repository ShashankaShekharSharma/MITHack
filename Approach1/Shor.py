from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit.visualization import plot_circuit
import matplotlib.pyplot as plt
import numpy as np

# Define the number of qubits and shots
numberofqubits = 7
shots = 1024

# Create quantum and classical registers
q = QuantumRegister(numberofqubits, 'q')
c = ClassicalRegister(4, 'c')

# Create a quantum circuit
qc = QuantumCircuit(q, c)

# Initialize source and target registers
qc.h(0)
qc.h(1)
qc.h(2)
qc.x(6)
qc.barrier()

# Modular exponentiation 7^x mod 15
qc.cx(q[2], q[4])
qc.cx(q[2], q[5])
qc.cx(q[6], q[4])
qc.ccx(q[1], q[5], q[3])
qc.cx(q[3], q[5])
qc.ccx(q[1], q[4], q[6])
qc.cx(q[6], q[4])
qc.barrier()

# Inverse Quantum Fourier Transform (IQFT)
def iqft_cct(qc, q, n):
    for qubit in range(n//2):
        qc.swap(q[qubit], q[n - qubit - 1])
    for j in range(n):
        for m in range(j):
            qc.cp(-np.pi/float(2**(j-m)), q[m], q[j])
        qc.h(q[j])

iqft_cct(qc, q, 3)

# Measure
qc.measure(q[0], c[0])
qc.measure(q[1], c[1])
qc.measure(q[2], c[2])

# Draw the circuit
qc.draw('mpl')

# Save the circuit as a PNG file
qc.draw('mpl', filename='shors_circuit.png')

# Show the circuit
plt.show()