import sys
import numpy as np

from transmitter import encode
from channel import channel
from receiver import decode

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python main.py [message string]")

    message = sys.argv[1]
    x = encode(message)
    y = channel(x)
    z = decode(y)

    print(f"Message : {message}")
    print(f"Send    : {x}")
    print(f"Receive : {[f'{val:.2f}' for val in y]}")
    print(f"Decoded : {z}")

    energie = np.sum(np.array(x)**2)
    print(f"Énergie totale dépensée : {energie}")