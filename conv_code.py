import numpy as np

def _compute_xor(register: list[int], g: int) -> int:
    """
    Sortie d'un générateur polynomial.

    register[0]   = bit le plus ANCIEN
    register[k-1] = bit le plus RÉCENT (entrée courante)
    MSB de g      → register[0]
    LSB de g      → register[k-1]
    """
    k = len(register)
    result = 0
    for i in range(k):
        if (g >> (k - 1 - i)) & 1:
            result ^= register[i]
    return result


# ---------------------------------------------------------------------------
# Encoder
# ---------------------------------------------------------------------------

def encode(message: list[int], k: int, G: list[int]) -> list[int]:
    """
    Encode un message avec un code convolutif de longueur de contrainte k.

    Paramètres
    ----------
    message : bits d'information (0 ou 1)
    k       : longueur de contrainte
    G       : polynômes générateurs (doivent tenir sur k bits, i.e. g < 2^k)

    Retour
    ------
    (len(message) + k-1) * len(G) bits codés (flush inclus).
    """
    padded = [0] * (k - 1) + message + [0] * (k - 1)
    result = []
    for i in range(len(message) + k - 1):
        window = padded[i: i + k]   # window[0]=ancien, window[k-1]=courant
        for g in G:
            result.append(_compute_xor(window, g))
    return result


# ---------------------------------------------------------------------------
# Trellis
# ---------------------------------------------------------------------------

def _create_matrice(entry_bit: int, k: int, G: list[int]) -> np.ndarray:
    """
    Sous-matrice du treillis pour un bit d'entrée donné.

    Colonnes :
      0                 : bit d'entrée
      1 .. k-1          : état courant  (MSB = bit entré le plus récemment parmi les anciens)
      k .. 2k-2         : état suivant
      2k-1 .. 2k+|G|-2  : bits de sortie
    """
    n_states     = 2 ** (k - 1)
    state_length = k - 1
    entry_length = 1 + 2 * state_length + len(G)

    matrice = np.zeros((n_states, entry_length), dtype=int)

    for i in range(n_states):
        matrice[i, 0] = entry_bit

        # État courant : i en binaire MSB en premier
        # current_state_bits[0] = bit entré le plus récemment (parmi les anciens)
        # current_state_bits[k-2] = bit le plus ancien
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


def _create_treillis(k: int, G: list[int], d: float):
    """
    Construit NS (Next State) et OS (Output Symbols).

    NS[s, b]     : état suivant depuis s avec l'entrée b
    OS[s, b, :]  : amplitudes de sortie (±d)
    """
    matrice0 = _create_matrice(0, k, G)
    matrice1 = _create_matrice(1, k, G)

    n_states     = 2 ** (k - 1)
    state_length = k - 1

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
# Viterbi soft
# ---------------------------------------------------------------------------

def decode(received_signal: list[list[float]], k: int, G: list[int],
                 d: float) -> str:
    """
    Décodeur de Viterbi à décision douce (distance euclidienne au carré).

    Paramètres
    ----------
    received_signal : liste de (N + k-1) vecteurs réels de longueur len(G)
    k               : longueur de contrainte
    G               : polynômes générateurs
    d               : amplitude de la constellation

    Retour
    ------
    Chemin décodé (bits de flush inclus).
    """
    NS, OS = _create_treillis(k, G, d)
    n_states = 2 ** (k - 1)

    n_flush_symbols = k - 1
    total_symbols   = len(received_signal)

    curr_list = [None] * n_states
    curr_list[0] = {"cost": 0.0, "path": ""}

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
                new_path = curr_list[s]["path"] + str(bit)

                if (next_list[next_state] is None
                        or new_cost < next_list[next_state]["cost"]):
                    next_list[next_state] = {"cost": new_cost, "path": new_path}

        curr_list = next_list

    if curr_list[0] is not None:
        return curr_list[0]["path"]

    valid = [x for x in curr_list if x is not None]
    return min(valid, key=lambda x: x["cost"])["path"]


# ---------------------------------------------------------------------------
# Utilitaires QAM
# ---------------------------------------------------------------------------

