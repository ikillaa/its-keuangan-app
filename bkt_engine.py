def hitung_skor_baru(skor_lama, is_benar):
    """
    Fungsi ini mengimplementasikan Bayesian Knowledge Tracing (BKT).
    Tugasnya mengupdate probabilitas siswa menguasai skill.
    """
    
    # --- PARAMETER BKT ---
    p_transit = 0.1  
    p_guess = 0.2    
    p_slip = 0.1     

    # --- LOGIKA UTAMA ---
    if is_benar:
        # Jika jawaban BENAR
        p_learned_given_evidence = (skor_lama * (1 - p_slip)) / \
                                   ((skor_lama * (1 - p_slip)) + ((1 - skor_lama) * p_guess))
    else:
        # Jika jawaban SALAH
        p_learned_given_evidence = (skor_lama * p_slip) / \
                                   ((skor_lama * p_slip) + ((1 - skor_lama) * (1 - p_guess)))

    # Update terakhir
    skor_baru = p_learned_given_evidence + ((1 - p_learned_given_evidence) * p_transit)
    
    return skor_baru