"""Integrasi dataset independen kedua (Marpaung et al. 2024: dosis N pada Inpari-32 sendiri, Karangploso,
Malang, MK 2023) ke buat_naskah.py: Tabel 1, metode 2.2/2.3/2.8/2.9, hasil 3.4 (+Tabel 5 baru; Tabel 5 lama
-> Tabel 6), hasil 3.5 (NLEAF diperbarui), diskusi 4.4, keterbatasan 4.7, abstrak. Semua angka dibaca dari
data/lapangan/validasi_marpaung_karangploso.json dan marpaung2024_karangploso_inpari32.json saat naskah dibangun."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
F = HERE / "buat_naskah.py"
s = F.read_text(encoding="utf-8")

# ---- 0. muat data + turunan (setelah blok pemuatan JSON)
old = 'MEK = J("mekanisme_n_daun.json")'
new = '''MEK = J("mekanisme_n_daun.json")
MAR = J("validasi_marpaung_karangploso.json"); MRD = J("marpaung2024_karangploso_inpari32.json")
_mo = MAR["observasi"]
mar_rmse = {m: (sum((MAR[m]["rLAI"][a] - _mo["rLAI"][a]) ** 2 for a in ("28", "42", "56")) / 3) ** 0.5
            for m in ("std", "ext")}
_mnj = MRD["tabel9_N_jaringan"]["N_jaringan_persen"]
mar_nj0 = _mnj["P1"]; mar_njF = sum(v for k, v in _mnj.items() if k != "P1") / 9
_mt = {k: v[3] for k, v in MRD["tabel4_jumlah_anakan_per_rumpun"].items() if k.startswith("P")}
_ml = {k: v[3] for k, v in MRD["tabel3_luas_daun_cm2_per_rumpun"].items() if k.startswith("P")}
_m100 = [k for k, d in MRD["perlakuan_N_kg_ha"].items() if d == 100]
mar_rtil = _mt["P1"] / (sum(_mt[k] for k in _m100) / 3)
mar_rlpt = (_ml["P1"] / _mt["P1"]) / (sum(_ml[k] for k in _m100) / 3 / (sum(_mt[k] for k in _m100) / 3))
MARU = MAR["pembaruan_NLEAF"]'''
assert old in s, "anchor muat data"
s = s.replace(old, new)

# ---- 1. Tabel 1: baris dataset baru + teks 2.2 (tanggal tanam + ekstraksi tabel)
old = '''       ["Hikmah et al. (2021)", "LTFE Sukamandi; Jul–Dec 2020", "Inpari-33", "0 N vs NPK (140 kg N ha⁻¹)",
        "Grain; leaf area at 21/35 DAT and flowering", "Independent validation"]],'''
new = '''       ["Hikmah et al. (2021)", "LTFE Sukamandi; Jul–Dec 2020", "Inpari-33", "0 N vs NPK (140 kg N ha⁻¹)",
        "Grain; leaf area at 21/35 DAT and flowering", "Independent validation"],
       ["Marpaung et al. (2024)", "Karangploso (Malang), East Java; DS 2023", "Inpari-32",
        "0 (unfertilised) vs 50, 100, 150 kg N ha⁻¹ (× PGPR)",
        "Grain; leaf area, tillers, biomass at 14/28/42/56 DAT; tissue N", "Independent validation (same variety)"]],'''
assert old in s, "anchor Tabel 1"
s = s.replace(old, new)

old = '"were assumed (1 May 2016; 22 November 2017; 1 May 2022; 2 August 2020); the sensitivity of all results to ±21 days "'
new = '"were assumed (1 May 2016; 22 November 2017; 1 May 2022; 2 August 2020; 15 May 2023); the sensitivity of all results to ±21 days "'
assert old in s, "anchor tanggal tanam"
s = s.replace(old, new)

# ---- 2. 2.3 cuaca: pemangkasan hujan ekstrem
old = 'P("Daily weather was taken from Open-Meteo (ERA5-based reanalysis; Hersbach et al., 2020) at each site; NASA POWER was "'
new = 'P("Daily weather was taken from Open-Meteo (ERA5-based reanalysis; Hersbach et al., 2020) at each site, with daily rainfall capped at the PCSE input limit of 250 mm (one day at Karangploso); NASA POWER was "'
assert old in s, "anchor cuaca"
s = s.replace(old, new)

# ---- 3. 2.8 evaluasi: protokol dataset kedua
old = '''Transfer to the farmers' fields of the 2016 "
  "experiments (126 kg N ha⁻¹) was also tested.")'''
new = '''Transfer to the farmers' fields of the 2016 "
  "experiments (126 kg N ha⁻¹) was also tested. A second independent dataset became available for Inpari-32 itself: "
  "an N-rate trial (0, 50, 100, 150 kg N ha⁻¹) at Karangploso, East Java (≈500 m elevation), DS 2023 "
  + C("marpaung2024") + ", with leaf area, tillers and biomass at 14–56 DAT read directly from the published tables "
  "(no digitising). The same stage-B protocol was applied without any phenological adjustment: NSOILBASE was estimated "
  "from the 0-N yield alone and the yield response and the 0-N/100-N ratios of LAI and biomass were then predicted "
  "blind. Two confounders are noted: the control received no P, K or PGPR, and all fertilised plots received PGPR "
  "(differences among PGPR concentrations were not significant for almost all variables), so part of the yield response "
  "to the first 50 kg N ha⁻¹ includes P, K and PGPR effects; the unreported transplanting date and fertiliser "
  "timing were assumed and varied (±14 days; alternative splits).")'''
assert old in s, "anchor 2.8"
s = s.replace(old, new)

# ---- 4. 2.9: pembaruan sekuensial
old = '''Robustness to the observation model was tested by recalibrating with the ratio errors halved, "
  "doubled, or without ratio data.'''
new = '''Robustness to the observation model was tested by recalibrating with the ratio errors halved, "
  "doubled, or without ratio data. The posterior of the extension was additionally propagated to the Karangploso trial "
  "(64 draws, NSOILBASE re-estimated from the 0-N yield per draw) and then updated with its three LAI ratios by "
  "importance sampling (sequential Bayesian updating), which narrows the NLEAF interval without re-running the chain.'''
assert old in s, "anchor 2.9"
s = s.replace(old, new)

# ---- 5. Tabel 5 lama -> Tabel 6 (dua kemunculan di 3.6)
s = s.replace('f"and thicker leaves (Table 5). Early in the season', 'f"and thicker leaves (Table 6). Early in the season')
s = s.replace('TABLE("Table 5. Mechanistic diagnosis of the 0-N/140-N contrast in the LTFE (observed vs simulated ratios).",',
              'TABLE("Table 6. Mechanistic diagnosis of the 0-N/140-N contrast in the LTFE (observed vs simulated ratios).",')

# ---- 6. 3.4: paragraf + Tabel 5 baru sebelum paragraf transfer 2016
old = '''P(f"At the three farmers' fields of 2016, the Sukamandi N supply led to yield underestimates of "'''
new = '''P(f"The Karangploso N-rate trial on Inpari-32 itself confirmed this picture on an independent site, season and "
  f"soil (Table 5). With TSUM unchanged (same variety), simulated maturity was {MAR['ext']['DOM_0N']:.0f} DAT against "
  "the reported 120 DAT. NSOILBASE estimated from the unfertilised plot was "
  f"{MAR['std']['NSOILBASE_fit']:.0f} (standard) and {MAR['ext']['NSOILBASE_fit']:.0f} kg N ha⁻¹ (extension), "
  f"below the Sukamandi values ({f1(ps['NSOILBASE'])}–{f1(pe['NSOILBASE'])} kg N ha⁻¹), as expected for a "
  "different soil. The observed 0-N/100-N LAI ratio fell to "
  f"{_mo['rLAI']['42']:.2f} at 42 DAT, whereas the standard model again predicted almost no leaf-area response "
  f"({MAR['std']['rLAI']['42']:.2f}–{MAR['std']['rLAI']['28']:.2f}); the extension, blind, gave "
  f"{MAR['ext']['rLAI']['56']:.2f}–{MAR['ext']['rLAI']['28']:.2f} (RMSE {mar_rmse['ext']:.2f} versus "
  f"{mar_rmse['std']:.2f}; posterior-mean CRPS {MAR['ext']['prediksi_posterior']['crps_rasio_LAI_rata2']:.3f} versus "
  f"{MAR['std']['prediksi_posterior']['crps_rasio_LAI_rata2']:.3f}). Both models under-predicted the yield response to "
  f"the first 50 kg N ha⁻¹ ({MAR['std']['rY']['50']:.2f} against {_mo['rY']['50']:.2f} observed), which is "
  "expected because the unfertilised control also lacked P, K and PGPR (Section 2.8), so the observed response is not "
  "an N response alone. Two independent observations support the conserved-leaf-N strategy directly: tissue N of the "
  f"unfertilised plants was {mar_nj0:.2f}% against {mar_njF:.2f}% in fertilised plants (a {100 * (1 - mar_nj0 / mar_njF):.0f}% "
  f"reduction, while leaf area at 56 DAT fell by {100 * (1 - _mo['rLAI']['56']):.0f}%), and the leaf-area reduction was "
  f"almost entirely a tiller-number effect (tiller ratio {mar_rtil:.2f}; leaf area per tiller ratio {mar_rlpt:.2f}), "
  "the extreme of the plasticity hierarchy seen in the LTFE (Section 3.6).")
TABLE("Table 5. Blind prediction of the second independent dataset: N-rate trial on Inpari-32, Karangploso, DS 2023 "
      "(Marpaung et al., 2024). NSOILBASE fitted on the 0-N yield only; all ratios predicted blind (dose means over "
      "PGPR concentrations).",
      ["Quantity", "Observed", "8.1", "8.1+NLEAF"],
      [["Yield ratio 50N/0N", f2(_mo["rY"]["50"]), f2(MAR["std"]["rY"]["50"]), f2(MAR["ext"]["rY"]["50"])],
       ["Yield ratio 100N/0N", f2(_mo["rY"]["100"]), f2(MAR["std"]["rY"]["100"]), f2(MAR["ext"]["rY"]["100"])],
       ["Yield ratio 150N/0N", f2(_mo["rY"]["150"]), f2(MAR["std"]["rY"]["150"]), f2(MAR["ext"]["rY"]["150"])],
       ["LAI ratio 0N/100N, 28 DAT", f2(_mo["rLAI"]["28"]), f2(MAR["std"]["rLAI"]["28"]), f2(MAR["ext"]["rLAI"]["28"])],
       ["LAI ratio 0N/100N, 42 DAT", f2(_mo["rLAI"]["42"]), f2(MAR["std"]["rLAI"]["42"]), f2(MAR["ext"]["rLAI"]["42"])],
       ["LAI ratio 0N/100N, 56 DAT", f2(_mo["rLAI"]["56"]), f2(MAR["std"]["rLAI"]["56"]), f2(MAR["ext"]["rLAI"]["56"])],
       ["Biomass ratio 0N/100N, 28/42/56 DAT", f"{f2(_mo['rDM']['28'])} / {f2(_mo['rDM']['42'])} / {f2(_mo['rDM']['56'])}",
        f"{f2(MAR['std']['rDM']['28'])} / {f2(MAR['std']['rDM']['42'])} / {f2(MAR['std']['rDM']['56'])}",
        f"{f2(MAR['ext']['rDM']['28'])} / {f2(MAR['ext']['rDM']['42'])} / {f2(MAR['ext']['rDM']['56'])}"],
       ["NSOILBASE from 0-N plot (kg N ha⁻¹)", "–", f1(MAR["std"]["NSOILBASE_fit"]), f1(MAR["ext"]["NSOILBASE_fit"])],
       ["Maturity (DAT; reported 120)", "120", f0(MAR["std"]["DOM_0N"]), f0(MAR["ext"]["DOM_0N"])]],
      widths=[4.6, 3.2, 2.6, 2.8], fs=8,
      note="Confounders: the control received no P, K or PGPR and all fertilised plots received PGPR, so the observed "
           "yield response includes non-N effects; LAI from leaf area per hill (16 hills m⁻²); dry matter from "
           "grain at 14% moisture × 0.86. Results were robust to the assumed transplanting date (±14 d) and "
           "fertiliser split (Section 2.8).")
P(f"At the three farmers' fields of 2016, the Sukamandi N supply led to yield underestimates of "'''
assert old in s, "anchor 3.4"
s = s.replace(old, new, 1)

# ---- 7. 3.5: NLEAF diperbarui (setelah kalimat NLEAF Table 2)
old = '''f"was {ci('ext', 'NLEAF', f2)} (Table 2).'''
new = '''f"was {ci('ext', 'NLEAF', f2)} (Table 2); sequential updating with the three Karangploso LAI ratios narrowed it to "
  f"{MARU['NLEAF_sesudah'][1]:.2f} [{MARU['NLEAF_sesudah'][0]:.2f}, {MARU['NLEAF_sesudah'][2]:.2f}] "
  f"(importance sampling, effective sample size {MARU['ESS']:.0f}).'''
assert old in s, "anchor 3.5 NLEAF"
s = s.replace(old, new)

# ---- 8. 4.4 INS: variasi spasial Karangploso
old = '"publications, so soil tests did not explain the difference.")'
anchor2 = s.find('H("4.4.')
i = s.find('so soil tests did not explain the difference', anchor2)
# kalimat 4.4 berbeda; cari kalimatnya di 4.4
old44 = None
for cand in ('"farmers’ fields', '"farmers\' fields'):
    j = s.find(cand, anchor2)
    if j > 0:
        break
# tambah kalimat di akhir paragraf pertama 4.4 dengan anchor teks yang pasti ada
old = 'H("4.5. Sensitivity reflects the N economy of grain filling", 2)'
new = '''P(f"The Karangploso trial adds a spatial data point: the indigenous supply inferred there "
  f"({MAR['std']['NSOILBASE_fit']:.0f}–{MAR['ext']['NSOILBASE_fit']:.0f} kg N ha⁻¹) differs from the "
  "Sukamandi value by 10–20%, consistent with the view that NSOILBASE is a stable property of a field rather than "
  "of a region, and must be re-estimated locally — which a single omission plot suffices to do.")
H("4.5. Sensitivity reflects the N economy of grain filling", 2)'''
assert old in s, "anchor 4.4/4.5"
s = s.replace(old, new, 1)

# ---- 9. 4.7 keterbatasan: varietas + NLEAF
old = '''The independent validation used Inpari-33 rather than "
  "Inpari-32, although results were robust to eight variety assumptions.'''
new = '''The LTFE validation used Inpari-33 rather than "
  "Inpari-32, although results were robust to eight variety assumptions, and the second validation used Inpari-32 "
  "itself; its control, however, lacked P, K and PGPR, so only its leaf-area and biomass ratios, not its yield "
  "response, are a clean test of the N module.'''
assert old in s, "anchor 4.7 varietas"
s = s.replace(old, new)

old = '''"and N recovery trade off along a ridge of similar likelihood; a larger N-rate dataset, or an independent measurement "
  "of the indigenous N supply, would be needed to narrow it.'''
new = '''"and N recovery trade off along a ridge of similar likelihood; updating with the Karangploso LAI ratios narrowed it "
  f"to {MARU['NLEAF_sesudah'][1]:.2f} [{MARU['NLEAF_sesudah'][0]:.2f}, {MARU['NLEAF_sesudah'][2]:.2f}] (Section 3.5), and "
  "a larger N-rate dataset, or an independent measurement of the indigenous N supply, would narrow it further.'''
assert old in s, "anchor 4.7 NLEAF"
s = s.replace(old, new)

# ---- 10. abstrak: validasi kedua
old = '''f"LINTUL3-type extension reversing this strategy reduced the error in the leaf-area response from {rm['std']:.2f} to "
    f"{rm['ext']:.2f}.'''
new = '''f"LINTUL3-type extension reversing this strategy reduced the error in the leaf-area response from {rm['std']:.2f} to "
    f"{rm['ext']:.2f}, and blindly reproduced the leaf-area response of a second, independent N-rate trial on the same "
    f"variety in East Java (ratio RMSE {mar_rmse['ext']:.2f} versus {mar_rmse['std']:.2f} for the standard model).'''
assert old in s, "anchor abstrak"
s = s.replace(old, new)

F.write_text(s, encoding="utf-8")
print("patch marpaung ok")
