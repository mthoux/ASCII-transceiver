import sys
import numpy as np
import channel 

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Donne un message !")

    # Transform each letter in its ASCII code
    message = sys.argv[1]
    digits = [float(ord(c)) for c in message]

    # Canal must have an even entry
    if len(digits) % 2 != 0:
        digits.append(0.0)

    x = np.array(digits)
    y = channel.channel(x)

    # Dummy decoder
    decoded = []
    for nb in y:
        decoded.append(chr(abs(round(nb))))

    print(f"Message : {message}")
    print(f"Send    : {x}")
    print(f"Receive : {[f'{val:.2f}' for val in y]}")
    print(f"Decoded : {decoded}")