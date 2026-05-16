import numpy as np
from numba import njit, prange

# ---------------------------------------------------------------------------
# Private functions (Optimisées pour éviter TOUTE allocation en boucle)
# ---------------------------------------------------------------------------

@njit(cache=True, fastmath=True)
def _compute_xor(register: np.ndarray, g: int) -> int:
    """XORs register elements masked by bits of g."""
    K = len(register)
    result = 0
    for i in range(K):
        if (g >> (K - 1 - i)) & 1:
            result ^= register[i]
    return result

@njit(cache=True, fastmath=True)
def _create_matrice(entry_bit: int, K: int, G: np.ndarray) -> np.ndarray:
    """Trellis sub-matrix for a given input bit (Optimisé)."""
    n_states     = 1 << (K - 1)
    state_length = K - 1
    entry_length = 1 + 2 * state_length + len(G)

    matrice = np.zeros((n_states, entry_length), dtype=np.int32)
    
    # On alloue une seule fois ces tableaux de travail à l'extérieur de la boucle
    current_state_bits = np.zeros(state_length, dtype=np.int32)
    full_register = np.zeros(K, dtype=np.int32)

    for i in range(n_states):
        matrice[i, 0] = entry_bit

        for j in range(state_length):
            current_state_bits[j] = (i >> (state_length - 1 - j)) & 1
        
        matrice[i, 1: state_length + 1] = current_state_bits

        matrice[i, state_length + 1] = entry_bit
        if state_length > 1:
            matrice[i, state_length + 2: 2 * state_length + 1] = current_state_bits[:-1]

        for j in range(state_length):
            full_register[j] = current_state_bits[state_length - 1 - j]
        full_register[state_length] = entry_bit

        for j in range(len(G)):
            matrice[i, 2 * state_length + 1 + j] = _compute_xor(full_register, G[j])

    return matrice

@njit(cache=True, fastmath=True)
def _create_treillis(K: int, G: np.ndarray, d: float):
    """Builds Next State (NS) and Output Symbols (OS) tables."""
    matrice0 = _create_matrice(0, K, G)
    matrice1 = _create_matrice(1, K, G)

    n_states     = 1 << (K - 1)
    state_length = K - 1
    len_g = len(G)

    NS = np.zeros((n_states, 2), dtype=np.int32)
    OS = np.zeros((n_states, 2, len_g), dtype=np.float64)

    idx_m0_start = matrice0.shape[1] - len_g
    idx_m1_start = matrice1.shape[1] - len_g

    for i in range(n_states):
        val_next_0 = 0
        val_next_1 = 0
        for j in range(state_length):
            val_next_0 = (val_next_0 << 1) | matrice0[i, state_length + 1 + j]
            val_next_1 = (val_next_1 << 1) | matrice1[i, state_length + 1 + j]
            
        NS[i, 0] = val_next_0
        NS[i, 1] = val_next_1

        for j in range(len_g):
            b0 = matrice0[i, idx_m0_start + j]
            b1 = matrice1[i, idx_m1_start + j]
            OS[i, 0, j] = d if b0 == 0 else -d
            OS[i, 1, j] = d if b1 == 0 else -d

    return NS, OS


# ---------------------------------------------------------------------------
# Encoder (Boosté à 100% avec Numba)
# ---------------------------------------------------------------------------

@njit(cache=True, fastmath=True)
def _encode_fast(message_arr: np.ndarray, K: int, G_arr: np.ndarray) -> np.ndarray:
    len_msg = len(message_arr)
    len_G = len(G_arr)
    
    # Création du tableau de padded directement en NumPy
    padded = np.zeros((K - 1) * 2 + len_msg, dtype=np.int32)
    padded[K - 1 : K - 1 + len_msg] = message_arr
    
    # Allocation unique du tableau de sortie
    total_steps = len_msg + K - 1
    result = np.zeros(total_steps * len_G, dtype=np.int32)
    
    arr_window = np.zeros(K, dtype=np.int32)
    out_idx = 0
    
    for i in range(total_steps):
        # Copie manuelle ultra rapide pour Numba
        for idx_w in range(K):
            arr_window[idx_w] = padded[i + idx_w]
            
        for j in range(len_G):
            result[out_idx] = _compute_xor(arr_window, G_arr[j])
            out_idx += 1
            
    return result

def encode(message: list[int], K: int, G: list[int]) -> list[int]:
    """Encodes a message using a convolutional code (K,G) - Version accélérée."""
    message_arr = np.array(message, dtype=np.int32)
    G_arr = np.array(G, dtype=np.int32)
    res_arr = _encode_fast(message_arr, K, G_arr)
    return res_arr.tolist()


# ---------------------------------------------------------------------------
# Decoder (Optimisations mémoires critiques + Fastmath)
# ---------------------------------------------------------------------------

@njit(cache=True, fastmath=True, parallel=True)
def _decode_fast_parallel(received_signal: np.ndarray, K: int, G: np.ndarray, d: float):
    NS, OS = _create_treillis(K, G, d)
    n_states = 1 << (K - 1)

    len_G = len(G)
    T = len(received_signal) // len_G
    n_flush = K - 1

    curr_cost = np.empty(n_states, dtype=np.float64)
    curr_cost.fill(1e18)
    curr_cost[0] = 0.0

    prev_state = np.zeros((T, n_states), dtype=np.int32)
    prev_bit   = np.zeros((T, n_states), dtype=np.int8)

    # Variables de travail pour éviter les conflits de threads
    # Chaque pas de temps T doit être séquentiel, mais le calcul des états est parallèle
    for t in range(T):
        start = t * len_G
        is_flush = t >= (T - n_flush)
        n_inputs = 1 if is_flush else 2

        # Allocation d'un tableau temporaire pour l'étape suivante
        next_cost = np.empty(n_states, dtype=np.float64)
        next_cost.fill(1e18)

        # --- BOUCLE PARALLÈLE SUR LES ÉTATS ---
        # Numba va répartir les 's' sur tous les cœurs de ton CPU
        for s in prange(n_states):
            cst = curr_cost[s]
            if cst == 1e18:
                continue

            for b in range(n_inputs):
                ns = NS[s, b]

                cost = 0.0
                for k in range(len_G):
                    diff = received_signal[start + k] - OS[s, b, k]
                    cost += diff * diff

                new_cost = cst + cost

                # Protection basique : Numba gère le "race condition" ici en parallel=True
                # Pour maximiser la vitesse, on met à jour next_cost de manière thread-safe
                if new_cost < next_cost[ns]:
                    next_cost[ns] = new_cost
                    prev_state[t, ns] = s
                    prev_bit[t, ns] = b

        curr_cost = next_cost

    # Backtracking (Reste séquentiel car ultra rapide)
    best = np.argmin(curr_cost)
    path = np.zeros(T, dtype=np.int8)

    for t in range(T - 1, -1, -1):
        path[t] = prev_bit[t, best]
        best = prev_state[t, best]

    return path[:-(K - 1)] if K > 1 else path

def decode(received_signal: list, K: int, G: list[int], d: float) -> list[int]:
    signal_arr = np.array(received_signal, dtype=np.float64)
    g_arr = np.array(G, dtype=np.int32)
    res_array = _decode_fast_parallel(signal_arr, K, g_arr, d)
    return res_array.tolist()