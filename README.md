# Digital ASCII Transceiver (COM-302)

Welcome to our **Digital Communications** project as part of the course *COM-302 Principles of Digital Communications*! The core objective of this project was to design and implement a complete digital communication pipeline—specifically, a software-defined transmitter/receiver (transceiver).

Since the project guidelines required our system to support a specific 64-character alphabet using standard ASCII characters, we named it the **ASCII-Transceiver**.

> 💡 **Note on the Implementation:** Since this course focuses purely on *digital* communications, the entire analog portion of the pipeline —including the channel effects— is mocked using a Python script. Our software implementation handling the actual data stream effectively ends at the modulation stage before the simulation takes over.

![Processed constallations](assets/constellations.png)

---

## 🚀 Project Constraints & Objectives

We were tasked with transmitting a message under the following physical and architectural constraints:

* **Energy Constraint:** $E \le 1200\text{ J}$
* **Message Length:** $\le 500\text{ bits}$ (for a 40-character input message).
* **Target Alphabet:** `abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .`

---

## 🛠️ System Pipeline

### 1. Transmitter
* **Pilot Generation:** Creates a known sequence of identical inputs used by the receiver for channel calibration.
* **Source Coding:** Maps the character alphabet to binary bits (e.g., experimenting with Huffman coding optimized for the English language).
* **Channel Coding:** Applies a Convolutional Code ($K=7$, $G=(171, 133)$)— a historical NASA standard used in deep-space missions.
* **Modulation:** 4-QAM (Quadrature Amplitude Modulation).

### 2. The Channel (Simulated Noise)
The transmitted signal passes through a simulated channel that introduces both phase rotation and thermal noise:
1.  **Random Phase Rotation:** Vertices are randomly rotated by $90^\circ$, $180^\circ$, $270^\circ$, or $0^\circ$ based on a uniform distribution:
    $$\theta \in \{0^\circ, 90^\circ, 180^\circ, 270^\circ\}$$
2.  **Additive White Gaussian Noise (AWGN):** Adds standard Gaussian noise with a mean of 0 and a variance of 1.

### 3. Receiver
* **Phase Correction:** Averages the received pilot symbols to estimate the rotation angle and rotate the signal back to its original orientation.
* **Soft-Decision Decoding:** Skip traditional demodulation! The raw, continuous measurements from the channel are fed directly into a Soft Viterbi algorithm.
* **Source Decoding:** Reconstructs the original text message from the decoded bits using the alphabet mapping.

---

## 📊 Engineering Discussion

### Why Convolutional Code ($K=7, G=(171,133)$)?
This specific convolutional code is an industry classic, famously utilized byf NASA in the **Voyager 2** spacecraft. 
Among all possible convolutional codes, it offers the best performance gains for a mininal implementation cost.
Why was it used by NASA ?
Its beauty lies in the asymmetry of its complexity: the encoder is computationally lightweight and highly energy-efficient (ideal for a spacecraft or power-constrained transmitter), while the heavier computational burden is shifted to the decoder on Earth. While modern protocols utilize more advanced methods like Turbo Codes, convolutional coding remains a robust baseline standard.

### The Power of Soft Viterbi Decoding
Standard Viterbi decoding operates on hard binary choices (0 or 1) and evaluates paths using the **Hamming distance**. 

Instead, our implementation uses **Soft-Decision Viterbi Decoding**. In this version, we bypass the demodulator and directly feed the raw values straight from the Analog-to-Digital Converter (ADC) into the decoding algorithm. What are the advantages of doing so ? Maximizing information usage. To understand let us go through a dummy example.

#### 🧩 A Simple Example: Hard vs. Soft Decisions
Imagine a simple encoder that adds a parity bit to a 3-bit message:
* **Sent:** `101` $\rightarrow$ **Encoded Output:** `1010`
* **Hard Receiver:** Receives `1110`. It detects an error because the parity doesn't match, but it has no idea *which* bit flipped.
* **Soft Receiver:** Looks directly at the continuous voltage levels from the ADC, getting values like `[0.9, 0.4, 0.7, 0.2]`. Looking at these values, it becomes highly obvious that the second bit (`0.4`) was supposed to be a `0` but got corrupted by noise. 

By leveraging this extra "soft" information, our pipeline achieves an impressive **2 dB gain in SNR performance** over a hard-decision system.

---

## 📈 Going Further

* **Energy Optimization:** A bonus was offered to the team that achieved the absolute minimum energy consumption. Due to a packed semester workload, we focused on meeting the baseline constraints rather than optimizing for the absolute minimum, but calculating the theoretical Shannon limit for minimal achievable energy remains a fascinating extension!
* **Security Track:** As a future improvement, a cryptographic layer could easily be stacked on top of the source coding phase.

---

## 👩‍💻 For Visitors & Students

This project is an incredible learning tool. If you want to sharpen your digital communications and DSP knowledge, we highly encourage you to **delete everything except `channel.py`** and try to build your own transmitter and receiver from scratch to meet the project constraints!

If you want to explore the project, we highly recommend using the visualization. It beautifully demonstrates how messy and mixed the data constellation looks when the QAM spacing ($d$) is small, showcasing the incredible error-correcting power of the Soft Viterbi algorithm.

## 📜 Theory References
The mathematical derivations and theoretical exercises behind this implementation can be found in our Overleaf document:  
🔗 [View Theory Document](https://www.overleaf.com/project/6a00a5d3ddacfe8cdca0dc5a)

---

## Authors
* **[@mthoux](https://github.com/mthoux)** — Transceiver and theory
* **[@Romain-du-25](https://github.com/Romain-du-25)** — Theory
* **[@DrMoebius1](https://github.com/DrMoebius1)** — Theory

---

## 📄 License
This project is licensed under the **MIT License**. Feel free to fork it, experiment with it, share it, or use it as educational material!