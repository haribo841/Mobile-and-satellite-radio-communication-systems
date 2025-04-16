import numpy as np
import matplotlib.pyplot as plt
import math

# Parametry systemu
D = 1000                      # odległość między stacją mikro (0) a makro (1000 m)
n_users = 20                  # liczba użytkowników
f = 3.5e9                     # częstotliwość [Hz]
# Stałe: logarytm dziesiętny, FSPL wyrażone w dB
def fspl(d):
    # FSPL [dB] = 20*log10(d) + 20*log10(f) - 147.55, gdzie d w metrach
    return 20 * np.log10(d) + 20 * np.log10(f) - 147.55

# Parametry stacji i anten (w dBm i dBi)
P_tx_micro = 30             # moc nadawcza mikro [dBm]
G_tx_micro = 12             # zysk anteny stacji mikro [dBi]
P_tx_macro = 46             # moc nadawcza makro [dBm]
G_tx_macro = 18             # zysk anteny stacji makro [dBi]
G_ue = 2                    # zysk anteny użytkownika [dBi]

# Wysokości
h_micro = 5                 # wysokość stacji mikro [m]
H_macro = 40                # wysokość stacji makro [m]
u = 2                       # wysokość użytkownika [m]

# Pasma przydzielane użytkownikom (w Hz)
B_total = 5e6               # całkowite pasmo [Hz]
B_user_micro = B_total / 4  # 1.25 MHz dla stacji mikro
B_user_macro = B_total / 10 # 0.5 MHz dla stacji makro

# Generujemy losowo położenie użytkowników (jeden wymiar: x między 0 a D)
np.random.seed(42) # dla powtarzalności wyników
user_positions = np.random.uniform(0, D, n_users)

def calc_received_power(x, bs_position, bs_height, P_tx, G_tx):
    # Obliczamy odległość euklidesową między użytkownikiem a stacją
    # dla mikro: bs_position = 0, bs_height = h_micro; dla makro: bs_position = D, bs_height = H_macro.
    horizontal_dist = abs(x - bs_position)
    vertical_diff = abs(bs_height - u)
    d = np.sqrt(horizontal_dist**2 + vertical_diff**2)
    path_loss = fspl(d)
    # Suma mocy + zyski minus stratę propagacji
    P_rx = P_tx + G_tx + G_ue - path_loss
    return P_rx, d

# Funkcja licząca przepływność użytkownika
def calc_throughput(P_rx_serving_dBm, P_rx_interferer_dBm, bandwidth):
    # Konwersja mocy z dBm na mW:
    S_mW = 10**(P_rx_serving_dBm/10)
    I_mW = 10**(P_rx_interferer_dBm/10)
    # SINR = S/I (bez uwzględnienia szumu)
    SINR = S_mW / I_mW if I_mW > 0 else 1e9
    # Przepływność R = B · log2(1 + SINR)
    R = bandwidth * math.log2(1 + SINR)  # [bit/s]
    return R

# Lista wartości CRE, dla których przeprowadzamy symulację (w dB)
CRE_values = [0, 3, 6, 12]

# Aby zebrać średnią przepływność dla każdej wartości CRE
avg_throughputs = []

# Pętla po wartościach CRE
for CRE in CRE_values:
    # Listy przechowujące wyniki dla tej wartości CRE
    throughputs = np.zeros(n_users)
    # Najpierw wyznacz przypisanie użytkowników – aby wyliczyć zasoby (liczba użytkowników przyłączonych do każdej stacji)
    assignment = []  # "micro" lub "macro"
    for x in user_positions:
        # Moc odebrana od stacji mikro i makro
        P_rx_micro, d_micro = calc_received_power(x, bs_position=0, bs_height=h_micro, 
                                                    P_tx=P_tx_micro, G_tx=G_tx_micro)
        P_rx_macro, d_macro = calc_received_power(x, bs_position=D, bs_height=H_macro, 
                                                    P_tx=P_tx_macro, G_tx=G_tx_macro)
        # Doliczamy CRE do mocy mikro
        if (P_rx_micro + CRE) >= P_rx_macro:
            assignment.append("micro")
        else:
            assignment.append("macro")
    
    # Policz, ile użytkowników jest przyłączonych do każdej stacji
    n_micro = assignment.count("micro")
    n_macro = assignment.count("macro")
    # Unikamy dzielenia przez zero
    bw_micro_user = B_user_micro / n_micro if n_micro > 0 else 0
    bw_macro_user = B_user_macro / n_macro if n_macro > 0 else 0

    # Dla każdego użytkownika liczymy przepływność
    for i, x in enumerate(user_positions):
        P_rx_micro, d_micro = calc_received_power(x, bs_position=0, bs_height=h_micro, 
                                                    P_tx=P_tx_micro, G_tx=G_tx_micro)
        P_rx_macro, d_macro = calc_received_power(x, bs_position=D, bs_height=H_macro, 
                                                    P_tx=P_tx_macro, G_tx=G_tx_macro)
        if assignment[i] == "micro":
            serving_power = P_rx_micro
            interfering_power = P_rx_macro
            allocated_bw = bw_micro_user
        else:
            serving_power = P_rx_macro
            interfering_power = P_rx_micro
            allocated_bw = bw_macro_user

        # Obliczamy przepływność – wynik w Mbps
        R = calc_throughput(serving_power, interfering_power, allocated_bw) / 1e6
        throughputs[i] = R

    avg_throughput = np.mean(throughputs)
    avg_throughputs.append(avg_throughput)
    print(f"CRE = {CRE} dB: liczba przyłączonych: mikro = {n_micro}, makro = {n_macro}, średnia przepływność = {avg_throughput:.3f} Mbps")

# Wykres słupkowy
plt.figure(figsize=(8, 5))
plt.bar([str(c) for c in CRE_values], avg_throughputs, color='skyblue')
plt.xlabel("CRE [dB]")
plt.ylabel("Średnia przepływność [Mbps]")
plt.title("Średnia przepływność użytkowników dla różnych wartości CRE")
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()
