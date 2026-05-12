import sys
import numpy as np
import config
from channel import channel
from utils import *
import visualization


def transceiver(input_message_text, m_ary=4, d=1.0):
    k = int(np.log2(m_ary)) 

    # --- TRANSMITTER ---
    # Construct signal, start with pilot
    input_pilot = [+d, +d]
    input_message_numbers  = construct_list(input_message_text, config.ALPHABET)
    input_message_bits     = to_bitstream(input_message_numbers, bits_per_char=6)
    input_message_symbols  = bitstream_to_symbols(input_message_bits, k)
    input_message_modulate = map_to_qam(input_message_symbols, m_ary, d)
    input_signal = input_pilot + input_message_modulate

    # --- CANAL ---
    output_signal = channel(input_signal)
    
    # --- RECEIVER ---
    # Pilot analysis
    output_pilot = output_signal[0:2]
    pilot_re, pilot_im = output_pilot[0], output_pilot[1]
    
    if   pilot_re >= 0 and pilot_im >= 0:   t_id = 1
    elif pilot_re <  0 and pilot_im >= 0:   t_id = 2
    elif pilot_re <  0 and pilot_im <  0:   t_id = 3
    else:                                   t_id = 4

    output_message_corrected = inverse_channel(output_signal[2:], t_id)
    output_message_symbols = unmap_from_qam(output_message_corrected, m_ary, d)
    output_message_bits = symbols_to_bitstream(output_message_symbols, k)
    output_message_numbers = from_bitstream(output_message_bits, bits_per_char=6)
    output_message_text = reconstruct_message(output_message_numbers, config.ALPHABET)

    # --- STATS ---
    energy = np.sum(np.array(input_signal)**2)

    return {
        "config": {
            "m_ary": m_ary,
            "k": k,
            "d": d
        },
        "input": {
            "input_pilot": input_pilot,
            "input_message_numbers": input_message_numbers,
            "input_message_bits": input_message_bits,
            "input_message_symbols": input_message_symbols,
            "input_message_modulate": input_message_modulate,
            "input_signal": input_signal
        },
        "output": {
            "output_pilot": output_pilot,
            "t_id": t_id,
            "output_message_corrected": output_message_corrected,
            "output_message_quantized": map_to_qam(output_message_symbols, m_ary, d),
            "output_message_symbols": output_message_symbols,
            "output_message_bits": output_message_bits,
            "output_message_numbers": output_message_numbers,
            "output_message_text": output_message_text
        },
        "stats": {
            "energy": energy
        }
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py 'message'")
        sys.exit()

    msg = sys.argv[1]
    # On capture le dictionnaire retourné par le transceiver
    res = transceiver(msg, m_ary=config.M_ARY, d=config.D_SPACING)
    
    # On appelle la nouvelle fonction d'affichage
    visualization.display_diagnostics(msg, res)