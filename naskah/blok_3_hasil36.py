# ---- blok 3: hasil 3.6 diagnostik mekanisme + Tabel 5 - disisipkan sebelum Diskusi ----
H("3.6. Mechanistic diagnosis of the leaf-area response", 2)
d22, d20 = dek[("S2022", "60")], dek[("S2020", "FL")]
P(f"Tiller number explained only {100 * d22['porsi_anakan']:.0f}% (DS 2022, 60 DAT) and {100 * d20['porsi_anakan']:.0f}% "
  f"(2020, flowering) of the log-reduction of LAI in the 0-N plots; the remainder came from a smaller leaf area per tiller "
  f"(ratios {d22['rasio_luas_per_anakan']:.2f} and {d20['rasio_luas_per_anakan']:.2f}), i.e. fewer, shorter or narrower "
  f"and thicker leaves (Table 5). Early in the season (2020, 35 DAT) the tiller contribution was larger "
  f"({100 * dek[('S2020', '35')]['porsi_anakan']:.0f}%). Leaf greenness was reduced by only {spad_red[0]:.0f}% at 35 DAT and "
  f"{spad_red[1]:.0f}% at flowering while LAI was reduced by {lai_red_obs[2]:.0f}% and {lai_red_obs[3]:.0f}%, and the biomass per "
  f"unit leaf area of the 0-N crop was {bpl[('S2022', '35')]:.2f} and {bpl[('S2022', '60')]:.2f} times that of the 140-N crop "
  "(DS 2022, 35 and 60 DAT). The observed crop therefore conserved N per unit leaf area and adjusted leaf area.")
P(f"The standard model did the opposite: it kept LAI nearly unchanged (ratios {strat[('S2022', 'std', '60')]['sim_rasio_LAI']:.2f} "
  f"and {strat[('S2020', 'std', 'FL')]['sim_rasio_LAI']:.2f}) and diluted specific leaf N by {min(sln_red_std):.0f}–"
  f"{max(sln_red_std):.0f}%, which lowered leaf photosynthetic capacity through the AMAX(SLN) relationship; biomass per "
  f"unit leaf area did not change (ratio {strat[('S2022', 'std', '60')]['sim_rasio_WLV_per_LAI']:.2f}). With the NLEAF "
  f"extension, SLN ratios rose to {min(sln_ratio_ext):.2f}–{max(sln_ratio_ext):.2f} and leaf mass per leaf area increased "
  f"({strat[('S2022', 'ext', '60')]['sim_rasio_WLV_per_LAI']:.2f} and {strat[('S2020', 'ext', 'FL')]['sim_rasio_WLV_per_LAI']:.2f}), "
  "moving the simulated strategy towards the observed one. The reduction of LAI lowered the intercepted fraction of "
  f"radiation from {inter['S2022']['f_int140']:.2f} to {inter['S2022']['f_int0']:.2f} in DS 2022 (ratio "
  f"{inter['S2022']['rasio_intersepsi']:.2f}), which explains only part of the yield ratio ({inter['S2022']['rasio_hasil']:.2f}); "
  f"the residual factor ({inter['S2022']['rasio_hasil_per_intersepsi']:.2f}) reflects lower radiation-use efficiency and sink "
  f"size. In 2020 the yield ratio ({inter['S2020']['rasio_hasil']:.2f}) exceeded the interception ratio "
  f"({inter['S2020']['rasio_intersepsi']:.2f}), consistent with the under-performing NPK plot of that season.")
TABLE("Table 5. Mechanistic diagnosis of the 0-N/140-N contrast in the LTFE (observed vs simulated ratios).",
      ["Quantity", "DS 2022, 60 DAT obs.", "8.1", "8.1+NLEAF", "2020, flowering obs.", "8.1", "8.1+NLEAF"],
      [["LAI ratio", f2(d22["rasio_LAI"]), f2(strat[("S2022", "std", "60")]["sim_rasio_LAI"]), f2(strat[("S2022", "ext", "60")]["sim_rasio_LAI"]),
        f2(d20["rasio_LAI"]), f2(strat[("S2020", "std", "FL")]["sim_rasio_LAI"]), f2(strat[("S2020", "ext", "FL")]["sim_rasio_LAI"])],
       ["Tiller-number ratio", f2(d22["rasio_anakan"]), "–", "–", f2(d20["rasio_anakan"]), "–", "–"],
       ["Leaf area per tiller ratio", f2(d22["rasio_luas_per_anakan"]), "–", "–", f2(d20["rasio_luas_per_anakan"]), "–", "–"],
       ["Share of ln LAI ratio due to tillers", f"{100 * d22['porsi_anakan']:.0f}%", "–", "–", f"{100 * d20['porsi_anakan']:.0f}%", "–", "–"],
       ["Leaf N per area ratio (SPAD obs.; SLN sim.)", "n.a.", f2(strat[("S2022", "std", "60")]["sim_rasio_SLN"]), f2(strat[("S2022", "ext", "60")]["sim_rasio_SLN"]),
        f2(strat[("S2020", "std", "FL")]["obs_rasio_SPAD"]), f2(strat[("S2020", "std", "FL")]["sim_rasio_SLN"]), f2(strat[("S2020", "ext", "FL")]["sim_rasio_SLN"])],
       ["Biomass (leaf mass) per leaf area ratio", f2(bpl[("S2022", "60")]), f2(strat[("S2022", "std", "60")]["sim_rasio_WLV_per_LAI"]),
        f2(strat[("S2022", "ext", "60")]["sim_rasio_WLV_per_LAI"]), "n.a.", f2(strat[("S2020", "std", "FL")]["sim_rasio_WLV_per_LAI"]),
        f2(strat[("S2020", "ext", "FL")]["sim_rasio_WLV_per_LAI"])],
       ["Interception ratio (k = 0.6) / yield ratio", f"{inter['S2022']['rasio_intersepsi']:.2f} / {inter['S2022']['rasio_hasil']:.2f}", "–", "–",
        f"{inter['S2020']['rasio_intersepsi']:.2f} / {inter['S2020']['rasio_hasil']:.2f}", "–", "–"]],
      widths=[4.6, 2.2, 1.4, 1.8, 2.3, 1.4, 1.8], fs=8,
      note="Observed tiller counts, leaf area and SPAD from Susanti et al. (2023, Tables 2–3) and Hikmah et al. (2021, Table 3). "
           "Observed biomass per leaf area uses above-ground dry matter; simulated values use leaf dry mass (WLV/LAI). n.a., not reported.")
