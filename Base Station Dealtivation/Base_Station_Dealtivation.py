import math
import random

def compute_bandwidth_for_rate(rate, snr_db):
    """Oblicza wymagane pasmo (MHz) aby uzyskać przepływność = rate [Mbit/s] 
       przy danym SNR (w dB) korzystając z wzoru c = b·log2(1+SNR_lin)."""
    snr_lin = 10**(snr_db/10)  # konwersja dB -> liniowe
    # Zamieniamy Mbit/s na bit/s i MHz -> Hz: zjednolicenie jednostek nie jest konieczne w obliczeniach względnych,
    # zakładamy, że log2 daje wynik w bitach na sekundę na Hz.
    return rate / math.log2(1 + snr_lin)

def scenario_two_stations(snr1_db, snr2_db, rates):
    """Scenariusz (a): Druga stacja aktywna. Wszyscy użytkownicy są obsługiwani przez stację 2,
       stacja 1 pozostaje z początkowym obciążeniem (2.5 MHz, 10 Mbit/s)."""
    B = 10.0  # MHz
    P1 = 460.0  # moc podstawowa [W]
    Delta = 4.2
    Psleep = 100.0
    # Oblicz pasmo potrzebne dla każdego użytkownika w stacji 2
    b2 = [compute_bandwidth_for_rate(r, snr2) for r, snr2 in zip(rates, snr2_db)]
    total_b2 = sum(b2)
    # Zajętość (względna):
    rho1 = 2.5 / B      # początkowa stacja 1 (0.25)
    rho2 = total_b2 / B
    # Oblicz moc obu stacji:
    P_sta1 = P1 + Delta * rho1
    P_sta2 = P1 + Delta * rho2
    total_power = P_sta1 + P_sta2
    total_rate = 10.0 + sum(rates)  # 10 Mbit/s (stacja 1 początkowo) + wymagania użytkowników
    EE = total_rate / total_power
    return {
        'rho1': rho1, 'rho2': rho2,
        'Power1': P_sta1, 'Power2': P_sta2,
        'TotalPower': total_power, 'TotalRate': total_rate, 'EE': EE
    }

def scenario_one_station(snr1_db, snr2_db, rates):
    """Scenariusz (b): Druga stacja wyłączona, wszyscy użytkownicy przeniesieni do stacji 1."""
    B = 10.0
    P1 = 460.0
    Delta = 4.2
    Psleep = 100.0
    # Wszyscy użytkownicy na stacji 1:
    b1 = [compute_bandwidth_for_rate(r, snr1) for r, snr1 in zip(rates, snr1_db)]
    total_b1 = 2.5 + sum(b1)  # sumujemy z początkowymi 2.5 MHz
    rho1 = total_b1 / B
    # Moc stacji 1 plus stacja 2 w trybie uśpienia:
    P_sta1 = P1 + Delta * rho1
    P_sta2 = Psleep
    total_power = P_sta1 + P_sta2
    total_rate = 10.0 + sum(rates)  # łączna przepływność
    EE = total_rate / total_power
    return {
        'rho1': rho1,
        'Power1': P_sta1, 'Power2': P_sta2,
        'TotalPower': total_power, 'TotalRate': total_rate, 'EE': EE
    }

def main():
    random.seed(0)  # dla powtarzalności przykładu
    num_users = 3
    # Losujemy wartości SNR i wymagane przepływności:
    snr1_db = [random.uniform(1,5) for _ in range(num_users)]
    snr2_db = [random.uniform(5,10) for _ in range(num_users)]
    rates   = [random.uniform(1,5) for _ in range(num_users)]
    print("SNR1 [dB]:", [f"{x:.2f}" for x in snr1_db])
    print("SNR2 [dB]:", [f"{x:.2f}" for x in snr2_db])
    print("Wymagane przepływności [Mbit/s]:", [f"{r:.2f}" for r in rates])

    res_a = scenario_two_stations(snr1_db, snr2_db, rates)
    res_b = scenario_one_station(snr1_db, snr2_db, rates)
    print("\nScenariusz (a) – 2 stacje aktywne:")
    print(f"  Zajętość pasma: st1 = {res_a['rho1']*100:.1f}%, st2 = {res_a['rho2']*100:.1f}%")
    print(f"  Moc: st1 = {res_a['Power1']:.1f} W, st2 = {res_a['Power2']:.1f} W, łącznie = {res_a['TotalPower']:.1f} W")
    print(f"  Efektywność energetyczna = {res_a['EE']:.4f} Mbit/J")

    print("\nScenariusz (b) – 1 stacja aktywna:")
    print(f"  Zajętość pasma (st1) = {res_b['rho1']*100:.1f}% (st2 uśpiona)")
    print(f"  Moc: st1 = {res_b['Power1']:.1f} W, st2 = {res_b['Power2']:.1f} W, łącznie = {res_b['TotalPower']:.1f} W")
    print(f"  Efektywność energetyczna = {res_b['EE']:.4f} Mbit/J")

if __name__ == "__main__":
    main()
