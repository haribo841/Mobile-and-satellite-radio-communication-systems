import numpy as np
import matplotlib.pyplot as plt

def steering_vector(angle_deg, num_elements, element_spacing_ratio):
    """
    Oblicza wektor sterujący dla ULA (Uniform Linear Array).

    Args:
        angle_deg (float): Kąt (w stopniach).
        num_elements (int): Liczba elementów anteny.
        element_spacing_ratio (float): Stosunek odległości między elementami
                                       do długości fali (np. 0.5 dla d=lambda/2).
    Returns:
        np.ndarray: Wektor sterujący (kolumnowy).
    """
    angle_rad = np.radians(angle_deg)
    m_indices = np.arange(num_elements)
    sv = np.exp(1j * 2 * np.pi * element_spacing_ratio * m_indices * np.sin(angle_rad))
    return sv[:, np.newaxis]  # zwracamy wektor kolumnowy (L x 1)

def plot_mvdr_beampattern(L, d_ratio, soi_angle_deg, snoi_angles_deg, snr_db, inr_db):
    """
    Oblicza i rysuje charakterystykę promieniowania (beampattern) dla beamformera MVDR.
    Wyświetla pół-koło od -90° do +90° z 0° u góry.
    """
    # 1) Konwersja mocy z dB do liniowego (zakładamy noise_power = 1)
    noise_power = 1.0
    soi_power = noise_power * (10 ** (snr_db / 10.0))
    snoi_power = noise_power * (10 ** (inr_db / 10.0))

    # 2) Wektor sterujący dla sygnału pożądanego (SOI)
    a_soi = steering_vector(soi_angle_deg, L, d_ratio)

    # 3) Budowa macierzy kowariancji zakłóceń + szumu R_in
    R_in = np.zeros((L, L), dtype=complex)
    for angle_deg in snoi_angles_deg:
        a_int = steering_vector(angle_deg, L, d_ratio)
        R_in += snoi_power * (a_int @ a_int.conj().T)
    R_in += noise_power * np.eye(L)

    # 4) Obliczenie wag MVDR wg wzoru: (R_in^{-1} a_soi) / (a_soi^H R_in^{-1} a_soi)
    try:
        R_in_inv = np.linalg.inv(R_in)
    except np.linalg.LinAlgError:
        # Jeśli R_in jest osobliwa, dodajemy niewielką wartość na przekątnej (regularizacja)
        R_in += np.eye(L) * 1e-6
        R_in_inv = np.linalg.inv(R_in)

    numerator = R_in_inv @ a_soi
    denominator = (a_soi.conj().T @ R_in_inv @ a_soi).item()
    weights = numerator / denominator  # wektor wag MVDR (L x 1)

    # 5) Skanowanie kątowe od -90° do +90° (np. co 0.5° → 361 próbek)
    phi_scan_deg = np.linspace(-90, 90, 361)
    beampattern_db = np.zeros(len(phi_scan_deg))

    for i, angle_deg in enumerate(phi_scan_deg):
        a_scan = steering_vector(angle_deg, L, d_ratio)        # (L x 1)
        response = (weights.conj().T @ a_scan).item()           # zespolony skalar
        power = np.abs(response) ** 2
        beampattern_db[i] = 10 * np.log10(power + 1e-12)        # +1e-12, żeby uniknąć log(0)

    # 6) Normalizacja: maksimum = 0 dB
    beampattern_db_normalized = beampattern_db - np.max(beampattern_db)

    # 7) Rysowanie pół-koła w układzie biegunowym (−90°…+90°, 0° u góry)
    plt.figure(figsize=(8, 7))
    ax = plt.subplot(111, projection='polar')
    phi_scan_rad = np.radians(phi_scan_deg)

    ax.plot(phi_scan_rad, beampattern_db_normalized, linewidth=1.5)

    # Ustawienia osi kątowej: 0° u góry („N”), skala rośnie zgodnie z ruchem wskazówek zegara
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_thetamin(-90)
    ax.set_thetamax(90)

    # Ustawienia osi radialnej: od -60 dB do 0 dB
    r_min = -60
    ax.set_rlim(bottom=r_min, top=0)
    ax.set_yticks(np.arange(r_min, 1, 10))  # etykiety co 10 dB

    # Etykiety kątowe co 30°: –90, –60, –30, 0, 30, 60, 90
    deg_ticks = np.arange(-90, 91, 30)
    ax.set_xticks(np.deg2rad(deg_ticks))
    ax.set_xticklabels([f"{d}°" for d in deg_ticks])

    title_str = (
        f"MVDR Beampattern (L={L}, d={d_ratio}λ, SOI={soi_angle_deg}°)\n"
        f"SNOI @ {snoi_angles_deg}°, SNR={snr_db}dB, INR={inr_db}dB"
    )
    ax.set_title(title_str, va='bottom', fontsize=12)
    ax.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    # Domyślne parametry zgodne z przykładem na slajdzie:
    default_L            = 8
    default_d_ratio      = 0.5
    default_soi_angle    = 0.0
    default_snoi_angles  = [-30.0, -15.0, 15.0, 30.0]
    default_snr_db       = 10.0
    default_inr_db       = 10.0

    # Interaktywne pytanie do użytkownika (naciśnięcie Enter → wartość domyślna)
    try:
        user_L = input(f"Podaj liczbę elementów anteny L (domyślnie {default_L}): ")
        L_elements = int(user_L) if user_L.strip() else default_L

        user_d = input(f"Podaj spacing d/λ (domyślnie {default_d_ratio}): ")
        d_lambda_ratio = float(user_d) if user_d.strip() else default_d_ratio

        user_soi = input(f"Podaj kąt SOI w stopniach (domyślnie {default_soi_angle}°): ")
        soi_direction = float(user_soi) if user_soi.strip() else default_soi_angle

        user_snoi = input(f"Podaj kąty SNOI w stopniach oddzielone przecinkami (domyślnie {','.join(map(str, default_snoi_angles))}): ")
        if user_snoi.strip():
            snoi_list = [float(x.strip()) for x in user_snoi.split(',')]
        else:
            snoi_list = default_snoi_angles

        user_snr = input(f"Podaj SNR (dB) dla SOI (domyślnie {default_snr_db}dB): ")
        snr_db_val = float(user_snr) if user_snr.strip() else default_snr_db

        user_inr = input(f"Podaj INR (dB) dla każdego SNOI (domyślnie {default_inr_db}dB): ")
        inr_db_val = float(user_inr) if user_inr.strip() else default_inr_db

    except ValueError:
        print("Błędna wartość wejściowa. Używam wartości domyślnych.")
        L_elements     = default_L
        d_lambda_ratio = default_d_ratio
        soi_direction  = default_soi_angle
        snoi_list      = default_snoi_angles
        snr_db_val     = default_snr_db
        inr_db_val     = default_inr_db

    plot_mvdr_beampattern(
        L_elements,
        d_lambda_ratio,
        soi_direction,
        snoi_list,
        snr_db_val,
        inr_db_val
    )
