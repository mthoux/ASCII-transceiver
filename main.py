import sys
import numpy as np
import config
from transmitter import encode
from channel import channel
from receiver import decode, inverse_channel, quantize

def run_pipeline(msg_input, d=config.D_SPACING):
    """Logique stable pour test.py et usage manuel."""
    msg_original = msg_input.ljust(config.MSG_LEN)[:config.MSG_LEN]
    
    # 1. Pilot (1.5x pour la robustesse) + Data
    pilot_sent = [1.5 * d, 1.5 * d]
    tx_data = encode(msg_original, d=d)
    full_tx = pilot_sent + tx_data
    
    # 2. Channel
    energy = np.sum(np.array(full_tx)**2)
    full_rx = channel(full_tx)
    
    # 3. Pilot Analysis
    p_re, p_im = full_rx[0], full_rx[1]
    rx_data = full_rx[2:]
    
    if p_re >= 0 and p_im >= 0:   t_id = 1
    elif p_re < 0 and p_im >= 0:  t_id = 2
    elif p_re < 0 and p_im < 0:   t_id = 3
    else:                         t_id = 4

    # 4. Recovery
    corrected = inverse_channel(rx_data, t_id)
    quantized = quantize(corrected, d=d)
    decoded_msg = decode(quantized, d=d)

    # RETOUR STRICTEMENT IDENTIQUE POUR TEST.PY
    return {
        "decoded": decoded_msg,
        "energy": energy,
        "n": len(full_tx),
        "t_id": t_id,
        "success": decoded_msg == msg_original,
        # Données bonus pour l'affichage manuel
        "pilot_rx": [p_re, p_im],
        "points": {"tx": tx_data, "rx": rx_data, "cx": corrected, "qx": quantized}
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py 'message'")
        sys.exit()

    msg = sys.argv[1]
    res = run_pipeline(msg)

    # --- LE SUPER AFFICHAGE ---
    def sep(): print("-" * 65)
    print(f"\n{'='*65}\n{'DIAGNOSTICS & SUMMARY'.center(63)}\n{'='*65}")
    print(f"{'Original':<20}: {msg.ljust(40)[:40]}")
    print(f"{'Decoded':<20}: {res['decoded']}")
    print(f"{'Detected Rotation':<20}: ID {res['t_id']} (Pilot: {res['pilot_rx'][0]:.2f}, {res['pilot_rx'][1]:.2f})")
    sep()
    
    # Visualisation des points (5 premiers)
    tx, rx, cx, qx = res['points']['tx'], res['points']['rx'], res['points']['cx'], res['points']['qx']
    print(f"{'TYPE':<12} | {'SYMBOLS (Sample of 5)':<45}")
    sep()
    for label, data in [("TX (Sent)", tx), ("RX (Recv)", rx), ("CX (Corr)", cx), ("QX (Quant)", qx)]:
        pts = " ".join([f"({data[i]:.1f},{data[i+1]:.1f})" for i in range(0, 10, 2)])
        print(f"{label:<12} | {pts} ...")
    
    sep()
    color = "\033[92m" if res['energy'] <= config.MAX_ENERGY else "\033[91m"
    print(f"TOTAL ENERGY: {color}{res['energy']:.2f}\033[0m / {config.MAX_ENERGY} | N: {res['n']}")
    print(f"{'='*65}\n")