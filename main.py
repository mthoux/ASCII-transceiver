import sys
import numpy as np
from transmitter import encode
from channel import channel
from receiver import decode, inverse_channel, quantize

def print_header(title):
    print(f"\n{'='*65}")
    print(f" {title.center(63)}")
    print(f"{'='*65}")

def print_line():
    print("-" * 65)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python main.py [message string]")

    msg_input = sys.argv[1]
    D_SPACING = 2  # Distance between constellation points

    # --- TRANSMISSION PREPARATION ---
    # Create a known pilot point (e.g., [15, 15] if D=10)
    pilot_sent = [1.5 * D_SPACING, 1.5 * D_SPACING]
    # Encode the message into QAM symbols
    tx_data = encode(msg_input, d=D_SPACING)
    
    # Concatenate Pilot + Data to ensure they undergo the SAME random rotation
    full_tx = pilot_sent + tx_data
    
    # --- SINGLE CHANNEL CALL ---
    # This prevents the pilot and data from having different rotation IDs
    full_rx = channel(full_tx)
    
    # --- EXTRACTION & DIAGNOSTICS ---
    # Pilot is at the first two positions
    p_re, p_im = full_rx[0], full_rx[1]
    # The rest is our noisy message
    rx_data = full_rx[2:]
    
    # Detect rotation ID based on pilot quadrant
    if p_re >= 0 and p_im >= 0:   t_id = 1
    elif p_re < 0 and p_im >= 0:  t_id = 2
    elif p_re < 0 and p_im < 0:   t_id = 3
    else:                         t_id = 4

    # --- MESSAGE PROCESSING ---
    # Reverse the detected rotation
    corrected_data = inverse_channel(rx_data, t_id)
    # Snap noisy floats to the nearest grid points
    quantized_data = quantize(corrected_data, d=D_SPACING)
    # Map grid points back to characters
    decoded_msg = decode(quantized_data, d=D_SPACING)

    # --- RESULTS DISPLAY ---
    print_header("CHANNELS DIAGNOSTICS (PILOT)")
    print(f"{'Spacing (d)':<20}: {D_SPACING}")
    print(f"{'Pilot Received':<20}: [{p_re:.2f}, {p_im:.2f}]")
    print(f"{'Detected Rotation':<20}: ID {t_id}")

    print_header("TRANSMISSION SUMMARY")
    print(f"{'Original Message':<20}: {msg_input}")
    print(f"{'Decoded Message':<20}: {decoded_msg}")
    print_line()
    
    print(f"{'TYPE':<12} | {'SYMBOLS (Real, Imag)':<45}")
    print_line()
    
    # Format points for side-by-side comparison
    tx_pts = [f"({tx_data[i]:.0f},{tx_data[i+1]:.0f})" for i in range(0, len(tx_data), 2)]
    rx_pts = [f"({rx_data[i]:.1f},{rx_data[i+1]:.1f})" for i in range(0, len(rx_data), 2)]
    cx_pts = [f"({corrected_data[i]:.1f},{corrected_data[i+1]:.1f})" for i in range(0, len(corrected_data), 2)]
    qx_pts = [f"({quantized_data[i]:.0f},{quantized_data[i+1]:.0f})" for i in range(0, len(quantized_data), 2)]

    print(f"{'TX (Sent)':<12} | {' '.join(tx_pts[:5])} ...")
    print(f"{'RX (Recv)':<12} | {' '.join(rx_pts[:5])} ...")
    print(f"{'CX (Corr)':<12} | {' '.join(cx_pts[:5])} ...")
    print(f"{'QX (Quant)':<12} | {' '.join(qx_pts[:5])} ...")
    print_line()
    
    # Energy calculated on the full transmitted signal
    total_energy = np.sum(np.array(full_tx)**2)
    print(f"{'TOTAL ENERGY':<20}: {total_energy:.2f}")
    print_header("END OF PROCESS")