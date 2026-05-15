import numpy as np
import utils

def _compute_xor(table, g):
    k = len(table)

    result = 0
    for i in range(k):
        if (g >> i) & 1:
            result ^= table[k - 1 - i]

    return result

def encode_bits(message, k, G):

    string = [0] * (k - 1) + message + [0] * (k - 1)
    result = []

    for i in range(len(message) + k - 1):
        window = string[i:i+k]

        for g in G:
            result.append(_compute_xor(window, g))

    return result

def create_sub_matrice(entry_bit, k, G):
    n_states = 2**(k-1)
    state_length = k-1
    entry_length = 2*state_length + len(G) + 1
    
    matrice = np.zeros((n_states, entry_length), dtype=int)

    for i in range(n_states):
        # Set entry bit
        matrice[i, 0] = entry_bit

        # Fill current state
        current_state_bits = [(i >> (state_length - 1 - j)) & 1 for j in range(state_length)]
        matrice[i, 1:state_length+1] = current_state_bits

        # Fill next state
        next_state = [entry_bit] + current_state_bits[:-1]
        matrice[i, state_length+1 : 2*state_length+1] = next_state

        # Le registre complet (qui sert de table/fenêtre)
        full_register = [entry_bit] + current_state_bits
        
        # On utilise directement la fonction _compute_xor
        for j in range(len(G)):
            matrice[i, 2*state_length + 1 + j] = _compute_xor(full_register, G[j])

    return matrice

def create_treillis(k, G, d):
    matrice0 = create_sub_matrice(0, k, G)
    matrice1 = create_sub_matrice(1, k, G)
    
    n_states = 2**(k-1)
    state_length = k-1
    
    # NS : Next State matrix
    NS = np.zeros((n_states, 2), dtype=int)
    
    # OS : Output Symbols matrix
    OS = np.zeros((n_states, 2, len(G)))

    for i in range(n_states):
        # Conversion des bits de "next state" en index entier (0, 1, 2...)
        bits_next_0 = matrice0[i, state_length+1 : 2*state_length+1]
        NS[i, 0] = int("".join(map(str, bits_next_0)), 2)
        
        bits_next_1 = matrice1[i, state_length+1 : 2*state_length+1]
        NS[i, 1] = int("".join(map(str, bits_next_1)), 2)
        
        # Conversion des bits de sortie en tensions réelles
        # Si bit = 0 -> +d
        # Si bit = 1 -> -d
        OS[i, 0] = [d if b == 0 else -d for b in matrice0[i, -len(G):]]
        OS[i, 1] = [d if b == 0 else -d for b in matrice1[i, -len(G):]]
        
    return NS, OS

def soft_viterbi(received_signal, k, G, d):
    NS, OS = create_treillis(k, G, d)
    n_states = 2**(k-1)
    n_flush_bits = k-1

    curr_list = [None] * n_states
    curr_list[0] = {"cost": 0, "path": ""}

    for idx, received_symbols in enumerate(received_signal):
        next_list = [None] * n_states
        
        for s in range(n_states):
            if curr_list[s] is None:
                continue
            
            # Try input 0 and 1 but only 0 when flushing
            possible_inputs = [0] if idx >= len(received_signal) - n_flush_bits else [0, 1]
            
            for bit in possible_inputs:
                next_state = NS[s, bit]
                expected_output = OS[s, bit]
                
                # Euclidean distance: sum of (received - expected)^2
                branch_cost = sum((received_symbols[c] - expected_output[c])**2 
                                  for c in range(len(G)))
                
                new_cost = curr_list[s]["cost"] + branch_cost
                new_path = curr_list[s]["path"] + str(bit)
                
                # Selection (Add-Compare-Select)
                if next_list[next_state] is None or new_cost < next_list[next_state]["cost"]:
                    next_list[next_state] = {"cost": new_cost, "path": new_path}
        
        curr_list = next_list

    # Return the path ending in state 0 (standard for terminated codes)
    # If state 0 is unreachable for some reason, fallback to the minimum cost state
    if curr_list[0] is not None:
        return curr_list[0]["path"]
    
    # Fallback to absolute minimum cost
    valid_paths = [item for item in curr_list if item is not None]
    return min(valid_paths, key=lambda x: x["cost"])["path"]





# --- Test rapide ---
G_test = [5, 7] # G = [7, 5]
K = 3
d = 1 
msg = [1, 1, 1, 0, 1, 1 ,1, 0, 0, 0, 1, 1, 1, 0, 1, 1 ,1, 0, 0, 0]
signal_genere = encode_bits(msg, K, G_test)
print(signal_genere)

signal = utils.map_to_4qam_custom(signal_genere, d)

print(signal)

resultat = soft_viterbi(signal, K, G_test, d)
#rm flush bits :
resultat = resultat[:-(K-1)]

print(f"Message envoyé: {''.join(str(b) for b in msg)}")
print(f"Message décodé: {resultat}")