def bitstream_to_symbols_list(bitstream_list: list[int], k: int) -> list[int]:
    """Regroupe une liste de bits par paquets de k et les convertit en entiers."""
    if len(bitstream_list) % k != 0:
        raise ValueError(
            f"Longueur du bitstream ({len(bitstream_list)}) "
            f"n'est pas un multiple de k={k}."
        )
    symbols = []
    for i in range(0, len(bitstream_list), k):
        chunk  = bitstream_list[i: i + k]
        valeur = 0
        for bit in chunk:
            valeur = (valeur << 1) | bit
        symbols.append(valeur)
    return symbols


def map_to_4qam_custom(bitstream: list[int], d: float = 1.0) -> list[list[float]]:
    """
    Mapping 4-QAM (QPSK).

      00 → [+d, +d]   01 → [+d, -d]
      10 → [-d, +d]   11 → [-d, -d]
    """
    symbols = bitstream_to_symbols_list(bitstream, k=2)
    return [
        [d if ((s >> 1) & 1) == 0 else -d,
         d if (s & 1)         == 0 else -d]
        for s in symbols
    ]

def map_to_4qam_custom_2(bitstream: list[int], d: float = 1.0) -> list[float]:
    """
    Mapping 4-QAM (QPSK).
      00 → [+d, +d]   01 → [+d, -d]
      10 → [-d, +d]   11 → [-d, -d]
    """
    symbols = bitstream_to_symbols_list(bitstream, k=2)
    return [
        coord
        for s in symbols
        for coord in (d if ((s >> 1) & 1) == 0 else -d, d if (s & 1) == 0 else -d)
    ]

def add_awgn(signal: list[list[float]], snr_db: float) -> list[list[float]]:
    """Ajoute un bruit AWGN (snr_db = Eb/N0 en dB)."""
    snr_linear = 10 ** (snr_db / 10)
    sigma      = 1.0 / np.sqrt(2 * snr_linear)
    return [
        [sym[c] + np.random.normal(0, sigma) for c in range(len(sym))]
        for sym in signal
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def run_test(label: str, msg: list[int], k: int, G: list[int], d: float,
             snr_db: float | None = None) -> bool:
    print(f"\n{'='*60}")
    print(f"Test : {label}")
    tag = f"SNR={snr_db} dB" if snr_db is not None else "canal parfait"
    print(f"  k={k}, G={[hex(g) for g in G]}, {tag}")

    encoded  = encode(msg, k, G)
    signal   = map_to_4qam_custom(encoded, d)
    received = add_awgn(signal, snr_db) if snr_db is not None else signal

    decoded_full = decode(received, k, G, d)
    decoded      = decoded_full[:-(k - 1)] if k > 1 else decoded_full

    msg_str = "".join(str(b) for b in msg)
    ok      = msg_str == decoded
    print(f"  Envoyé  : {msg_str}")
    print(f"  Décodé  : {decoded}")
    print(f"  Résultat: {'✓ OK' if ok else '✗ ERREUR'}")
    return ok


if __name__ == "__main__":
    np.random.seed(42)

    msg = [1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0]
    d   = 1.0

    # K=3 — test de base
    # run_test("K=3  G=[7,5]         parfait", msg, 3, [7, 5], d)
    # run_test("K=3  G=[7,5]         10 dB",  msg, 3, [7, 5], d, snr_db=10.0)

    # K=7 — code NASA Voyager, polynômes en OCTAL
    # 0o171 = 0b1111001 = 121 décimal  (7 bits → K=7 ✓)
    # 0o133 = 0b1011011 =  91 décimal  (7 bits → K=7 ✓)
    run_test("K=7  G=[0o171,0o133] parfait", msg, 7, [0o171, 0o133], d)
    run_test("K=7  G=[0o171,0o133] 10 dB",  msg, 7, [0o171, 0o133], d, snr_db=10.0)
    run_test("K=7  G=[0o171,0o133]  6 dB",  msg, 7, [0o171, 0o133], d, snr_db=6.0)

    # K=7 avec polynômes en DÉCIMAL : 171 et 133 font 8 bits → K doit être 8
    # Si on passe G=[171,133] avec K=7, le MSB de 171 est ignoré → résultat faux.
    # La bonne façon : utiliser K=8.
    run_test("K=8  G=[171,133]     parfait (171/133 décimal)", msg, 8, [171, 133], d)

    # K=4
    run_test("K=4  G=[15,13]       parfait", msg, 4, [15, 13], d)