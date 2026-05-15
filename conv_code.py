import numpy as np

# ---------------------------------------------------------------------------
# Private functions
# ---------------------------------------------------------------------------

def _compute_xor(register: list[int], g: int) -> int:
    """
    Sortie d'un générateur polynomial.

    register[0]   = bit le plus ANCIEN
    register[K-1] = bit le plus RÉCENT (entrée courante)
    MSB de g      → register[0]
    LSB de g      → register[K-1]
    """
    K = len(register)
    result = 0
    for i in range(K):
        if (g >> (K - 1 - i)) & 1:
            result ^= register[i]
    return result

def _create_matrice(entry_bit: int, K: int, G: list[int]) -> np.ndarray:
    """
    Sous-matrice du treillis pour un bit d'entrée donné.

    Colonnes :
      0                 : bit d'entrée
      1 .. K-1          : état courant  (MSB = bit entré le plus récemment parmi les anciens)
      K .. 2K-2         : état suivant
      2K-1 .. 2K+|G|-2  : bits de sortie
    """
    n_states     = 2 ** (K - 1)
    state_length = K - 1
    entry_length = 1 + 2 * state_length + len(G)

    matrice = np.zeros((n_states, entry_length), dtype=int)

    for i in range(n_states):
        matrice[i, 0] = entry_bit

        # État courant : i en binaire MSB en premier
        # current_state_bits[0] = bit entré le plus récemment (parmi les anciens)
        # current_state_bits[K-2] = bit le plus ancien
        current_state_bits = [(i >> (state_length - 1 - j)) & 1
                              for j in range(state_length)]
        matrice[i, 1: state_length + 1] = current_state_bits

        # État suivant : décalage + insertion de entry_bit en MSB
        next_state_bits = [entry_bit] + current_state_bits[:-1]
        matrice[i, state_length + 1: 2 * state_length + 1] = next_state_bits

        # Registre dans l'ordre encode_bits (plus_ancien → plus_récent) :
        #   current_state_bits inversé donne [plus_ancien, ..., plus_récent_parmi_anciens]
        #   puis on ajoute entry_bit en dernière position (le plus récent de tous)
        full_register = current_state_bits[::-1] + [entry_bit]

        for j, g in enumerate(G):
            matrice[i, 2 * state_length + 1 + j] = _compute_xor(full_register, g)

    return matrice


def _create_treillis(K: int, G: list[int], d: float):
    """
    Construit NS (Next State) et OS (Output Symbols).

    NS[s, b]     : état suivant depuis s avec l'entrée b
    OS[s, b, :]  : amplitudes de sortie (±d)
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
    """
    Encode un message avec un code convolutif de longueur de contrainte K.

    Paramètres
    ----------
    message : bits d'information (0 ou 1)
    K       : longueur de contrainte
    G       : polynômes générateurs (doivent tenir sur K bits, i.e. g < 2^K)

    Retour
    ------
    (len(message) + K-1) * len(G) bits codés (flush inclus).
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
    """
    Décodeur de Viterbi à décision douce (distance euclidienne au carré).

    Paramètres
    ----------
    received_signal : liste de (N + K-1) vecteurs réels de longueur len(G)
    K               : longueur de contrainte
    G               : polynômes générateurs
    d               : amplitude de la constellation

    Retour
    ------
    Chemin décodé (bits de flush inclus).
    """
    NS, OS = _create_treillis(K, G, d)
    n_states = 2 ** (K - 1)

    n_flush_symbols = K - 1
    total_symbols   = len(received_signal)

    curr_list = [None] * n_states
    curr_list[0] = {"cost": 0.0, "path": []}

    for idx, received_symbols in enumerate(received_signal):
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