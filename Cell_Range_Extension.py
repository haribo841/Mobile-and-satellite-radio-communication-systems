import numpy as np
import matplotlib.pyplot as plt
import math

# — parametry stacji i anten
G_tx_macro = 18    # dBi
P_tx_macro = 46    # dBm
H_macro    = 40    # m

G_tx_micro = 12    # dBi
P_tx_micro = 30    # dBm
h_micro    = 5     # m

G_ue = 2           # dBi
u    = 2           # m

# — parametry kanału
D       = 1000          # m, odległość mikro(0)–makro(D)
n_users = 20

# — częstotliwość i pasmo
f  = 3.5e9      # Hz, 3.5 GHz
B  = 5e6        # Hz, 5 MHz
Nt = -174       # dBm/Hz (gęstość mocy szumu termicznego)

def fspl(d):
    """Free‐Space Path Loss [dB]"""
    return 20*np.log10(d) + 20*np.log10(f) - 147.55

def bandwidth_per_user(n_micro, n_macro):
    """Pasmo przydzielane równomiernie:
       - mikro dzieli B/4 między n_micro użytk.
       - makro dzieli B/10 między n_macro użytk."""
    B_s = (B/4) / n_micro if n_micro>0 else 0
    B_m = (B/10)/ n_macro if n_macro>0 else 0
    return B_m, B_s

def dbm_to_mw(p_dbm):
    return 10**(p_dbm/10)

def noise_dbm(bw_hz):
    """Szum termiczny w dBm = Nt (dBm/Hz) + 10log10(B)"""
    return Nt + 10*np.log10(bw_hz)

# pozycje użytkowników
np.random.seed(42)
user_pos = np.random.uniform(0, D, size=n_users)

def rx_powers(d):
    """Zwraca Pm, Ps [dBm] – moce odebrane od makro i mikro"""
    # odległości 3D
    dm = np.hypot(D-d, H_macro-u)
    ds = np.hypot(d,   h_micro-u)
    # moce odebrane
    Pm = P_tx_macro + G_tx_macro + G_ue - fspl(dm)
    Ps = P_tx_micro + G_tx_micro + G_ue - fspl(ds)
    return Pm, Ps

def user_throughput(d, CRE, n_micro, n_macro):
    """Przepływność pojedynczego użytkownika (bit/s)"""
    Pm, Ps = rx_powers(d)
    # przydział pasma
    Bm_user, Bs_user = bandwidth_per_user(n_micro, n_macro)
    # szumy
    N_m = dbm_to_mw(noise_dbm(Bm_user))
    N_s = dbm_to_mw(noise_dbm(Bs_user))
    # interferencja = moc od drugiej stacji (lin)
    I_m = dbm_to_mw(Ps)
    I_s = dbm_to_mw(Pm)
    # sygnał lin
    S_m = dbm_to_mw(Pm)
    S_s = dbm_to_mw(Ps + CRE)  # CRE dodajemy przy mikro
    # SINR liniowe
    sinr_m_lin = S_m / (I_m + N_m)
    sinr_s_lin = S_s / (I_s + N_s)
    # przepływność Shannona
    Rm = Bm_user * np.log2(1 + sinr_m_lin)
    Rs = Bs_user * np.log2(1 + sinr_s_lin)
    # wybieramy obsługującą stację
    return (Rm if Pm>=Ps else 0), (Rs if (Ps+CRE)>Pm else 0)

# symulacja dla CRE = 0,3,6,12 dB
CRE_values = [0, 3, 6, 12]
avg_rates = []

for CRE in CRE_values:
    # najpierw ustalamy przypisanie i liczymy, ilu jest przyłączonych do mikro/makro
    assign = []
    for d in user_pos:
        Pm, Ps = rx_powers(d)
        if Ps + CRE >= Pm:
            assign.append("micro")
        else:
            assign.append("macro")
    n_micro = assign.count("micro")
    n_macro = assign.count("macro")
    
    # sumujemy przepustowości
    rates = []
    for i, d in enumerate(user_pos):
        Rm, Rs = user_throughput(d, CRE, n_micro, n_macro)
        rates.append(Rm+Rs)
    avg_rates.append(np.mean(rates))

# rysujemy
plt.figure(figsize=(7,5))
plt.bar([str(c) for c in CRE_values], np.array(avg_rates)/1e6, edgecolor='k')
plt.xlabel("CRE [dB]")
plt.ylabel("Średnia przepływność [Mbps]")
plt.title("Symulacja: heterogeniczna sieć makro+mikro")
plt.grid(axis='y', lw=0.5, ls='--')
plt.show()
