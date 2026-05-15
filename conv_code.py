import numpy as np

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

        # Compute codewords
        full_register = [entry_bit] + current_state_bits
        
        for j in range(len(G)):
            res_xor = 0
            for bit_pos in range(k):
                # Check if bit at bit_pos in G is 1
                if (G[j] >> (k - 1 - bit_pos)) & 1:
                    res_xor ^= full_register[bit_pos]
            
            matrice[i, 2*state_length + 1 + j] = res_xor

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

    curr_list = [None]* n_states
    next_list = [None]* n_states

    curr_list[0] = {"cost": 0, "path": []}

    for idx,(i,j) in enumerate(received_signal):

        # Create next_list
        for curr in curr_list:
            
            # Get next state for bit 0
            next = NS[curr, 0]
            
            # Compute cost to that path
            cost = curr["cost"] + (i - OS[next, 0][0])^2 + (j - OS[next, 0][1])

            # Create path 
            path = curr[path] + f"{next:0{k-1}b}"

            # Compare
            if curr_list[next] is None: next_list[next] = {"cost": cost, "path": path}
            elif curr_list[next]["cost"] > cost: next_list[next] = {"cost": cost, "path": path}
            else: next_list[next] = curr_list[next]

            if(idx < len(received_signal) - n_flush_bits):

                # Get next state for bit 1
                next = NS[curr, 1]
                
                # Compute cost to that path
                cost = curr["cost"] + (i - OS[next, 1][0])**2 + (j - OS[next, 1][1])**2

                # Create path 
                path = curr["path"] + f"{next:0{k-1}b}"

                # Compare
                if curr_list[next] is None: next_list[next] = {"cost": cost, "path": path}
                elif curr_list[next]["cost"] > cost: next_list[next] = {"cost": cost, "path": path}
                else: next_list[next] = curr_list[next]

        # Update list
        curr_list = next_list

    # Output path with state 0

    return curr_list[0]["path"]






def soft_viterbi(symbols, k):
    # 1. Ton treillis (Prends bien soin de vérifier les sorties selon G)
    treillis = {
        "00": {0: ("00", ( 2,  2)), 1: ("10", (-2, 2))},
        "10": {0: ("01", (-2, -2)), 1: ("11", ( 2, -2))},
        "01": {0: ("00", ( 2,  2)), 1: ("10", (-2, 2))}, 
        "11": {0: ("01", (-2, -2)), 1: ("11", ( 2, -2))},
    }

    # 2. Initialisation : { "état": (distance_cumulée, "chemin_de_bits") }
    # On commence forcément à "00" avec une distance de 0
    states = {"00": (0, "")}

    # 3. Boucle sur chaque symbole reçu
    for i, sym_r in enumerate(symbols):
        temp = {} # Dictionnaire pour merger les chemins à cette itération
        
        # On gère le flush : si on est à la fin, on ne teste que l'entrée 0
        is_flush = i >= (len(symbols) - (k-1))
        inputs = [0] if is_flush else [0, 1]

        # 4. Pour chaque état "survivant" de l'étape précédente
        for state_actuel, (dist_cumulee, path) in states.items():
            for bit_in in inputs:
                # Récupération de la transition
                next_state, sym_t = treillis[state_actuel][bit_in]
                
                # Calcul de la distance euclidienne (Maths)
                dist_b = (sym_r[0] - sym_t[0])**2 + (sym_r[1] - sym_t[1])**2
                total_dist = dist_cumulee + dist_b
                new_path = path + str(bit_in)

                # 5. LE MERGE (Add-Compare-Select)
                # Si l'état de destination n'a pas encore de chemin OU si le nouveau est meilleur
                if next_state not in temp or total_dist < temp[next_state][0]:
                    temp[next_state] = (total_dist, new_path)
        
        # On remplace les anciens états par les nouveaux survivants
        states = temp

    # 6. Résultat final : le chemin associé à l'état "00" après le flush
    return states["00"][1]

# Exemple d'utilisation
points_recus = [(1.5, 1.7), (-1.8, 1.9), (-2.1, -2.0), (1.9, 2.1)]
resultat = soft_viterbi(points_recus, 3)
print(f"Message décodé : {resultat}")