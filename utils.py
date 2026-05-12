import numpy as np

def index_alphabet(char: str, alphabet: str):
    if char not in alphabet:
        raise ValueError(f"Le caractère '{char}' n'est pas dans l'alphabet autorisé.")
    return alphabet.index(char) 

def construct_list(message: str, alphabet: str):
    return [index_alphabet(char, alphabet) for char in message]

def reconstruct_message(indices: list, alphabet: str):
    return "".join([alphabet[i] for i in indices])

def split_6bits_in(x: int, bits_per_group: int):
    if not (0 <= x <= 63):
        raise ValueError("Must have 0 <= x <= 63")
    if 6 % bits_per_group != 0:
        raise ValueError("6 must be divisible by bits_per_group")
    
    nb_groups = 6 // bits_per_group
    mask = (1 << bits_per_group) - 1
    
    # reversed list to ensure order MSB to LSB
    return [(x >> (bits_per_group * i)) & mask for i in reversed(range(nb_groups))]

def split_6bits_list_in(x_list: list, bits_per_group: int):
    return [
        val 
        for n in x_list 
        for val in split_6bits_in(n, bits_per_group)
    ]

def rebuild_6bits_from(symbols: list, bits_per_group: int):
    nb_groups = 6 // bits_per_group
    if len(symbols) != nb_groups:
        raise ValueError(f"Need {nb_groups} symbols to 6 bits.")
    
    x = 0

    # First symbol is MSB
    for i, s in enumerate(symbols):
        shift = bits_per_group * (nb_groups - 1 - i)
        x |= (s << shift)
    return x

def rebuild_6bits_list_from(symbols_list: list, bits_per_group: int):
    nb_groups = 6 // bits_per_group
    return [
        rebuild_6bits_from(symbols_list[i : i + nb_groups], bits_per_group)
        for i in range(0, len(symbols_list), nb_groups)
    ]   

def map_to_4qam(symbols, d):
    # Mapping simple : 
    # bit 1 -> signe de I, bit 0 -> signe de Q
    mapping = {
        0: [+d, +d], # 00
        1: [-d, +d], # 01
        2: [+d, -d], # 10
        3: [-d, -d]  # 11
    }
    return [coord for s in symbols for coord in mapping[s]]

import numpy as np

def map_to_qam(symbols, m_ary, d=1.0):
    """
    Mapping QAM générique pour M = 4, 16, 64...
    """
    k = int(np.log2(m_ary))
    if k % 2 != 0:
        raise ValueError("Cette fonction simplifiée ne gère que les constellations carrées (4, 16, 64...).")

    # Nombre de niveaux par axe (ex: 4 pour le 16-QAM)
    m_per_axis = int(np.sqrt(m_ary))
    
    coords = []
    for s in symbols:
        # On sépare le symbole en deux indices (I et Q)
        idx_i = s >> (k // 2)
        idx_q = s & ((1 << (k // 2)) - 1)
        
        # Conversion d'index en amplitude (ex pour M=16 : -3d, -d, d, 3d)
        val_i = (2 * idx_i - (m_per_axis - 1)) * d
        val_q = (2 * idx_q - (m_per_axis - 1)) * d
        
        coords.extend([val_i, val_q])
    return coords

def unmap_from_qam(coords, m_ary, d=1.0):
    k = int(np.log2(m_ary))
    m_per_axis = int(np.sqrt(m_ary))
    
    symbols = []
    for i in range(0, len(coords), 2):
        # On quantifie les valeurs reçues vers les niveaux théoriques
        # Formule inverse du mapping pour retrouver l'index
        def quantize(val):
            idx = round(((val / d) + (m_per_axis - 1)) / 2)
            return max(0, min(m_per_axis - 1, idx))
        
        idx_i = quantize(coords[i])
        idx_q = quantize(coords[i+1])
        
        symbols.append((idx_i << (k // 2)) | idx_q)
    return symbols