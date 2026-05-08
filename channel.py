import numpy as np

def channel(x):
    x = np.asarray(x, dtype=float)

    if x.size % 2 != 0:
        raise ValueError(f"Input length must be even, got {x.size}.")
    
    i = int(np.random.randint(1, 5)) # uniform on {1,2,3,4}

    # Reshape into (n/2, 2) so each row is one complex symbol (a, b)
    pairs = x.reshape(-1, 2)
    a, b = pairs[:, 0], pairs[:, 1]

    if i == 1:
        Tx = np.stack([ a, b], axis=1)
    elif i == 2:
        Tx = np.stack([-b, a], axis=1)
    elif i == 3:
        Tx = np.stack([-a, -b], axis=1)
    else: # i == 4
        Tx = np.stack([ b, -a], axis=1)

    Tx = Tx.reshape(-1)
    z = np.random.standard_normal(Tx.shape)

    return (Tx + z)