import numpy as np
from numba import njit

# ---------------------------------------------------------------------------
# Private functions
# ---------------------------------------------------------------------------

@njit
def _compute_xor(register: np.ndarray, g: int) -> int:
    """XORs register elements masked by bits of g."""
    K = len(register)
    result = 0
    for i in range(K):
        if (g >> (K - 1 - i)) & 1:
            result ^= register[i]
    return result

@njit
def _create_matrice(entry_bit: int, K: int, G: np.ndarray) -> np.ndarray:
    """Trellis sub-matrix for a given input bit."""
    n_states     = 2 ** (K - 1)
    state_length = K - 1
    entry_length = 1 + 2 * state_length + len(G)

    matrice = np.zeros((n_states, entry_length), dtype=np.int32)

    for i in range(n_states):
        matrice[i, 0] = entry_bit

        # Remplacement des list comprehensions par des boucles simples pour Numba
        current_state_bits = np.zeros(state_length, dtype=np.int32)
        for j in range(state_length):
            current_state_bits[j] = (i >> (state_length - 1 - j)) & 1
        
        matrice[i, 1: state_length + 1] = current_state_bits

        # next state
        matrice[i, state_length + 1] = entry_bit
        if state_length > 1:
            matrice[i, state_length + 2: 2 * state_length + 1] = current_state_bits[:-1]

        # full register (current inverted + entry_bit)
        full_register = np.zeros(K, dtype=np.int32)
        for j in range(state_length):
            full_register[j] = current_state_bits[state_length - 1 - j]
        full_register[state_length] = entry_bit

        for j, g in enumerate(G):
            matrice[i, 2 * state_length + 1 + j] = _compute_xor(full_register, g)

    return matrice

@njit
def _create_treillis(K: int, G: np.ndarray, d: float):
    """Builds Next State (NS) and Output Symbols (OS) tables."""
    matrice0 = _create_matrice(0, K, G)
    matrice1 = _create_matrice(1, K, G)

    n_states     = 2 ** (K - 1)
    state_length = K - 1

    NS = np.zeros((n_states, 2), dtype=np.int32)
    OS = np.zeros((n_states, 2, len(G)), dtype=np.float64)

    for i in range(n_states):
        # Calcul de l'index entier binaire à la main (Numba n'aime pas "".join et map)
        val_next_0 = 0
        val_next_1 = 0
        for j in range(state_length):
            bit0 = matrice0[i, state_length + 1 + j]
            bit1 = matrice1[i, state_length + 1 + j]
            val_next_0 = (val_next_0 << 1) | bit0
            val_next_1 = (val_next_1 << 1) | bit1
            
        NS[i, 0] = val_next_0
        NS[i, 1] = val_next_1

        # Attribution des amplitudes
        len_g = len(G)
        for j in range(len_g):
            b0 = matrice0[i, matrice0.shape[1] - len_g + j]
            b1 = matrice1[i, matrice1.shape[1] - len_g + j]
            OS[i, 0, j] = d if b0 == 0 else -d
            OS[i, 1, j] = d if b1 == 0 else -d

    return NS, OS


# ---------------------------------------------------------------------------
# Encoder
# ---------------------------------------------------------------------------

def encode(message: list[int], K: int, G: list[int]) -> list[int]:
    """Encodes a message using a convolutional code (K,G)."""
    padded = [0] * (K - 1) + message + [0] * (K - 1)
    result = []
    # Conversion locale pour la fonction de calcul
    arr_window = np.zeros(K, dtype=np.int32)
    for i in range(len(message) + K - 1):
        window = padded[i: i + K]
        for idx_w, w in enumerate(window):
            arr_window[idx_w] = w
        for g in G:
            result.append(_compute_xor(arr_window, g))
    return result

# ---------------------------------------------------------------------------
# Decoder (Boosté par Numba)
# ---------------------------------------------------------------------------

@njit(parallel=True, fastmath=True, cache=True)
def _decode_fast_optimized(received_signal, K, G, d):
    NS, OS = _create_treillis(K, G, d)
    n_states = 2 ** (K - 1)

    len_G = len(G)
    T = len(received_signal) // len_G
    n_flush = K - 1

    # coûts
    curr_cost = np.full(n_states, 1e18)
    next_cost = np.full(n_states, 1e18)
    curr_cost[0] = 0.0

    # backpointers (ULTRA important)
    prev_state = np.zeros((T, n_states), dtype=np.int32)
    prev_bit   = np.zeros((T, n_states), dtype=np.int8)

    for t in range(T):

        start = t * len_G

        # reset
        for i in range(n_states):
            next_cost[i] = 1e18

        is_flush = t >= T - n_flush

        for s in range(n_states):
            cst = curr_cost[s]
            if cst == 1e18:
                continue

            n_inputs = 1 if is_flush else 2

            for b in range(n_inputs):
                ns = NS[s, b]

                # coût
                cost = 0.0
                for k in range(len_G):
                    diff = received_signal[start + k] - OS[s, b, k]
                    cost += diff * diff

                new_cost = cst + cost

                if new_cost < next_cost[ns]:
                    next_cost[ns] = new_cost
                    prev_state[t, ns] = s
                    prev_bit[t, ns] = b

        # swap
        for i in range(n_states):
            curr_cost[i] = next_cost[i]

    # backtracking
    best = np.argmin(curr_cost)
    path = np.zeros(T, dtype=np.int8)

    for t in range(T - 1, -1, -1):
        path[t] = prev_bit[t, best]
        best = prev_state[t, best]

    return path[:-(K - 1)] if K > 1 else path


def decode(received_signal: list, K: int, G: list[int], d: float) -> list[int]:
    """Interface du décodeur acceptant des listes Python standards.
    
    Convertit les entrées en types NumPy pour satisfaire Numba, puis réexporte.
    """
    signal_arr = np.array(received_signal, dtype=np.float64)
    g_arr = np.array(G, dtype=np.int32)
    
    res_array = _decode_fast_optimized(signal_arr, K, g_arr, d)
    
    # Renvoie une liste de int standards pour rester compatible avec ton main.py
    return [int(b) for b in res_array]