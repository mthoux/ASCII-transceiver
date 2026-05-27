import os
import subprocess
import numpy as np

def online_channel(input_signal, srv_hostname="iscsrv72.epfl.ch", srv_port="80"):
    """
    Gère la communication avec le serveur EPFL en écrivant le signal d'entrée,
    en exécutant le script client et en récupérant le signal de sortie.
    """
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construit un chemin absolu vers input.txt et output.txt
    input_file_path = os.path.join(current_dir, "input.txt")
    output_file_path = os.path.join(current_dir, "output.txt")
    
    # 1. Write input_signal in input.txt
    np.savetxt(input_file_path, input_signal)
    
    # 2. Call client/client.py via subprocess
    # On adapte aussi le chemin de client.py pour qu'il soit absolu et robuste
    client_script_path = os.path.join(current_dir, "client.py")
    cmd = [
        "./venv/bin/python3", client_script_path,
        "--input_file", input_file_path,
        "--output_file", output_file_path,
        "--srv_hostname", srv_hostname,
        "--srv_port", srv_port
    ]
    
    # Config environnement to include PYTHONPATH=.
    current_env = os.environ.copy()
    current_env["PYTHONPATH"] = "."
    
    print("Envoi du signal au serveur EPFL...")
    result = subprocess.run(cmd, env=current_env, capture_output=True, text=True)
    
    # Sécurity : if client.py crash
    if result.returncode != 0:
        print("Erreur lors de l'exécution du client :")
        print(result.stderr)
        raise RuntimeError("Le script client a échoué.")
        
    # 3. Get result in output.txt
    if os.path.exists(output_file_path):
        output_signal = np.loadtxt(output_file_path)
    else:
        raise FileNotFoundError(f"Le fichier {output_file_path} n'a pas été généré par le serveur.")
        
    print("Signal reçu et chargé avec succès !")
    return output_signal