import sys
import numpy as np
import config
from channel import channel
from utils import *
import visualization
import conv_code

def pilot_analysis(signal):

    pilot_re = np.mean(signal[0::2])
    pilot_im = np.mean(signal[1::2])
    
    if   pilot_re >= 0 and pilot_im >= 0:   t_id = 1
    elif pilot_re <  0 and pilot_im >= 0:   t_id = 2
    elif pilot_re <  0 and pilot_im <  0:   t_id = 3
    else:                                   t_id = 4

    return t_id, (pilot_re, pilot_im)


def transceiver(input_text, encoding_dict, d, n_pilot):

    K=7  
    G=[0o171,0o133]

    # --- TRANSMITTER ---
    # Construct signal, start with pilot
    input_pilot = [+d, +d] * n_pilot

    # Source coding
    input_bits = to_bitstream(input_text, encoding_dict)
    input_encoded = conv_code.encode(input_bits, K, G)
    input_modulate = map_to_4qam(input_encoded, d)
    input_signal = input_pilot + input_modulate

    # --- CANAL ---
    output_signal = channel(input_signal)
    
    # --- RECEIVER ---
    # Pilot analysis
    t_id, output_pilot = pilot_analysis(output_signal[0:2*n_pilot])
    output_corrected = inverse_channel(output_signal[2*n_pilot:], t_id)

    grouped_for_viterbi = [
        output_corrected[i : i + len(G)] 
        for i in range(0, len(output_corrected), len(G))
    ]
    
    output_bits = conv_code.decode(grouped_for_viterbi, K, G, d)
    output_text = from_bitstream(output_bits, encoding_dict)

    # --- STATS ---
    energy = np.sum(np.array(input_signal)**2)
    energy_per_bit = energy / len(input_encoded)
    # BIT ERROR RATE
    error = np.sum([1 for i, j in zip(input_bits, output_bits) if i != j])
    bit_error_rate = error/len(input_bits)

    return {
        "config": {
            "d": d
        },
        "input": {
            "input_text": input_text,
            "input_pilot": input_pilot,
            "input_bits": input_bits,
            "input_modulate": input_modulate,
            "input_signal": input_signal
        },
        "output": {
            "output_signal": output_signal,
            "output_pilot": output_pilot,
            "t_id": t_id,
            "output_corrected": output_corrected,
            "output_bits": output_bits,
            "output_text": output_text
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
    res = transceiver(msg, config.classic_encoding, d=config.D_SPACING, n_pilot=4)

    visualization.display_diagnostics(res)