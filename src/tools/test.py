import random
import numpy as np
import src.config as config
from src.main import transceiver

# ANSI Colors for clean terminal output
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def generate_random_msg() -> str:
    """Generates a random string based on the allowed config alphabet and target length."""
    return ''.join(random.choice(config.ALPHABET) for _ in range(config.MSG_LEN))

def run_stress_test(total_runs: int = config.TOTAL_RUNS, verbose_runs: int = 15):
    """Executes a pipeline verification suite with character-level color diagnostics."""
    
    # --- DISPLAY HEADERS ---
    print(f"\n{BOLD}{'='*90}")
    print(f"--- STRESS TEST CONFIGURATION ---".center(90))
    print(f"{'='*90}{RESET}")
    print(f"Modulation : 4-QAM (QPSK)")
    print(f"Distance d : {config.D_SPACING}")
    print(f"Thresholds : Energy <= {config.MAX_ENERGY} | Length <= {config.MAX_LENGTH}")
    print(f"Runs       : {total_runs} messages (Showing first {verbose_runs} traces)")
    
    print(f"\n{'='*90}")
    print(f"{'#':<4} | {'Data Trace (Original vs Decoded)':<42} | {'Energy':<8} | {'Status & Root Cause'}")
    print("-" * 90)

    # Prepare complete test dataset
    test_set = list(config.TEST_SET)
    while len(test_set) < total_runs:
        test_set.append(generate_random_msg())

    success_count = 0
    total_energy = 0
    
    pilot_failures = 0
    noise_failures = 0
    
    all_compression_ratios = []
    all_spectral_efficiencies = []
    all_eb_n0_db = []
    max_signal_len = 0

    for i, msg in enumerate(test_set):
        res = transceiver(
            input_text=msg, 
            encoding_dict=config.ENCODING, 
            d=config.D_SPACING, 
            n_pilot=config.N_PILOT, 
            K=config.K, 
            G=config.G,
            boost_factor=config.BOOST_FACTOR,
            punctured_bit=config.PUNCTURED_BIT
        )
        
        decoded         = res['output']['text']
        energy          = res['stats']['energy']
        signal_len      = len(res['input']['signal'])
        estimated_rot   = res['output']['t_id']
        actual_rot      = res['debug']['rotation']
        
        if signal_len > max_signal_len:
            max_signal_len = signal_len

        # Validate pipeline conditions
        is_correct   = (msg == decoded)
        is_energy_ok = (energy <= config.MAX_ENERGY)
        is_length_ok = (signal_len <= config.MAX_LENGTH)
        
        run_success  = is_correct and is_energy_ok and is_length_ok

        if run_success:
            success_count += 1
        else:
            if not is_correct:
                if estimated_rot != actual_rot:
                    pilot_failures += 1
                else:
                    noise_failures += 1
        
        total_energy += energy
        
        # --- TELECOM METRICS COMPILATION ---
        input_bits_len = len(res['input']['bits'])
        if len(msg) > 0:
            all_compression_ratios.append(input_bits_len / len(msg))
        
        total_2d_symbols = signal_len / 2
        all_spectral_efficiencies.append(input_bits_len / total_2d_symbols)
        
        eb = res['stats']['energy_per_bit']
        n0 = 2.0
        if eb > 0:
            all_eb_n0_db.append(10 * np.log10(eb / n0))
        
        # --- VERBOSE TRACE PRINTING ---
        if i < verbose_runs:
            status = f"{GREEN}OK{RESET}" if run_success else f"{RED}FAIL{RESET}"
            
            reasons = []
            if not is_energy_ok: reasons.append("Energy")
            if not is_length_ok: reasons.append("Length")
            
            if not is_correct:
                if estimated_rot != actual_rot:
                    reasons.append(f"{RED}{BOLD}Pilot Error{RESET}")
                else:
                    reasons.append("Noise Corruption")
                    
            reason_str = f" ({', '.join(reasons)})" if reasons else ""

            # --- COLORATION CHIRURGICALE CARACTÈRE PAR CARACTÈRE ---
            colored_decoded_parts = []
            max_len = max(len(msg), len(decoded))
            
            # On padde avec des espaces pour éviter les out-of-bounds si les longueurs diffèrent
            padded_msg = msg.ljust(max_len)
            padded_dec = decoded.ljust(max_len)
            
            for char_idx in range(max_len):
                c_in = padded_msg[char_idx]
                c_out = padded_dec[char_idx]
                
                if c_in == c_out:
                    colored_decoded_parts.append(f"{GREEN}{c_out}{RESET}")
                else:
                    # Caractère faux ou absent (si padding d'espace visible)
                    display_char = c_out if c_out != ' ' else '_' 
                    colored_decoded_parts.append(f"{RED}{BOLD}{display_char}{RESET}")
            
            colored_decoded_str = "".join(colored_decoded_parts)
            
            # Print ajusté pour garder un alignement parfait à l'écran
            print(f"{i+1:<4} | In : {msg:<35} | {energy:>8.1f} | {status}{reason_str}")
            print(f"     | Out: {colored_decoded_str:<35} | Rot: Real {actual_rot} / Est {estimated_rot}")
            print("-" * 90)
        elif i == verbose_runs:
            print("...")

    # --- FINAL AGGREGATE STATS ---
    accuracy = (success_count / total_runs) * 100
    avg_energy = total_energy / total_runs

    print(f"ACCURACY       : {accuracy:.1f}% ({success_count}/{total_runs})")
    print(f"AVG ENERGY     : {avg_energy:.2f} (Limit: {config.MAX_ENERGY})")
    print(f"MAX SIG LENGTH : {max_signal_len} (Limit: {config.MAX_LENGTH})")
    
    # --- DIAGNOSTIC BREAKDOWN ---
    total_failures = total_runs - success_count
    if total_failures > 0:
        print(f"\n{BOLD}--- FAILURE ANALYSIS DIAGNOSTICS ---{RESET}")
        print(f"  ↳ Total Text Failures : {pilot_failures + noise_failures}")
        print(f"    ■ Pilot Tracking Errors : {pilot_failures} ({ (pilot_failures/total_runs)*100 :.1f}%) -> {RED}Bad phase sync{RESET}")
        print(f"    ■ Noise / Puncture Soft-Errors : {noise_failures} ({ (noise_failures/total_runs)*100 :.1f}%) -> {RED}Channel attenuation/noise{RESET}")

    # --- TELECOM ANALYSIS DISPLAY ---
    print(f"\n{BOLD}--- TELECOMMUNICATION METRICS ---{RESET}")
    if all_compression_ratios:
        print(f"Source Bitrate      : {np.mean(all_compression_ratios):.2f} bits/char")
    if all_spectral_efficiencies:
        print(f"Spectral Efficiency : {np.mean(all_spectral_efficiencies):.2f} bits/symbol (Punctured)")
    if all_eb_n0_db:
        print(f"Channel SNR (Eb/N0) : {np.mean(all_eb_n0_db):.2f} dB")
    
    if accuracy == 100 and avg_energy <= config.MAX_ENERGY and max_signal_len <= config.MAX_LENGTH:
        print(f"\n{GREEN}{BOLD}SYSTEM VALIDATED ✅{RESET}")
    else:
        print(f"\n{RED}{BOLD}SYSTEM UNSTABLE ❌{RESET}")
    print(f"{BOLD}{'='*90}{RESET}\n")

if __name__ == "__main__":
    run_stress_test()