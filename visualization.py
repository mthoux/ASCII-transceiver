def display_diagnostics(msg, res):
    def sep(): print("-" * 65)
    GREEN, RED, RESET, BOLD = "\033[92m", "\033[91m", "\033[0m", "\033[1m"

    # Extraction des données de config et de résultats
    conf     = res['config']
    out_text = res['output']['output_message_text']
    t_id     = res['output']['t_id']
    pilot_rx = res['output']['output_pilot']
    energy   = res['stats']['energy']
    total_l  = len(res['input']['input_signal'])

    # 1. En-tête et Configuration
    print(f"\n{BOLD}{'='*65}")
    print(f"{'DIAGNOSTICS & SUMMARY'.center(63)}")
    print(f"{'='*65}{RESET}")
    
    print(f"{BOLD}[ CONFIGURATION ]{RESET}")
    print(f"Modulation : {conf['m_ary']}-QAM ({conf['k']} bits/symbole)")
    print(f"Distance d : {conf['d']}")
    sep()

    # 2. Analyse du texte (caractère par caractère)
    colored_decoded = ""
    for i in range(max(len(msg), len(out_text))):
        c_orig = msg[i] if i < len(msg) else None
        c_out  = out_text[i] if i < len(out_text) else None
        if c_orig == c_out: 
            colored_decoded += f"{GREEN}{c_out}{RESET}"
        else: 
            colored_decoded += f"{RED}{c_out if c_out else '∅'}{RESET}"

    print(f"{'Original':<20}: {msg}")
    print(f"{'Decoded':<20}: {colored_decoded}")
    print(f"{'Rotation':<20}: ID {t_id} (Pilot RX: {pilot_rx[0]:.2f}, {pilot_rx[1]:.2f})")
    sep()
    
    # 3. Visualisation des points (Lecture directe)
    print(f"{'TYPE':<12} | {'SYMBOLS (Sample of 5)':<45}")
    sep()
    mapping = [
        ("TX (Sent)", res['input']['input_message_modulate']),
        ("RX (Recv)", res['input']['input_signal'][2:]),
        ("CX (Corr)", res['output']['output_message_corrected']),
        ("QX (Quant)", res['output']['output_message_quantized'])
    ]
    for label, data in mapping:
        sample = data[:10]
        pts = " ".join([f"({sample[i]:.1f},{sample[i+1]:.1f})" for i in range(0, len(sample), 2)])
        print(f"{label:<12} | {pts} ...")
    
    sep()

    # 4. Métriques et Verdict
    e_ok, l_ok, c_ok = energy <= 1200, total_l <= 500, msg == out_text
    
    print(f"ENERGY  : {GREEN if e_ok else RED}{energy:.2f}{RESET} / 1200")
    print(f"LENGTH  : {GREEN if l_ok else RED}{total_l}{RESET} / 500")
    sep()

    if e_ok and l_ok and c_ok:
        print(f"{BOLD}VERDICT : {GREEN}CORRECT ✅{RESET}")
    else:
        errors = [m for cond, m in [(not c_ok, "Corruption"), (not e_ok, "Énergie"), (not l_ok, "Longueur")] if cond]
        print(f"{BOLD}VERDICT : {RED}INVALID ❌ ({', '.join(errors)}){RESET}")
        
    print(f"{BOLD}{'='*65}{RESET}\n")