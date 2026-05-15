import numpy as np

# --- CONVERSION TEXTE ---
def index_alphabet(char: str, alphabet: str):
    if char not in alphabet:
        raise ValueError(f"Caractère '{char}' non autorisé.")
    return alphabet.index(char) 

def reconstruct_message(indices: list, alphabet: str):
    return "".join([alphabet[i] for i in indices])


def to_bitstream(text, encoding_dict):
    """Retourne une chaîne de caractères '0' et '1'."""
    return "".join([encoding_dict[char] for char in text])

def from_bitstream(bitstream_str, encoding_dict):
    """
    Décode une chaîne de bits en texte brut via un dictionnaire variable.
    """
    # Inversion du dictionnaire pour la recherche
    reverse_dict = {v: k for k, v in encoding_dict.items()}
    
    decoded_text = ""
    current_buffer = ""
    
    # On parcourt chaque caractère '0' ou '1' de la chaîne
    for bit in bitstream_str:
        current_buffer += bit 
        
        if current_buffer in reverse_dict:
            decoded_text += reverse_dict[current_buffer]
            current_buffer = "" 
            
    return decoded_text

def bitstream_to_symbols(bitstream_str: str, k: int):
    """Regroupe par paquets de k. Lève une erreur si le compte n'est pas bon."""
    if len(bitstream_str) % k != 0:
        raise ValueError(f"Bitstream length ({len(bitstream_str)}) is not a multiple of k={k}.")
    
    symbols = []
    for i in range(0, len(bitstream_str), k):
        chunk = bitstream_str[i:i + k]
        symbols.append(int(chunk, 2))
    return symbols

def bitstream_to_symbols(bitstream_list: list, k: int):
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

def symbols_to_bitstream(symbols: list, k: int):
    return "".join([format(s, 'b').zfill(k) for s in symbols])

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


def bitstream_to_symbols_str(bitstream_str: str, k: int):
    """Regroupe une chaîne de caractères binaire par paquets de k."""
    if len(bitstream_str) % k != 0:
        raise ValueError(f"Bitstream length ({len(bitstream_str)}) is not a multiple of k={k}.")
    
    symbols = []
    for i in range(0, len(bitstream_str), k):
        chunk = bitstream_str[i:i + k]
        symbols.append(int(chunk, 2))
    return symbols

def bitstream_to_symbols_list(bitstream_list: list, k: int):
    """Regroupe une liste de bits (0 et 1) par paquets de k."""
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

def map_to_4qam_custom(bitstream, d=1.0):
    """
    Prend en entrée un bitstream (str ou list), le convertit en symboles (k=2)
    et applique le mapping personnalisé sous forme de paires [[I, Q], ...] :
    00 -> [d, d]
    01 -> [d, -d]
    10 -> [-d, d]
    11 -> [-d, -d]
    """
    # Étape 1 : Détection automatique du type de bitstream et conversion en symboles (k=2)
    if isinstance(bitstream, str):
        symbols = bitstream_to_symbols_str(bitstream, k=2)
    elif isinstance(bitstream, list):
        symbols = bitstream_to_symbols_list(bitstream, k=2)
    else:
        raise TypeError("Le bitstream doit être une chaîne de caractères (str) ou une liste (list).")

    # Étape 2 : Mapping vers la constellation
    paires_coordonnees = []
    for s in symbols:
        bit_gauche = (s >> 1) & 1  # Premier bit
        bit_droite = s & 1         # Deuxième bit
        
        val_i = d if bit_gauche == 0 else -d
        val_q = d if bit_droite == 0 else -d
        
        # On stocke sous forme de paire [I, Q] bien propre
        paires_coordonnees.append([val_i, val_q])
        
    return paires_coordonnees

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