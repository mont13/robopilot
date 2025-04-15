import socket
import time

# Nahraďte skutečnou IP adresou vašeho UR kontroleru
ROBOT_IP = "192.168.0.96"  # Příklad IP adresy
DASHBOARD_PORT = 29999

# Název programu, jak je uložen na robotu (včetně cesty, pokud není v kořenovém adresáři /programs/)
# Důležité: Cesta musí být v Linuxovém formátu (lomítka /) a relativní k adresáři /programs
# Příklad: Pokud je program v /programs/podslozka/muj_program.urp, použijte "podslozka/muj_program.urp"
# Nebo jen "muj_program.urp", pokud je přímo v /programs
PROGRAM_OPEN = "/programs/gripper_open.urp"


def send_dashboard_command(command):
    """Funkce pro odeslání příkazu na Dashboard Server a získání odpovědi."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)  # Nastavení timeoutu pro připojení a komunikaci
            print(f"Připojování k {ROBOT_IP}:{DASHBOARD_PORT}...")
            s.connect((ROBOT_IP, DASHBOARD_PORT))
            print("Připojeno.")

            # Přidání nového řádku, pokud chybí
            if not command.endswith('\n'):
                command += '\n'

            print(f"Odesílání příkazu: {command.strip()}")
            s.sendall(command.encode('utf-8'))

            # Čekání na odpověď (může přijít více řádků)
            response = ""
            while True:
                try:
                    chunk = s.recv(1024).decode('utf-8')
                    if not chunk:
                        # Spojení uzavřeno serverem
                        break
                    response += chunk
                    # Jednoduchá kontrola, zda odpověď obsahuje očekávaný text (lze vylepšit)
                    if "Loading program" in response or "Starting program" in response or "Failed" in response or "Error" in response or "Connected" in response:
                        # Zde můžeme předpokládat konec relevantní odpovědi pro jednoduché příkazy
                        # Pro složitější scénáře může být potřeba lepší parsing odpovědi
                        break
                    if len(response) > 2048:  # Pojistka proti nekonečnému čtení
                        print("Warning: Příliš dlouhá odpověď, ukončuji čtení.")
                        break
                except socket.timeout:
                    # Pokud už nic nepřichází, bereme to jako konec odpovědi
                    print("Socket timeout při čtení odpovědi.")
                    break
                except Exception as e:
                    print(f"Chyba při čtení odpovědi: {e}")
                    break

            print(f"Odpověď serveru: {response.strip()}")
            return response.strip()

    except socket.timeout:
        print(f"Chyba: Timeout při připojování k {ROBOT_IP}:{DASHBOARD_PORT}")
        return None
    except ConnectionRefusedError:
        print(f"Chyba: Spojení odmítnuto. Je robot zapnutý a ve správné síti? Není blokován port?")
        return None
    except Exception as e:
        print(f"Došlo k neočekávané chybě: {e}")
        return None

# --- Hlavní část skriptu ---


# 1. Načtení programu
print("\n--- Načítání programu ---")
response_load = send_dashboard_command(f"load {PROGRAM_OPEN}")
# Jednoduchá kontrola úspěchu
if response_load and ("Loading program" in response_load or "File not found" not in response_load):
    print("Program pravděpodobně úspěšně načten (nebo již byl načten).")
    time.sleep(2)  # Dát robotu čas na zpracování

    # 2. Spuštění programu
    print("\n--- Spouštění programu ---")
    response_play = send_dashboard_command("play")
    if response_play and "Starting program" in response_play:
        print("Příkaz ke spuštění programu úspěšně odeslán.")
    else:
        print("Chyba při odesílání příkazu ke spuštění nebo neočekávaná odpověď.")

else:
    print(
        f"Nepodařilo se načíst program: {PROGRAM_OPEN}. Zkontrolujte název a cestu.")

print("\nSkript dokončen.")
