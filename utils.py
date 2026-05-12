import numpy as np

# --- CONVERSION TEXTE ---
def index_alphabet(char: str, alphabet: str):
    if char not in alphabet:
        raise ValueError(f"Caractère '{char}' non autorisé.")
    return alphabet.index(char) 

def construct_list(message: str, alphabet: str):
    return [index_alphabet(char, alphabet) for char in message]

def reconstruct_message(indices: list, alphabet: str):
    return "".join([alphabet[i] for i in indices])

# --- NOUVELLE LOGIQUE : BITSTREAM GÉNÉRIQUE ---
def to_bitstream(indices: list, bits_per_char: int = 6):
    """Transforme les indices en une liste de bits (0, 1)."""
    bitstream = []
    for val in indices:
        for i in reversed(range(bits_per_char)):
            bitstream.append((val >> i) & 1)
    return bitstream

def from_bitstream(bitstream: list, bits_per_char: int = 6):
    """Transforme une liste de bits en indices (0-63)."""
    indices = []
    for i in range(0, len(bitstream), bits_per_char):
        chunk = bitstream[i:i + bits_per_char]
        if len(chunk) < bits_per_char: break # On ignore le padding final
        val = 0
        for bit in chunk:
            val = (val << 1) | bit
        indices.append(val)
    return indices

def bitstream_to_symbols(bitstream: list, k: int):
    """Regroupe les bits par paquets de k pour la modulation."""
    # Padding : on ajoute des 0 pour que la longueur soit divisible par k
    remainder = len(bitstream) % k
    if remainder != 0:
        bitstream.extend([0] * (k - remainder))
    
    symbols = []
    for i in range(0, len(bitstream), k):
        chunk = bitstream[i:i + k]
        val = 0
        for bit in chunk:
            val = (val << 1) | bit
        symbols.append(val)
    return symbols

def symbols_to_bitstream(symbols: list, k: int):
    """Éclate les symboles reçus en flux de bits."""
    bitstream = []
    for s in symbols:
        for i in reversed(range(k)):
            bitstream.append((s >> i) & 1)
    return bitstream

# --- MODULATION GÉNÉRIQUE (M=2 à M=64) ---
def map_to_qam(symbols, m_ary, d=1.0):
    k = int(np.log2(m_ary))
    
    # Cas BPSK (M=2) : 1 bit -> 1 point sur l'axe Réel
    if m_ary == 2:
        return [d if s == 0 else -d for s in symbols for _ in range(2)] # Ajout d'un 0 imaginaire

    # Cas non-carrés (M=8, M=32) : Mapping simplifié par défaut
    # Pour faire simple, on traite comme une grille rectangulaire ou on lève une erreur
    if k % 2 != 0:
        raise ValueError(f"M={m_ary} (k={k}) nécessite une constellation non-carrée complexe.")

    m_per_axis = int(np.sqrt(m_ary))
    coords = []
    for s in symbols:
        idx_i = s >> (k // 2)
        idx_q = s & ((1 << (k // 2)) - 1)
        val_i = (2 * idx_i - (m_per_axis - 1)) * d
        val_q = (2 * idx_q - (m_per_axis - 1)) * d
        coords.extend([val_i, val_q])
    return coords

def unmap_from_qam(coords, m_ary, d=1.0):
    k = int(np.log2(m_ary))
    if m_ary == 2:
        return [0 if coords[i] > 0 else 1 for i in range(0, len(coords), 2)]

    m_per_axis = int(np.sqrt(m_ary))
    symbols = []
    for i in range(0, len(coords), 2):
        def quantize(val):
            idx = round(((val / d) + (m_per_axis - 1)) / 2)
            return max(0, min(m_per_axis - 1, idx))
        idx_i = quantize(coords[i])
        idx_q = quantize(coords[i+1])
        symbols.append((idx_i << (k // 2)) | idx_q)
    return symbols

def inverse_channel(data, transform_type):
    # (Gardé tel quel)
    data = np.asarray(data, dtype=float)
    pairs = data.reshape(-1, 2)
    a, b = pairs[:, 0], pairs[:, 1]
    if transform_type == 1: rx = np.stack([a, b], axis=1)
    elif transform_type == 2: rx = np.stack([b, -a], axis=1)
    elif transform_type == 3: rx = np.stack([-a, -b], axis=1)
    elif transform_type == 4: rx = np.stack([-b, a], axis=1)
    else: raise ValueError("Invalid transformation index.")
    return rx.flatten()