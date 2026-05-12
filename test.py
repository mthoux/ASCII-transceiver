import random
import config
from main import transceiver

# Couleurs ANSI
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def generate_random_msg():
    return ''.join(random.choice(config.ALPHABET) for _ in range(config.MSG_LEN))

def run_stress_test(total_runs=config.TOTAL_RUNS):
    # --- AFFICHAGE CONFIG ---
    print(f"\n{BOLD}{'='*70}")
    print(f"--- STRESS TEST CONFIGURATION ---".center(70))
    print(f"{'='*70}{RESET}")
    print(f"Modulation : {config.M_ARY}-QAM")
    print(f"Distance d : {config.D_SPACING}")
    print(f"Thresholds : Energy <= {config.MAX_ENERGY} | Length <= {config.MAX_LENGTH}")
    print(f"Runs       : {total_runs} messages")
    
    print(f"\n{'='*70}")
    print(f"{'#':<3} | {'Original (start)':<25} | {'Energy':<8} | {'Status'}")
    print("-" * 70)

    test_set = list(config.TEST_SET)
    while len(test_set) < total_runs:
        test_set.append(generate_random_msg())

    success_count = 0
    total_energy = 0

    for i, msg in enumerate(test_set):
        res = transceiver(msg, m_ary=config.M_ARY, d=config.D_SPACING)
        
        decoded = res['output']['output_message_text']
        energy  = res['stats']['energy']
        length  = len(res['input']['input_signal'])

        # FAILLE POSSIBLE : Le padding. On strip ou on compare sur la longueur d'origine.
        # Ici on compare si le message original est contenu dans le décodé ou vice-versa
        is_correct = (msg.strip() == decoded.strip())
        is_energy_ok = (energy <= config.MAX_ENERGY)
        is_length_ok = (length <= config.MAX_LENGTH)
        
        run_success = is_correct and is_energy_ok and is_length_ok

        if run_success:
            success_count += 1
        
        total_energy += energy
        
        if i < 15:
            status = f"{GREEN}OK{RESET}" if run_success else f"{RED}FAIL{RESET}"
            # On affiche la raison de l'échec si c'est pas correct
            reason = "" if is_correct else " (Text)"
            print(f"{i+1:<3} | {msg[:25]:<25}... | {energy:>8.1f} | {status}{reason}")
        elif i == 15:
            print("...")

    accuracy = (success_count / total_runs) * 100
    avg_energy = total_energy / total_runs

    print("-" * 70)
    print(f"ACCURACY   : {accuracy:.1f}% ({success_count}/{total_runs})")
    print(f"AVG ENERGY : {avg_energy:.2f} (Limit: {config.MAX_ENERGY})")
    
    if accuracy == 100 and avg_energy <= config.MAX_ENERGY:
        print(f"\n{GREEN}{BOLD}SYSTEM VALIDATED ✅{RESET}")
    else:
        print(f"\n{RED}{BOLD}SYSTEM UNSTABLE ❌{RESET}")
    print(f"{BOLD}{'='*70}{RESET}\n")

if __name__ == "__main__":
    run_stress_test()