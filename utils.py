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

def unmap_from_4qam(coords):

    symbols = []
    for i in range(0, len(coords), 2):
        I = coords[i]
        Q = coords[i+1]
        
        b1 = 1 if I < 0 else 0
        b0 = 1 if Q < 0 else 0
        
        symbols.append((b1 << 1) | b0)
        
    return symbols