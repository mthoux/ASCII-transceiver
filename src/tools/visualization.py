import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

def display_diagnostics(res):
    def sep(): print("-" * 65)
    GREEN, RED, RESET, BOLD = "\033[92m", "\033[91m", "\033[0m", "\033[1m"

    input_text     = res["input"]["text"]
    conf           = res['config']
    output_text    = res['output']['text']
    t_id           = res['output']['t_id']
    pilot_rx       = res['output']['pilot']
    energy         = res['stats']['energy']
    energy_per_bit = res['stats']['energy_per_bit']
    bit_error_rate = res['stats']['bit_error_rate']
    total_l        = len(res['input']['signal'])
    
    # Récupération de la vraie rotation du canal (ID 0, 1, 2 ou 3)
    chosen_rotation = res['debug']['rotation']

    # 1. En-tête et Configuration
    print(f"\n{BOLD}{'='*65}")
    print(f"{'DIAGNOSTICS & SUMMARY'.center(63)}")
    print(f"{'='*65}{RESET}")
    
    print(f"{BOLD}[ CONFIGURATION ]{RESET}")
    print(f"Distance d : {conf['d']}")
    sep()

    # 2. Analyse du texte
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
    
    # Mapping unique pour l'affichage en degrés (optionnel, juste pour la lisibilité)
    id_to_angle = {1: 0, 2: 90, 3: 180, 4: 270}
    true_angle       = id_to_angle.get(chosen_rotation, "??")
    estimated_angle  = id_to_angle.get(t_id, "??")

    # --- COMPARAISON DIRECTE DES IDs ---
    rot_correct = (t_id == chosen_rotation)
    rot_color = GREEN if rot_correct else RED

    print(f"{'Rotation Canal':<20}: ID {chosen_rotation} ({true_angle}°)")
    print(f"{'Rotation Estimée':<20}: {rot_color}ID {t_id} ({estimated_angle}°){RESET}")
    sep()
    
    # 4. Métriques et Verdict
    e_ok, l_ok, c_ok = energy <= 1200, total_l <= 500, input_text == output_text
    
    print(f"ENERGY          : {GREEN if e_ok else RED}{energy:.2f}{RESET} / 1200")
    print(f"LENGTH          : {GREEN if l_ok else RED}{total_l}{RESET} / 500")
    print(f"Bit Error Rate  : {GREEN if bit_error_rate == 0 else RED}{bit_error_rate:.2} %{RESET}")
    print(f"Energy per bit  : {energy_per_bit:.2} J/b{RESET}")

    sep()

    if e_ok and l_ok and c_ok:
        print(f"{BOLD}VERDICT : {GREEN}CORRECT ✅{RESET}")
    else:
        errors = [m for cond, m in [(not c_ok, "Corruption"), (not e_ok, "Énergie"), (not l_ok, "Longueur")] if cond]
        print(f"{BOLD}VERDICT : {RED}INVALID ❌ ({', '.join(errors)}){RESET}")
        
    print(f"{BOLD}{'='*65}{RESET}\n")


def print_diagnostics(res):
    """
    Affiche le diagnostic textuel proprement dans le terminal.
    """
    p_out_re, p_out_im = res["output"]["pilot"]
    status = "SUCCÈS (0 erreur)" if res['stats']['bit_error_rate'] == 0 else "DES ERREURS DÉTECTÉES"
    
    print("\n" + "="*40)
    print("      DIAGNOSTICS TIMING & PERFS")
    print("="*40)
    print(f"• Message Input  : '{res['input']['text']}'")
    print(f"• Message Output : '{res['output']['text']}'")
    print("-"*40)
    print(f"• Quadrant détecté (t_id) : {res['output']['t_id']}")
    print(f"• Pilote moyen (I, Q)    : ({p_out_re:.2f}, {p_out_im:.2f})")
    print("-"*40)
    print(f"• Énergie Totale         : {res['stats']['energy']:.2f}")
    print(f"• Énergie par Bit        : {res['stats']['energy_per_bit']:.2f}")
    print(f"• Bit Error Rate (BER)   : {res['stats']['bit_error_rate']*100:.3f} %")
    print("-"*40)
    print(f"Status : {status}")
    print("="*40 + "\n")

