import numpy as np
import matplotlib.pyplot as plt

# Parametry stacji i anten
G_tx_macro = 18    # dBi
P_tx_macro = 46    # dBm
H_macro    = 40    # m

G_tx_micro = 12    # dBi
P_tx_micro = 30    # dBm
h_micro    = 5     # m

G_ue = 2           # dBi
u    = 2           # m

# Parametry kanału
D       = 1000          # m, odległość mikro(0)–makro(D)
n_users = 20

# Częstotliwość i pasmo
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
    micro_bandwidth = (B/4) / n_micro if n_micro>0 else 0
    macro_bandwidth = (B/10)/ n_macro if n_macro>0 else 0
    return macro_bandwidth, micro_bandwidth

def dbm_to_mw(p_dbm):
    return 10**(p_dbm/10)

def noise_dbm(bw_hz):
    """Szum termiczny w dBm = Nt (dBm/Hz) + 10log10(B)"""
    return Nt + 10*np.log10(bw_hz)

# pozycje użytkowników
rng = np.random.default_rng(42)
user_pos = rng.uniform(0, D, size=n_users)

def rx_powers(d):
    """Zwraca Pm, Ps [dBm] – moce odebrane od makro i mikro"""
    # odległości 3D
    dm = np.hypot(D-d, H_macro-u)
    ds = np.hypot(d,   h_micro-u)
    # moce odebrane
    macro_power_dbm = P_tx_macro + G_tx_macro + G_ue - fspl(dm)
    micro_power_dbm = P_tx_micro + G_tx_micro + G_ue - fspl(ds)
    return macro_power_dbm, micro_power_dbm

def user_throughput(d, cre_db, n_micro, n_macro):
    """Przepływność pojedynczego użytkownika (bit/s)"""
    macro_power_dbm, micro_power_dbm = rx_powers(d)
    # przydział pasma
    macro_bandwidth, micro_bandwidth = bandwidth_per_user(n_micro, n_macro)
    # szumy
    macro_noise = dbm_to_mw(noise_dbm(macro_bandwidth))
    micro_noise = dbm_to_mw(noise_dbm(micro_bandwidth))
    # interferencja = moc od drugiej stacji (lin)
    macro_interference = dbm_to_mw(micro_power_dbm)
    micro_interference = dbm_to_mw(macro_power_dbm)
    # sygnał lin
    macro_signal = dbm_to_mw(macro_power_dbm)
    micro_signal = dbm_to_mw(micro_power_dbm + cre_db)  # CRE dodajemy przy mikro
    # SINR liniowe
    sinr_m_lin = macro_signal / (macro_interference + macro_noise)
    sinr_s_lin = micro_signal / (micro_interference + micro_noise)
    # przepływność Shannona
    macro_rate = macro_bandwidth * np.log2(1 + sinr_m_lin)
    micro_rate = micro_bandwidth * np.log2(1 + sinr_s_lin)
    # wybieramy obsługującą stację
    return (
        macro_rate if macro_power_dbm >= micro_power_dbm else 0,
        micro_rate if micro_power_dbm + cre_db > macro_power_dbm else 0,
    )

# symulacja dla CRE = 0,3,6,12 dB
CRE_values = [0, 3, 6, 12]
avg_rates = []

for cre_db in CRE_values:
    # najpierw ustalamy przypisanie i liczymy, ilu jest przyłączonych do mikro/makro
    assign = []
    for d in user_pos:
        macro_power_dbm, micro_power_dbm = rx_powers(d)
        if micro_power_dbm + cre_db >= macro_power_dbm:
            assign.append("micro")
        else:
            assign.append("macro")
    n_micro = assign.count("micro")
    n_macro = assign.count("macro")
    
    # sumujemy przepustowości
    rates = []
    for d in user_pos:
        macro_rate, micro_rate = user_throughput(d, cre_db, n_micro, n_macro)
        rates.append(macro_rate + micro_rate)
    avg_rates.append(np.mean(rates))

# rysujemy
plt.figure(figsize=(7,5))
plt.bar([str(c) for c in CRE_values], np.array(avg_rates)/1e6, edgecolor='k')
plt.xlabel("CRE [dB]")
plt.ylabel("Średnia przepływność [Mbps]")
plt.title("Symulacja: heterogeniczna sieć makro+mikro")
plt.grid(axis='y', lw=0.5, ls='--')
plt.show()
