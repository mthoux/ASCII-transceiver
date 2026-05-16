import sys
import numpy as np
import src.config as config
from src.channel import channel
from src.utils import *
import src.tools.visualization as visualization
import src.convolutional_code as convolutional_code

def transceiver(input_text, encoding_dict, d, n_pilot, K, G):

    # --- TRANSMITTER ---
    # Construct signal, start with pilot
    input_pilot         = [+d, +d] * n_pilot
    input_bits          = to_bitstream(input_text, encoding_dict)               # Source coding
    input_encoded       = convolutional_code.encode(input_bits, K, G)           # Channel coding
    input_modulate      = map_to_4qam(input_encoded, d)                         # Modulation
    input_signal        = input_pilot + input_modulate                          # Create signal

    # --- CHANNEL ---
    output_signal = channel(input_signal)                                       # Send signal trough channel
    
    # --- RECEIVER ---
    t_id, output_pilot  = pilot_analysis(output_signal[0:2*n_pilot])            # Pilot analysis
    output_corrected    = rotate_signal(output_signal[2*n_pilot:], t_id)        # Rotate signal
    output_bits         = convolutional_code.decode(output_corrected, K, G, d)  # Decode
    output_text         = from_bitstream(output_bits, encoding_dict)            # Reconstruct string

    # --- STATS ---
    energy = np.sum(np.array(input_signal)**2)
    energy_per_bit = energy / len(input_encoded)
    error = np.sum([1 for i, j in zip(input_bits, output_bits) if i != j])
    bit_error_rate = error/len(input_bits)

    return {
        "config": {
            "d": d,
            "n_pilot": n_pilot
        },
        "input": {
            "text": input_text,
            "pilot": input_pilot,
            "bits": input_bits,
            "modulate": input_modulate,
            "signal": input_signal
        },
        "output": {
            "signal": output_signal,
            "t_id": t_id,
            "corrected": output_corrected,
            "bits": output_bits,
            "pilot": output_pilot,
            "text": output_text
        },
        "stats": {
            "energy": energy,
            "energy_per_bit": energy_per_bit,
            "bit_error_rate": bit_error_rate
        }
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py 'message'")
        sys.exit()

    msg = sys.argv[1]
    res = transceiver(msg, 
                      config.ENCODING, 
                      d=config.D_SPACING, 
                      n_pilot=config.N_PILOT, 
                      K=config.K, 
                      G=config.G)

    visualization.display_diagnostics(res)
    visualization.plot_constellations(res)