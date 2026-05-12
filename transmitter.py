import numpy as np

ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ."

def encode(message, d=2):
    # Les multiplicateurs pour une grille 8x8 sont [-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5]
    # On multiplie par d pour obtenir l'espacement voulu
    offsets = [(i - 3.5) * d for i in range(8)]
    
    qam_map = {}
    for i, char in enumerate(ALPHABET):
        qam_map[char] = (offsets[i % 8], offsets[i // 8])

    if isinstance(message, list):
        return [float(v) for v in message]
        
    encoded_list = []
    for char in message:
        real, imag = qam_map.get(char, (0, 0))
        encoded_list.extend([float(real), float(imag)])
    
    return encoded_list