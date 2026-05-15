import numpy as np

def to_bitstream(text, encoding_dict):
    """Retourne une liste d'entiers (0 et 1)."""
    return [int(bit) for char in text for bit in encoding_dict[char]]

def from_bitstream(bitstream_array, encoding_dict):
    """
    Décode un TABLEAU de bits numériques (ex: [1, 0, 1, 1]) 
    en texte brut via un dictionnaire variable.
    """
    # Inversion du dictionnaire pour la recherche (on garde les clés en string '0101...')
    reverse_dict = {v: k for k, v in encoding_dict.items()}
    
    decoded_text = ""
    current_buffer = ""
    
    # On parcourt directement le tableau d'entiers
    for bit in bitstream_array:
        # On convertit le int (0 ou 1) en str ('0' ou '1') pour le buffer
        current_buffer += str(bit) 
        
        if current_buffer in reverse_dict:
            decoded_text += reverse_dict[current_buffer]
            current_buffer = "" 
            
    return decoded_text

def _bitstream_to_symbols(bitstream_list: list, k: int):
    """Regroupe un tableau de bits par paquets de k. Lève une erreur si le compte n'est pas bon."""
    if len(bitstream_list) % k != 0:
        raise ValueError(f"Bitstream length ({len(bitstream_list)}) is not a multiple of k={k}.")
    
    symbols = []
    for i in range(0, len(bitstream_list), k):
        chunk = bitstream_list[i:i + k]
        
        # Convertit la liste de bits [1, 0, 1] en entier (ex: 5)
        valeur = 0
        for bit in chunk:
            # On décale vers la gauche et on ajoute le bit actuel
            valeur = (valeur << 1) | bit
            
        symbols.append(valeur)
        
    return symbols

def map_to_4qam(bitstream: list[int], d: float = 1.0) -> list[float]:
    """
    Mapping 4-QAM (QPSK).
      00 → [+d, +d]   01 → [+d, -d]
      10 → [-d, +d]   11 → [-d, -d]
    """
    symbols = _bitstream_to_symbols(bitstream, k=2)
    return [
        coord
        for s in symbols
        for coord in (d if ((s >> 1) & 1) == 0 else -d, d if (s & 1) == 0 else -d)
    ]

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