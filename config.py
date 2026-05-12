# config.py
ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ."
D_SPACING = 5
M_ARY = 4

# --- CONFIG TEST ---
TOTAL_RUNS = 50
MSG_LEN = 40  # Ta contrainte de 40 caractères
MAX_ENERGY = 1200
MAX_LENGTH = 500

TEST_SET = [
    "hello",
    "The quick brown fox jumps over the dog.",
    "A1b2C3d4E5f6G7h8I9j0 .A1b2C3d4E5f6G7h8I9",
    "Testing 1234567890 symbols and spaces. ",
    "AAAAAaaaaaBBBBBbbbbbCCCCCcccccDDDDDdddd",
    "Short msg.                              ",
    "Short msg.",
    "Z.Z.Z.Z.Z.Z.Z.Z.Z.Z.Z.Z.Z.Z.Z.Z.Z.Z.Z.Z.",
]