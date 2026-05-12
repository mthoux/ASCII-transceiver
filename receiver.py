import numpy as np

ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ."

def quantize(flat_list, d=2):
    data = np.asarray(flat_list)
    # On normalise par d, on arrondit à l'entier le plus proche (.5), puis on remultiplie
    # La logique : round(x/d - 0.5) + 0.5 le tout multiplié par d
    offsets = np.array([(i - 3.5) * d for i in range(8)])
    
    quantized = []
    for val in data:
        # On trouve la valeur de la grille la plus proche
        idx = np.abs(offsets - val).argmin()
        quantized.append(offsets[idx])
        
    return np.array(quantized)

def decode(quantized_data, d=2):
    offsets = [(i - 3.5) * d for i in range(8)]
    reverse_map = {(offsets[i % 8], offsets[i // 8]): char for i, char in enumerate(ALPHABET)}

    decoded_string = ""
    for i in range(0, len(quantized_data), 2):
        pair = (quantized_data[i], quantized_data[i+1])
        decoded_string += reverse_map.get(pair, "?")
    return decoded_string

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