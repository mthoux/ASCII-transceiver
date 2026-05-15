import sys
import numpy as np
import config
from channel import channel
from utils import *
import visualization

import commpy.channelcoding.convcode as cc


def transceiver(input_message_text, encoding_dict=config.classic_encoding, m_ary=4, d=1.0,):
    k = int(np.log2(m_ary)) 

    # --- CONFIGURATION DU CODE CONVOLUTIF ---
    # K=7, R=1/2. Polynômes octaux 171 et 133
    memory = np.array([6]) # K-1
    g_matrix = np.array([[0o171, 0o133]]) # 0o pour l'octal en Python
    trellis = cc.Trellis(memory, g_matrix)

    # --- TRANSMITTER ---
    # Construct signal, start with pilot
    N_PILOTS = 3
    input_pilot = [+d, +d] * N_PILOTS
    input_message_bits = to_bitstream(input_message_text, encoding_dict)

    input_message_bits = np.array([int(b) for b in input_message_bits])
    input_message_bits = cc.conv_encode(input_message_bits, trellis)
    input_message_bits = "".join(input_message_bits.astype(str))

    input_message_symbols  = bitstream_to_symbols(input_message_bits, k)
    input_message_modulate = map_to_qam(input_message_symbols, m_ary, d)
    input_signal = input_pilot + input_message_modulate

    # --- CANAL ---
    output_signal = channel(input_signal)
    
    # --- RECEIVER ---
    # Pilot analysis
    pilot_re = np.mean(output_signal[0:2*N_PILOTS:2])
    pilot_im = np.mean(output_signal[1:2*N_PILOTS:2])
    output_pilot = [pilot_re, pilot_im]
    
    if   pilot_re >= 0 and pilot_im >= 0:   t_id = 1
    elif pilot_re <  0 and pilot_im >= 0:   t_id = 2
    elif pilot_re <  0 and pilot_im <  0:   t_id = 3
    else:                                   t_id = 4

    output_message_corrected = inverse_channel(output_signal[2*N_PILOTS:], t_id)
    output_message_symbols = unmap_from_qam(output_message_corrected, m_ary, d)
    output_message_bits = symbols_to_bitstream(output_message_symbols, k)

    output_message_bits = np.array([int(b) for b in output_message_bits])
    output_message_bits = cc.viterbi_decode(output_message_bits.astype(float), trellis, decoding_type='hard')
    flush_size = memory[0]
    output_message_bits = output_message_bits[:-flush_size] if flush_size > 0 else output_message_bits
    output_message_bits = "".join(output_message_bits.astype(str))

    output_message_text = from_bitstream(output_message_bits, encoding_dict)

    # --- STATS ---
    energy = np.sum(np.array(input_signal)**2)
    energy_per_bit = energy / len(input_message_bits)
    # BIT ERROR RATE
    #bite_error_rate = ...

    # print(f"DEBUG BITS IN:  {input_message_bits[:50]}")
    # print(f"DEBUG BITS OUT: {output_message_bits[:50]}")
    # print(f"MATCH: {input_message_bits == output_message_bits}")

    return {
        "config": {
            "m_ary": m_ary,
            "k": k,
            "d": d
        },
        "input": {
            "input_pilot": input_pilot,
            "input_message_bits": input_message_bits,
            "input_message_symbols": input_message_symbols,
            "input_message_modulate": input_message_modulate,
            "input_signal": input_signal
        },
        "output": {
            "output_signal": output_signal,
            "output_pilot": output_pilot,
            "t_id": t_id,
            "output_message_corrected": output_message_corrected,
            "output_message_quantized": map_to_qam(output_message_symbols, m_ary, d),
            "output_message_symbols": output_message_symbols,
            "output_message_bits": output_message_bits,
            "output_message_text": output_message_text
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