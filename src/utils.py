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

def pilot_analysis(signal):
    pilot_re = np.mean(signal[0::2])
    pilot_im = np.mean(signal[1::2])
    
    if pilot_re >= 0:
        t_id = 1 if pilot_im >= 0 else 4
    else:
        t_id = 2 if pilot_im >= 0 else 3
        
    return t_id, (pilot_re, pilot_im)