def plot_constellations(result):
    """
    Plot the raw received and phase-corrected constellations side by side,
    with dynamically adjusted quadrant colors to support puncturing.
    """
    # 1 — STYLE & CONFIG
    try:
        plt.style.use('seaborn-v0_8-whitegrid')
    except OSError:
        pass

    d       = result['config']['d']
    n_pilot = result['config']['n_pilot']
    
    # 2 — QUADRANT COLOUR MAPPING
    signal_in = result['input']['modulate']
    in_re     = signal_in[0::2]
    in_im     = signal_in[1::2]
    n_symbols_original = len(in_re)

    QUADRANT_COLORS = {
        1: '#2b7bba',  # Q1 — slate blue
        2: '#4a984a',  # Q2 — sage green
        3: '#e68a00',  # Q3 — muted orange
        4: '#df3b3b',  # Q4 — crimson red
    }
    QUADRANT_LABELS = {
        1: 'Origin Q1', 2: 'Origin Q2',
        3: 'Origin Q3', 4: 'Origin Q4',
    }

    # Génération des couleurs initiales pour TOUS les symboles générés
    original_colors = []
    for i in range(n_symbols_original):
        re, im = in_re[i], in_im[i]
        if   re > 0 and im > 0: q = 1
        elif re < 0 and im > 0: q = 2
        elif re < 0 and im < 0: q = 3
        else:                   q = 4
        original_colors.append(QUADRANT_COLORS[q])

    # 3 — DATA EXTRACTION & PUCTURE ADJUSTMENT
    # Signaux bruts reçus du canal
    pilots_raw    = result['output']['signal'][:2 * n_pilot]
    pilot_raw_re  = pilots_raw[0::2]
    pilot_raw_im  = pilots_raw[1::2]
    pilot_out_re, pilot_out_im = result['output']['pilot']

    # Récupération des données reçues (poinçonnées !)
    raw_signal = result['output']['signal'][2 * n_pilot:]
    raw_re     = raw_signal[0::2]
    raw_im     = raw_signal[1::2]
    n_symbols_received = len(raw_re)

    # Récupération du signal corrigé
    corrected = result['output']['corrected']
    # Sécurité si jamais les pilotes sont encore présents dans corrected
    if len(corrected) == len(result['output']['signal']):
        corrected = corrected[2 * n_pilot:]
    corr_re = corrected[0::2]
    corr_im = corrected[1::2]

    # --- CORRECTION DU BUG DE COULEUR ---
    # Si le signal reçu est plus court à cause du poinçonnage, 
    # on adapte la taille des couleurs pour correspondre aux points restants.
    if n_symbols_received < n_symbols_original:
        # Cas où le poinçonnage a été fait de manière uniforme / linéaire ou par paires
        # On échantillonne les couleurs d'origine pour fitter la taille reçue
        indices = np.linspace(0, n_symbols_original - 1, n_symbols_received, dtype=int)
        symbol_colors = [original_colors[idx] for idx in indices]
    else:
        symbol_colors = original_colors

    # 4 — FIGURE & AXES LAYOUT
    fig = plt.figure(figsize=(10, 5.8), facecolor='#fdfdfd')
    gs  = fig.add_gridspec(2, 2, height_ratios=[0.87, 0.13])
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])

    # 5 — LEFT PLOT: RAW RECEIVED CONSTELLATION
    ax1.scatter(raw_re, raw_im,
                c=symbol_colors, alpha=0.5, s=20, zorder=2)
    ax1.scatter([d, -d, -d,  d], [d, d, -d, -d],
                color='#1d242a', marker='x', s=80, alpha=0.9, zorder=1)
    ax1.scatter(pilot_raw_re, pilot_raw_im,
                color='#f1c40f', edgecolor='#34495e',
                s=60, marker='*', zorder=3)
    ax1.scatter(pilot_out_re, pilot_out_im,
                color='#f39c12', edgecolor='#c0392b', linewidths=1.2,
                s=200, marker='*', zorder=4)

    ax1.set_title('Raw Received Constellation', fontsize=11, fontweight='bold', pad=8)
    ax1.set_xlabel('In-phase (I)',   fontsize=9)
    ax1.set_ylabel('Quadrature (Q)', fontsize=9)
    ax1.axhline(0, color='#7f8c8d', linewidth=0.8, linestyle=':')
    ax1.axvline(0, color='#7f8c8d', linewidth=0.8, linestyle=':')
    ax1.set_xlim([-d * 2.5, d * 2.5])
    ax1.set_ylim([-d * 2.5, d * 2.5])
    ax1.set_aspect('equal')

    # 6 — RIGHT PLOT: PHASE-CORRECTED CONSTELLATION
    ax2.scatter(corr_re, corr_im,
                c=symbol_colors, alpha=0.5, s=20, zorder=2)
    ax2.scatter([d, -d, -d,  d], [d, d, -d, -d],
                color='#1d242a', marker='x', s=80, alpha=0.9, zorder=1)

    ax2.set_title('Phase-Corrected Constellation', fontsize=11, fontweight='bold', pad=8)
    ax2.set_xlabel('In-phase (I)',   fontsize=9)
    ax2.set_ylabel('Quadrature (Q)', fontsize=9)
    ax2.axhline(0, color='#7f8c8d', linewidth=0.8, linestyle=':')
    ax2.axvline(0, color='#7f8c8d', linewidth=0.8, linestyle=':')
    ax2.set_xlim([-d * 2.5, d * 2.5])
    ax2.set_ylim([-d * 2.5, d * 2.5])
    ax2.set_aspect('equal')

    # 7 — SHARED LEGEND
    legend_handles = [
        Line2D([0], [0], marker='o', color='w',
               markerfacecolor=QUADRANT_COLORS[q],
               label=QUADRANT_LABELS[q], markersize=8)
        for q in (1, 2, 3, 4)
    ] + [
        Line2D([0], [0], marker='*', color='w', label='Pilots',
               markerfacecolor='#f1c40f', markeredgecolor='#34495e', markersize=9),
        Line2D([0], [0], marker='*', color='w', label='Avg. pilot',
               markerfacecolor='#f39c12', markeredgecolor='#c0392b', markersize=13),
        Line2D([0], [0], marker='x', color='w', label='4-QAM ideal',
               markerfacecolor='#1d242a', markeredgecolor='black', markersize=8),
    ]
    fig.legend(
        handles=legend_handles,
        loc='upper center', bbox_to_anchor=(0.5, 0.95),
        ncol=7, fontsize='x-small', frameon=True, facecolor='#ffffff',
    )

    # 8 — SUMMARY BANNER (FULL-WIDTH BOTTOM ROW)
    text_in  = result['input']['text']
    text_out = result['output']['text']
    energy   = result['stats']['energy']
    sig_len  = len(result['input']['signal'])
    ber_pct  = result['stats']['bit_error_rate'] * 100

    energy_ok = energy  <= 1200
    length_ok = sig_len <= 500
    verdict   = 'SUCCESS' if (energy_ok and length_ok and text_in == text_out) else 'FAILED'

    C_GREEN = '#2e7d32'
    C_RED   = '#c62828'
    C_DARK  = '#1a252f'

    ax_banner = fig.add_subplot(gs[1, :])
    ax_banner.set_facecolor('#ffffff')

    Y = [0.76, 0.52, 0.28, 0.04]

    for label, y in [('[ TRANSCRIPTION ]', Y[0]), ('[ PERFORMANCE ]', Y[2]), ('[ SYSTEM STATUS ]', Y[3])]:
        ax_banner.text(0.02, y, label, color=C_DARK, fontweight='bold', fontfamily='monospace', fontsize=9, transform=ax_banner.transAxes)

    max_len = max(len(text_in), len(text_out))
    padded_in  = text_in.ljust(max_len)
    padded_out = text_out.ljust(max_len)
    indent     = '           '

    base_layer  = f'Original : {text_in}\nDecoded  : '
    green_layer = '\n' + indent + ''.join(c if c == padded_in[i] else ' ' for i, c in enumerate(padded_out))
    red_layer   = '\n' + indent + ''.join(c if c != padded_in[i] else ' ' for i, c in enumerate(padded_out))

    for text, color, bold in [(base_layer, C_DARK, False), (green_layer, C_GREEN, True), (red_layer, C_RED, True)]:
        ax_banner.text(0.20, Y[1], text, color=color, fontweight='bold' if bold else 'normal', fontfamily='monospace', fontsize=9, transform=ax_banner.transAxes)

    ax_banner.text(0.20, Y[2], f'Energy : {energy:.2f} / 1200 J', color=C_GREEN if energy_ok else C_RED, fontfamily='monospace', fontsize=9, fontweight='bold', transform=ax_banner.transAxes)
    ax_banner.text(0.48, Y[2], f'Length : {sig_len} / 500 samples', color=C_GREEN if length_ok else C_RED, fontfamily='monospace', fontsize=9, fontweight='bold', transform=ax_banner.transAxes)
    ax_banner.text(0.76, Y[2], f'BER    : {ber_pct:.3f} %', color=C_GREEN if ber_pct == 0 else C_DARK, fontfamily='monospace', fontsize=9, transform=ax_banner.transAxes)

    status_prefix = f'Channel rotation ID: {result["output"]["t_id"]}  |  Energy/bit: {result["stats"]["energy_per_bit"]:.2f} J/b  |  Verdict: '
    ax_banner.text(0.20, Y[3], status_prefix, color=C_DARK, fontfamily='monospace', fontsize=9, transform=ax_banner.transAxes)
    ax_banner.text(0.72, Y[3], verdict, color=C_GREEN if verdict == 'SUCCESS' else C_RED, fontfamily='monospace', fontsize=9, fontweight='bold', transform=ax_banner.transAxes)

    ax_banner.grid(False)
    ax_banner.set_xticks([])
    ax_banner.set_yticks([])
    for side in ('bottom', 'left', 'right'):
        ax_banner.spines[side].set_visible(False)
    ax_banner.spines['top'].set_color('#e2e8f0')
    ax_banner.spines['top'].set_linewidth(1.5)

    plt.tight_layout(rect=[0, 0.01, 1, 0.84])
    plt.show()