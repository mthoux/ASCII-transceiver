import sys
import numpy as np
import config
from channel import channel
from utils import *
import visualization

import commpy.channelcoding.convcode as cc


def transceiver(input_text, encoding_dict=config.classic_encoding, m_ary=4, d=1.0, n_pilot = 3):
    k = int(np.log2(m_ary)) 

    # --- CONFIGURATION DU CODE CONVOLUTIF ---
    # K=7, R=1/2. Polynômes octaux 171 et 133
    memory = np.array([6]) # K-1
    g_matrix = np.array([[0o171, 0o133]]) # 0o pour l'octal en Python
    trellis = cc.Trellis(memory, g_matrix)

    # --- TRANSMITTER ---
    # Construct signal, start with pilot
    input_pilot = [+d, +d] * n_pilot

    # Source coding
    input_bits = to_bitstream(input_text, encoding_dict)

    # Channel coding
    input_encoded = np.array([int(b) for b in input_bits])
    input_encoded = cc.conv_encode(input_encoded, trellis)
    input_encoded = "".join(input_encoded.astype(str))

    # Modulation
    input_symbols  = bitstream_to_symbols(input_encoded, k)
    input_modulate = map_to_qam(input_symbols, m_ary, d)
    input_signal = input_pilot + input_modulate

    # --- CANAL ---
    output_signal = channel(input_signal)
    
    # --- RECEIVER ---
    # Pilot analysis
    pilot_re = np.mean(output_signal[0:2*n_pilot:2])
    pilot_im = np.mean(output_signal[1:2*n_pilot:2])
    output_pilot = [pilot_re, pilot_im]
    
    if   pilot_re >= 0 and pilot_im >= 0:   t_id = 1
    elif pilot_re <  0 and pilot_im >= 0:   t_id = 2
    elif pilot_re <  0 and pilot_im <  0:   t_id = 3
    else:                                   t_id = 4

    output_message_corrected = inverse_channel(output_signal[2*n_pilot:], t_id)

    # Au lieu de unmap_from_qam qui donne des 0/1, on extrait la valeur "brute"
    # Pour la 4-QAM, la partie Réelle porte un bit, l'Imaginaire porte l'autre.
    soft_bits = []
    for i in range(0, len(output_message_corrected), 2):
        re = output_message_corrected[i]
        im = output_message_corrected[i+1]
        # On normalise : si c'est positif, c'est proche du bit '0'
        # Si c'est négatif, c'est proche du bit '1'
        # Commpy attend des valeurs où le signe et la magnitude indiquent la confiance
        soft_bits.append(re) 
        soft_bits.append(im)

    soft_bits = np.array(soft_bits)

    # On décode en mode SOFT
    # Attention : il faut parfois inverser le signe (soft_bits * -1) 
    # selon comment ton to_bitstream a mappé le 0 et le 1.
    output_bits = cc.viterbi_decode(soft_bits, trellis, decoding_type='soft')
    
    #output_message_symbols = unmap_from_qam(output_message_corrected, m_ary, d)
    #output_message_bits = symbols_to_bitstream(output_message_symbols, k)

    #output_message_bits = np.array([int(b) for b in output_message_bits])
    #output_message_bits = cc.viterbi_decode(output_message_bits.astype(float), trellis, decoding_type='hard')
    flush_size = memory[0]
    output_bits = output_bits[:-flush_size] if flush_size > 0 else output_bits
    output_bits = "".join(output_bits.astype(str))

    output_text = from_bitstream(output_bits, encoding_dict)

    # --- Pour que tes diagnostics de fin fonctionnent toujours ---
    # On recrée les symboles quantifiés juste pour l'affichage
    output_message_symbols = unmap_from_qam(output_message_corrected, m_ary, d)

    # --- STATS ---
    energy = np.sum(np.array(input_signal)**2)
    energy_per_bit = energy / len(input_encoded)
    # BIT ERROR RATE
    error = np.sum([1 for i, j in zip(input_bits, output_bits) if i != j])
    bit_error_rate = error/len(input_bits)

    print(f"Bit error rate: {bit_error_rate}")

    print(f"DEBUG BITS IN:  {input_bits[:50]}")
    print(f"DEBUG BITS OUT: {output_bits[:50]}")
    print(f"MATCH: {input_bits == output_bits}")

    return {
        "config": {
            "m_ary": m_ary,
            "k": k,
            "d": d
        },
        "input": {
            "input_pilot": input_pilot,
            "input_message_bits": input_bits,
            "input_message_symbols": input_symbols,
            "input_message_modulate": input_modulate,
            "input_signal": input_signal
        },
        "output": {
            "output_signal": output_signal,
            "output_pilot": output_pilot,
            "t_id": t_id,
            "output_message_corrected": output_message_corrected,
            "output_message_quantized": map_to_qam(output_message_symbols, m_ary, d),
            "output_message_symbols": output_message_symbols,
            "output_message_bits": output_bits,
            "output_message_text": output_text
        },
        "stats": {
            "energy": energy,
            "energy_per_bit": energy_per_bit
        }
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py 'message'")
        sys.exit()

    msg = sys.argv[1]
    res = transceiver(msg, config.classic_encoding, m_ary=config.M_ARY, d=config.D_SPACING)
    
    visualization.display_diagnostics(msg, res)
    #visualization.plot_data(res)