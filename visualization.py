import matplotlib.pyplot as plt
import numpy as np

def display_diagnostics(res):
    def sep(): print("-" * 65)
    GREEN, RED, RESET, BOLD = "\033[92m", "\033[91m", "\033[0m", "\033[1m"

    # Extraction des données de config et de résultats
    input_text     = res["input"]["input_text"]
    conf           = res['config']
    output_text    = res['output']['output_text']
    t_id           = res['output']['t_id']
    pilot_rx       = res['output']['output_pilot']
    energy         = res['stats']['energy']
    energy_per_bit = res['stats']['energy_per_bit']
    total_l        = len(res['input']['input_signal'])

    # 1. En-tête et Configuration
    print(f"\n{BOLD}{'='*65}")
    print(f"{'DIAGNOSTICS & SUMMARY'.center(63)}")
    print(f"{'='*65}{RESET}")
    
    print(f"{BOLD}[ CONFIGURATION ]{RESET}")
    print(f"Distance d : {conf['d']}")
    sep()

    # 2. Analyse du texte (caractère par caractère)
    colored_decoded = ""
    for i in range(max(len(input_text), len(output_text))):
        c_orig = input_text[i] if i < len(input_text) else None
        c_out  = output_text[i] if i < len(output_text) else None
        if c_orig == c_out: 
            colored_decoded += f"{GREEN}{c_out}{RESET}"
        else: 
            colored_decoded += f"{RED}{c_out if c_out else '∅'}{RESET}"

    print(f"{'Original':<20}: {input_text}")
    print(f"{'Decoded':<20}: {colored_decoded}")
    print(f"{'Rotation':<20}: ID {t_id} (Pilot RX: {pilot_rx[0]:.2f}, {pilot_rx[1]:.2f})")
    sep()
    
    # 3. Visualisation des points (Lecture directe)
    # print(f"{'TYPE':<12} | {'SYMBOLS (Sample of 5)':<45}")
    # sep()
    # mapping = [
    #     ("TX (Sent)", res['input']['input_message_modulate']),
    #     ("RX (Recv)", res['output']['output_signal'][2:]),
    #     ("CX (Corr)", res['output']['output_message_corrected']),
    #     ("QX (Quant)", res['output']['output_message_quantized'])
    # ]
    # for label, data in mapping:
    #     sample = data[:10]
    #     pts = " ".join([f"({sample[i]:.1f},{sample[i+1]:.1f})" for i in range(0, len(sample), 2)])
    #     print(f"{label:<12} | {pts} ...")
    
    # sep()

    # 4. Métriques et Verdict
    e_ok, l_ok, c_ok = energy <= 1200, total_l <= 500, input_text == output_text
    
    print(f"ENERGY          : {GREEN if e_ok else RED}{energy:.2f}{RESET} / 1200")
    print(f"LENGTH          : {GREEN if l_ok else RED}{total_l}{RESET} / 500")
    print(f"Energy per bit  : {energy_per_bit:.2f} J")

    sep()

    if e_ok and l_ok and c_ok:
        print(f"{BOLD}VERDICT : {GREEN}CORRECT ✅{RESET}")
    else:
        errors = [m for cond, m in [(not c_ok, "Corruption"), (not e_ok, "Énergie"), (not l_ok, "Longueur")] if cond]
        print(f"{BOLD}VERDICT : {RED}INVALID ❌ ({', '.join(errors)}){RESET}")
        
    print(f"{BOLD}{'='*65}{RESET}\n")

import matplotlib.pyplot as plt
import numpy as np

def plot_data(data):
    # On récupère le signal complet (Pilote + Message)
    tx_sig = np.array(data["input"]["input_signal"])
    rx_sig = np.array(data["output"]["output_message_corrected"]) # Signal après correction

    # Conversion en complexes (Re + j*Im)
    tx_cplx = tx_sig[0::2] + 1j * tx_sig[1::2]
    rx_cplx = rx_sig[0::2] + 1j * rx_sig[1::2]

    plt.figure(figsize=(8, 8))

    # Axes en GRAS (Priorité visuelle)
    plt.axhline(0, color='black', linewidth=2.5, zorder=1)
    plt.axvline(0, color='black', linewidth=2.5, zorder=1)

    # Données du message (on ignore le premier symbole qui est le pilote)
    plt.scatter(rx_cplx[1:].real, rx_cplx[1:].imag, color='red', alpha=0.5, s=20, label='Reçu (corrigé)')
    plt.scatter(tx_cplx[1:].real, tx_cplx[1:].imag, color='blue', marker='x', s=50, label='Théorique')

    # Pilote (Le premier symbole complexe : index 0)
    plt.scatter(tx_cplx[0].real, tx_cplx[0].imag, color='green', marker='D', s=120, label='Pilote TX')
    plt.scatter(rx_cplx[0].real, rx_cplx[0].imag, color='orange', marker='o', s=120, edgecolors='black', label='Pilote RX')

    plt.xlabel(r"$\bf{In-phase (I)}$", fontsize=12)
    plt.ylabel(r"$\bf{Quadrature (Q)}$", fontsize=12)
    plt.title(f"Constellation QAM-{data['config']['m_ary']}")
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend()
    
    plt.show()