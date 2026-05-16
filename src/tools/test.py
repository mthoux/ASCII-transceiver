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

def run_stress_test(total_runs: int = config.TOTAL_RUNS):
    """Executes a pipeline verification suite over a batch of messages."""
    
    # --- DISPLAY HEADERS ---
    print(f"\n{BOLD}{'='*70}")
    print(f"--- STRESS TEST CONFIGURATION ---".center(70))
    print(f"{'='*70}{RESET}")
    print(f"Modulation : 4-QAM (QPSK)")
    print(f"Distance d : {config.D_SPACING}")
    print(f"Thresholds : Energy <= {config.MAX_ENERGY} | Length <= {config.MAX_LENGTH}")
    print(f"Runs       : {total_runs} messages")
    
    print(f"\n{'='*70}")
    print(f"{'#':<3} | {'Original (start)':<25} | {'Energy':<8} | {'Status'}")
    print("-" * 70)

    # Prepare complete test dataset
    test_set = list(config.TEST_SET)
    while len(test_set) < total_runs:
        test_set.append(generate_random_msg())

    success_count = 0
    total_energy = 0
    
    # Lists to collect metrics for telecommunication analysis
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
            G=config.G
        )
        
        decoded      = res['output']['text']
        energy       = res['stats']['energy']
        signal_len   = len(res['input']['signal'])
        
        if signal_len > max_signal_len:
            max_signal_len = signal_len

        # Validate pipeline conditions
        is_correct   = (msg == decoded)
        is_energy_ok = (energy <= config.MAX_ENERGY)
        is_length_ok = (signal_len <= config.MAX_LENGTH)
        
        run_success  = is_correct and is_energy_ok and is_length_ok

        if run_success:
            success_count += 1
        
        total_energy += energy
        
        # --- TELECOM METRICS COMPILATION ---
        # 1. Source Compression Ratio (bits per source character)
        input_bits_len = len(res['input']['bits'])
        if len(msg) > 0:
            all_compression_ratios.append(input_bits_len / len(msg))
        
        # 2. Spectral Efficiency (Info bits / transmitted 2D symbols)
        # signal_len holds 1D coordinates (I and Q), so total 2D symbols = signal_len / 2
        total_2d_symbols = signal_len / 2
        all_spectral_efficiencies.append(input_bits_len / total_2d_symbols)
        
        # 3. Channel SNR (Eb/N0 in dB)
        # energy_per_bit (Eb) is calculated relative to channel encoded bits
        eb = res['stats']['energy_per_bit']
        n0 = 2.0  # AWGN variance is 1.0, so N0 = 2 * var = 2.0
        if eb > 0:
            all_eb_n0_db.append(10 * np.log10(eb / n0))
        
        # Verbose trace printing for the first 15 test iterations
        if i < 15:
            status = f"{GREEN}OK{RESET}" if run_success else f"{RED}FAIL{RESET}"
            
            reasons = []
            if not is_correct:   reasons.append("Text")
            if not is_energy_ok: reasons.append("Energy")
            if not is_length_ok: reasons.append("Length")
            reason_str = f" ({', '.join(reasons)})" if reasons else ""
            
            print(f"{i+1:<3} | {msg[:25]:<25}... | {energy:>8.1f} | {status}{reason_str}")
        elif i == 15:
            print("...")

    # --- FINAL AGGREGATE STATS ---
    accuracy = (success_count / total_runs) * 100
    avg_energy = total_energy / total_runs

    print("-" * 70)
    print(f"ACCURACY       : {accuracy:.1f}% ({success_count}/{total_runs})")
    print(f"AVG ENERGY     : {avg_energy:.2f} (Limit: {config.MAX_ENERGY})")
    print(f"MAX SIG LENGTH : {max_signal_len} (Limit: {config.MAX_LENGTH})")
    
    # --- TELECOM ANALYSIS DISPLAY ---
    print(f"\n{BOLD}--- TELECOMMUNICATION METRICS ---{RESET}")
    if all_compression_ratios:
        print(f"Source Bitrate      : {np.mean(all_compression_ratios):.2f} bits/char")
    if all_spectral_efficiencies:
        print(f"Spectral Efficiency : {np.mean(all_spectral_efficiencies):.2f} bits/symbol")
    if all_eb_n0_db:
        print(f"Channel SNR (Eb/N0) : {np.mean(all_eb_n0_db):.2f} dB")
    
    if accuracy == 100 and avg_energy <= config.MAX_ENERGY and max_signal_len <= config.MAX_LENGTH:
        print(f"\n{GREEN}{BOLD}SYSTEM VALIDATED ✅{RESET}")
    else:
        print(f"\n{RED}{BOLD}SYSTEM UNSTABLE ❌{RESET}")
    print(f"{BOLD}{'='*70}{RESET}\n")

if __name__ == "__main__":
    run_stress_test()