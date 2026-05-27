import numpy as np

# ---------------------------------------------------------------------------
# Private functions
# ---------------------------------------------------------------------------

def _bitstream_to_symbols(bitstream_list: list, k: int):
    """Groups bits into packets of length k.

    Args:
        bitstream_list: List of input bits.
        k: Bits per symbol.
    """
    if len(bitstream_list) % k != 0:
        raise ValueError(f"Bitstream length ({len(bitstream_list)}) is not a multiple of k={k}.")
    
    symbols = []
    for i in range(0, len(bitstream_list), k):
        chunk = bitstream_list[i:i + k]
        
        valeur = 0
        for bit in chunk:
            valeur = (valeur << 1) | bit
            
        symbols.append(valeur)
        
    return symbols

# ---------------------------------------------------------------------------

def to_bitstream(text, encoding_dict):
    """Converts text into a list of bits using a dictionary."""
    return [int(bit) for char in text for bit in encoding_dict[char]]

def from_bitstream(bitstream_array, encoding_dict):
    """Decodes a bit array into text using a dictionary."""
    reverse_dict = {v: k for k, v in encoding_dict.items()}
    
    decoded_text = ""
    current_buffer = ""
    
    for bit in bitstream_array:
        current_buffer += str(bit) 
        
        if current_buffer in reverse_dict:
            decoded_text += reverse_dict[current_buffer]
            current_buffer = "" 
            
    return decoded_text

def map_to_4qam(bitstream: list[int], d: float = 1.0) -> list[float]:
    """Maps a bitstream into 4-QAM (QPSK) constellation coordinates.

    Args:
        bitstream: List of input bits.
        d: Constellation scaling factor.

    Mapping 4-QAM (QPSK).
      00 → [+d, +d]   01 → [+d, -d]
      10 → [-d, +d]   11
    """
    symbols = _bitstream_to_symbols(bitstream, k=2)
    return [
        coord
        for s in symbols
        for coord in (d if ((s >> 1) & 1) == 0 else -d, d if (s & 1) == 0 else -d)
    ]

def rotate_signal(data, transform_type):
    """Rotates 2D constellation points by increments of 90 degrees.

    Args:
        data: Flattened array of IQ coordinates.
        transform_type: Rotation index (1: 0°, 2: -90°, 3: 180°, 4: 90°).
    """
    data = np.asarray(data, dtype=float)
    pairs = data.reshape(-1, 2)
    a, b = pairs[:, 0], pairs[:, 1]
    if transform_type == 1: rx = np.stack([a, b], axis=1)
    elif transform_type == 2: rx = np.stack([b, -a], axis=1)
    elif transform_type == 3: rx = np.stack([-a, -b], axis=1)
    elif transform_type == 4: rx = np.stack([-b, a], axis=1)
    else: raise ValueError("Invalid transformation index.")
    return rx.flatten()

def pilot_analysis(signal, d=1.2):  # Passe la valeur de d en paramètre (ou récupère-la de ta config)
    # 1. Calcul de la moyenne des pilotes reçus (ton code actuel, très bien)
    pilot_re = np.mean(signal[0::2])
    pilot_im = np.mean(signal[1::2])
    
    # Points théoriques attendus pour chaque t_id (les 4 rotations possibles de [+d, +d])
    # À adapter selon la logique exacte de tes rotations dans `rotate_signal`
    scenarios = {
        1: (+d, +d),   # i = 1 -> Pas de modification
        2: (-d, +d),   # i = 2 -> Le canal fait [-b, a]
        3: (-d, -d),   # i = 3 -> Le canal fait [-a, -b]
        4: (+d, -d)    # i = 4 -> Le canal fait [b, -a]
    }
    
    # 2. On calcule la distance euclidienne au carré pour chaque scénario
    distances = {}
    for t_id, (target_re, target_im) in scenarios.items():
        dist = (pilot_re - target_re)**2 + (pilot_im - target_im)**2
        distances[t_id] = dist
        
    # 3. Le meilleur t_id est celui qui minimise la distance
    best_t_id = min(distances, key=distances.get)
    
    return best_t_id, (pilot_re, pilot_im)

def puncture(bits, n, K):
    """
    Supprime exactement 'n' éléments (qui doivent être pairs !) dans le tableau 
    de floats aplatis 'bits' pour ne pas désaligner les couples I/Q.
    """
    if n <= 0:
        return list(bits)
    
    # On s'assure de poinçonner des couples entiers (I, Q)
    n_pairs = n // 2
    total_len = len(bits)
    total_pairs = total_len // 2
    flush_pairs = (K - 1)  # La queue de flush en termes de couples de symboles
    
    safe_zone_start = 0
    safe_zone_end = total_pairs - flush_pairs
    
    # On choisit les indices des COUPLES à supprimer
    if (safe_zone_end) <= n_pairs:
        pairs_to_remove = set(np.linspace(0, total_pairs - 1, n_pairs, dtype=int))
    else:
        pairs_to_remove = set(np.linspace(safe_zone_start, safe_zone_end - 1, n_pairs, dtype=int))
    
    # On reconstruit la liste en enlevant les floats des couples sélectionnés
    punctured = []
    for i in range(total_pairs):
        if i not in pairs_to_remove:
            punctured.append(bits[2*i])     # Garde I
            punctured.append(bits[2*i + 1]) # Garde Q
            
    return punctured


def depuncture(soft_bits, n, K):
    """
    Réinsère des paires de 0.0 aux positions exactes du poinçonnage.
    """
    if n <= 0:
        return list(soft_bits)
        
    original_len = len(soft_bits) + n
    original_pairs = original_len // 2
    flush_pairs = (K - 1)
    
    n_pairs = n // 2
    safe_zone_start = 0
    safe_zone_end = original_pairs - flush_pairs
    
    if (safe_zone_end - safe_zone_start) <= n_pairs:
        pairs_to_replace = list(np.linspace(0, original_pairs - 1, n_pairs, dtype=int))
    else:
        pairs_to_replace = list(np.linspace(safe_zone_start, safe_zone_end - 1, n_pairs, dtype=int))
    
    depunctured = list(soft_bits)
    # On insère les couples de (0.0, 0.0) de gauche à droite
    # Pour chaque couple à l'indice 'idx', cela correspond à l'indice float '2 * idx'
    for idx in sorted(pairs_to_replace):
        depunctured.insert(2 * idx, 0.0)     # Insère le faux I
        depunctured.insert(2 * idx + 1, 0.0) # Insère le faux Q
        
    return depunctured