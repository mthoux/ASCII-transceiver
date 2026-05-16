import numpy as np

# ---------------------------------------------------------------------------
# Private functions
# ---------------------------------------------------------------------------

def _compute_xor(register: list[int], g: int) -> int:
    """XORs register elements masked by bits of g.

    Args:
        register: List of values.
        g: Bitmask matching register length.
    """
    K = len(register)
    result = 0
    for i in range(K):
        if (g >> (K - 1 - i)) & 1:
            result ^= register[i]
    return result

def _create_matrice(entry_bit: int, K: int, G: list[int]) -> np.ndarray:
    """Trellis sub-matrix for a given input bit.

    Args:
        entry_bit: Current input bit.
        K: Memory length.
        G: List of generator polynomials.
    """
    n_states     = 2 ** (K - 1)
    state_length = K - 1
    entry_length = 1 + 2 * state_length + len(G)

    matrice = np.zeros((n_states, entry_length), dtype=int)

    for i in range(n_states):
        matrice[i, 0] = entry_bit

        current_state_bits = [(i >> (state_length - 1 - j)) & 1
                              for j in range(state_length)]
        matrice[i, 1: state_length + 1] = current_state_bits

        next_state_bits = [entry_bit] + current_state_bits[:-1]
        matrice[i, state_length + 1: 2 * state_length + 1] = next_state_bits

        full_register = current_state_bits[::-1] + [entry_bit]

        for j, g in enumerate(G):
            matrice[i, 2 * state_length + 1 + j] = _compute_xor(full_register, g)

    return matrice


def _create_treillis(K: int, G: list[int], d: float):
    """Builds Next State (NS) and Output Symbols (OS) tables.

    Args:
        K: Memory length.
        G: List of generator polynomials.
        d: Constellation amplitude.

    Returns:
        NS[s, b]    : Next state from state s with input bit b.
        OS[s, b, :] : Modulated output amplitudes (±d) for state s and input b.
    """
    matrice0 = _create_matrice(0, K, G)
    matrice1 = _create_matrice(1, K, G)

    n_states     = 2 ** (K - 1)
    state_length = K - 1

    NS = np.zeros((n_states, 2), dtype=int)
    OS = np.zeros((n_states, 2, len(G)), dtype=float)

    for i in range(n_states):
        bits_next_0 = matrice0[i, state_length + 1: 2 * state_length + 1]
        NS[i, 0] = int("".join(map(str, bits_next_0)), 2) if state_length > 0 else 0

        bits_next_1 = matrice1[i, state_length + 1: 2 * state_length + 1]
        NS[i, 1] = int("".join(map(str, bits_next_1)), 2) if state_length > 0 else 0

        OS[i, 0] = [d if b == 0 else -d for b in matrice0[i, -len(G):]]
        OS[i, 1] = [d if b == 0 else -d for b in matrice1[i, -len(G):]]

    return NS, OS


# ---------------------------------------------------------------------------
# Encoder
# ---------------------------------------------------------------------------

def encode(message: list[int], K: int, G: list[int]) -> list[int]:
    """Encodes a message using a convolutional code (K,G).

    Args:
        message: Information bits (0 or 1).
        K: Memory length.
        G: Generator polynomials (g < 2^K).

    Returns:
        Coded bits including the flush sequence.
    """
    padded = [0] * (K - 1) + message + [0] * (K - 1)
    result = []
    for i in range(len(message) + K - 1):
        window = padded[i: i + K]   # window[0]=ancien, window[K-1]=courant
        for g in G:
            result.append(_compute_xor(window, g))
    return result

# ---------------------------------------------------------------------------
# Decoder
# ---------------------------------------------------------------------------

def decode(received_signal: list[list[float]], K: int, G: list[int],
                 d: float) -> str:
    """Soft-decision Viterbi decoder using squared Euclidean distance.

    Args:
        received_signal: Received symbols.
        K: Memory length.
        G: Generator polynomials.
        d: Constellation amplitude.

    Returns:
        Decoded bit sequence (flush bits removed).
    """
    NS, OS = _create_treillis(K, G, d)
    n_states = 2 ** (K - 1)

    n_flush_symbols = K - 1
    total_symbols   = len(received_signal)
    len_G           = len(G)
    total_symbols   = len(received_signal) // len_G

    curr_list = [None] * n_states
    curr_list[0] = {"cost": 0.0, "path": []}

    for idx, start_idx in enumerate(range(0, len(received_signal), len_G)):

        received_symbols = received_signal[start_idx : start_idx + len_G]

        next_list       = [None] * n_states
        is_flushing     = idx >= total_symbols - n_flush_symbols
        possible_inputs = [0] if is_flushing else [0, 1]

        for s in range(n_states):
            if curr_list[s] is None:
                continue
            for bit in possible_inputs:
                next_state      = NS[s, bit]
                expected_output = OS[s, bit]

                branch_cost = sum(
                    (received_symbols[c] - expected_output[c]) ** 2
                    for c in range(len(G))
                )
                new_cost = curr_list[s]["cost"] + branch_cost
                new_path = [*curr_list[s]["path"], bit]

                if (next_list[next_state] is None
                        or new_cost < next_list[next_state]["cost"]):
                    next_list[next_state] = {"cost": new_cost, "path": new_path}

        curr_list = next_list

    return curr_list[0]["path"][:-(K - 1)] if K > 1 else curr_list[0]["path"]