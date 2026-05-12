# test.py
import random
import config
from main import run_pipeline

def generate_random_msg():
    return ''.join(random.choice(config.ALPHABET) for _ in range(config.MSG_LEN))

def run_stress_test(total_runs=50):
    print(f"--- Starting Stress Test ({total_runs} messages) ---")
    print(f"{'#':<3} | {'Original (start)':<25} | {'Energy':<8} | {'Status'}")
    print("-" * 60)

    # Base messages to always include
    test_set = [
        "The quick brown fox jumps over the dog.",
        "A1b2C3d4E5f6G7h8I9j0 .A1b2C3d4E5f6G7h8I9",
        "Testing 1234567890 symbols and spaces. ", # Chiffres et finaux
        "AAAAAaaaaaBBBBBbbbbbCCCCCcccccDDDDDdddd", # Répétitions (stress test)
        "Short msg.                              ", # Padding manuel
        "Z.Z.Z.Z.Z.Z.Z.Z.Z.Z.Z.Z.Z.Z.Z.Z.Z.Z.Z.Z.", # Alternance haute énergie
    ]
    
    # Fill with random
    while len(test_set) < total_runs:
        test_set.append(generate_random_msg())

    success_count = 0
    total_energy = 0

    for i, msg in enumerate(test_set):
        res = run_pipeline(msg)
        
        total_energy += res['energy']
        if res['success']:
            success_count += 1
        
        status = "✅ OK" if res['success'] else "❌ FAIL"
        if i < 10: # Display first 10
            print(f"{i+1:<3} | {msg[:25]}... | {res['energy']:>8.1f} | {status}")
        elif i == 10:
            print("...")

    accuracy = (success_count / total_runs) * 100
    avg_energy = total_energy / total_runs

    print("-" * 60)
    print(f"FINAL ACCURACY: {accuracy:.1f}% ({success_count}/{total_runs})")
    print(f"AVG ENERGY: {avg_energy:.2f} (Limit: {config.MAX_ENERGY})")
    
    if avg_energy > config.MAX_ENERGY:
        print("🚨 CRITICAL: ENERGY LIMIT EXCEEDED")

if __name__ == "__main__":
    run_stress_test(total_runs=100)