ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ."

def encode(ASCII_string):
    points = [-7, -5, -3, -1, 1, 3, 5, 7]
    qam_map = {}
    
    for i, char in enumerate(ALPHABET):
        qam_map[char] = (points[i % 8], points[i // 8])

    encoded_list = []
    for char in ASCII_string:
        real, imag = qam_map.get(char, (0, 0))
        encoded_list.append(float(real))
        encoded_list.append(float(imag))

    return encoded_list