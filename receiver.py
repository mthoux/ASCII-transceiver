ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ."

def decode(flat_list):
    points = [-7, -5, -3, -1, 1, 3, 5, 7]
    reverse_map = {}
    
    for i, char in enumerate(ALPHABET):
        real = points[i % 8]
        imag = points[i // 8]
        reverse_map[(real, imag)] = char

    decoded_string = ""
    
    for i in range(0, len(flat_list), 2):

        r_val = flat_list[i]
        i_val = flat_list[i+1] if (i+1) < len(flat_list) else 0

        r_grid = int(round((r_val - 1) / 2) * 2 + 1)
        i_grid = int(round((i_val - 1) / 2) * 2 + 1)
        
        r_grid = max(-7, min(7, r_grid))
        i_grid = max(-7, min(7, i_grid))
        
        decoded_string += reverse_map.get((r_grid, i_grid), "?")

    return decoded_string