"""Patch naskah untuk perbaikan metodologis (MCMC bertahap, AICc chi2, CRPS, identifiabilitas, pembanding ORYZA,
ketahanan model observasi). Jalankan sekali."""
from pathlib import Path
D = Path(__file__).parent
p = D / "buat_naskah.py"; s = p.read_text(encoding="utf-8")
(D / "buat_naskah_v2.py").write_text(s, encoding="utf-8")


def rep(a, b):
    global s
    if a not in s:
        raise SystemExit("MISS: " + a[:90])
    s = s.replace(a, b)


# ---------------------------------------------------------------- data baru
rep('POST = J("posterior_n_inpari32.json");',
    'POST = J("posterior_bertahap_n_inpari32.json"); ROB = J("ketahanan_model_observasi.json"); ORY = J("pembanding_oryza.json");')
rep('ps, pe = STD["parameter"], EXT["parameter"]',
    'ps, pe = STD["parameter"], EXT["parameter"]\n'
    'LODO_S = {r["ditahan"]: r for r in STD["lodo"]}; LODO_E = {r["ditahan"]: r for r in EXT["lodo"]}\n'
    'cal_err = max(abs(100 * (r["TWSO_sim"] / r["TWSO_obs"] - 1)) for r in STD["tabel"])\n'
    'DG = {k: POST[k]["diagnosis"] for k in ("tahap1", "std", "ext")}\n'
    'lpt_min = min(d["langkah_per_tau"] for d in DG.values()); rhat_max = max(max(d["rhat"].values()) for d in DG.values())\n'
    'ess_min = min(min(d["ess"].values()) for d in DG.values())\n'
    'rhoNS = POST["std"]["korelasi"][POST["std"]["urutan"].index("NSOILBASE")][POST["std"]["urutan"].index("N_recovery")]\n'
    'ROBD = {(r["varian"], r["model"]): r for r in ROB}\n')

rep('PUS["iizumi2009"]["cite"] = "Iizumi et al., 2009"',
    'PUS["iizumi2009"]["cite"] = "Iizumi et al., 2009"\nPUS["gelman1992"]["ref"] = PUS["gelman1992"]["ref"].replace("Statistical Science 7.", "Statistical Science 7, 457–472.")')
# ---------------------------------------------------------------- abstrak
rep('"cross-validation, MCMC, Sobol analysis and blind prediction of two seasons of 0-N omission plots from a long-term "\n    "experiment.',
    '"staged Bayesian inference, cross-validation and blind prediction of two seasons of 0-N omission plots from a long-term "\n    "experiment.')
rep('''"only in a juvenile window that closed before N deficiency developed. The corrected model reproduced grain yield across "
    f"N rates (cross-validated RMSE {100 * STD['rmse_lodo']['TWSO'] / 5716:.1f}%) and predicted independent 0-N yields within "''',
    '''"only in a juvenile window that closed before N deficiency developed. The corrected model reproduced grain yield at all "
    f"N rates (error ≤{cal_err:.0f}%) and predicted independent 0-N yields within "''')

# ---------------------------------------------------------------- metode 2.7 & 2.9
rep('P(f"Crop parameters from Step 1 were kept fixed. Indigenous soil N supply',
    'P(f"For point estimation, crop parameters from Step 1 were kept fixed; their uncertainty was propagated in the "\n'
    '  f"Bayesian analysis (Section 2.9). Indigenous soil N supply')
rep('"N-response signal. Models were compared with the small-sample Akaike criterion (AICc; Burnham and Anderson, 2002).")',
    '"N-response signal. The validation range of NSOILBASE in PCSE (0–100 kg N ha⁻¹) is an input check rather than a "\n'
    '  "physiological limit and truncated the posterior, so it was widened to 0–400 kg N ha⁻¹. Because observation errors "\n'
    '  "were fixed, −2 ln L equals the weighted sum of squares χ² plus a constant, and models were compared with "\n'
    '  "AICc = χ² + 2k + 2k(k + 1)/(n − k − 1) (Burnham and Anderson, 2002).")')
rep('''P("Posterior distributions of the N parameters were sampled with the affine-invariant ensemble sampler emcee "
  "(Foreman-Mackey et al., 2013), as in Bayesian calibration of rice models " + C("iizumi2009") + " (16 walkers, 120 steps, 40 burn-in, integrated autocorrelation time 4–8 steps) using "
  "the same likelihood, and 32 posterior draws were propagated to the LTFE predictions. Global sensitivity''',
    '''P("Parameter uncertainty was quantified by staged Bayesian inference with the affine-invariant ensemble sampler "
  + C("goodman2010") + " implemented in emcee (Foreman-Mackey et al., 2013), as in Bayesian calibration of rice models "
  + C("iizumi2009") + ". Stage 1 sampled AMAXTB@y, SPAN, TDWI and RGRLAI against the 2016 data with uniform priors "
  "(24 walkers × 600 steps). The stage-1 posterior of SPAN and AMAXTB@y, the two potential-production parameters with the "
  "largest Sobol indices, was approximated by a bivariate normal distribution and used as the prior in stage 2, which "
  "sampled them jointly with the N parameters (24 walkers × 800 steps); uncertainty from Step 1 was thereby propagated to "
  "the N parameters and predictions. Convergence was assessed with the integrated autocorrelation time τ (a chain length "
  "above 50τ is recommended for emcee), the effective sample size and split-R̂ computed across walkers "
  + C("gelman1992") + ", with a burn-in of max(100, 5τ). Sixty-four posterior draws were propagated to the LTFE, and "
  "predictive skill was scored with the continuous ranked probability score (CRPS) and 95% interval coverage "
  + C("gneiting2007") + ". Robustness to the observation model was tested by recalibrating with the ratio errors halved, "
  "doubled, or without ratio data. Global sensitivity''')

# ---------------------------------------------------------------- hasil 3.1 pembanding ORYZA
rep('"to ±30 days changed simulated flowering by 1–2 days after transplanting and yield by up to 10%.")',
    '"to ±30 days changed simulated flowering by 1–2 days after transplanting and yield by up to 10%. Compared with ORYZA "\n'
    '  "v3 calibrated on the same experiments (Agustiani et al., 2018a), WOFOST had a lower RMSE for AGB "\n'
    '  f"({ORY[\'semua\'][\'RMSE_AGB_t\']:.1f} vs 1.6 t ha⁻¹) and green LAI ({ORY[\'tanpa LAI masak\'][\'RMSE_LAI\']:.1f} vs 0.5) and the "\n'
    '  f"same mean normalised RMSE ({ORY[\'tanpa LAI masak\'][\'RMSEn_rata2_pct\']:.0f}% vs 23%), but a larger stem RMSE "\n'
    '  f"({ORY[\'semua\'][\'RMSE_batang_t\']:.1f} vs 0.7 t ha⁻¹; Table S2). Observed stem mass kept increasing after flowering "\n'
    '  "(from 4.1 to 7.5 t ha⁻¹ at Subang), whereas WOFOST allocates all post-anthesis assimilates to the panicles, so that "\n'
    '  "simulated stem mass levelled off at 71–75 DAT (Section 4.2).")')

# ---------------------------------------------------------------- hasil 3.2 identifiabilitas
rep('''  f"flowering biomass ratio more closely, at a small cost in grain yield fit (LODO RMSE {f0(EXT['rmse_lodo']['TWSO'])} "
  f"kg ha⁻¹). The two versions''',
    '''  f"flowering biomass ratio more closely and had a lower LODO RMSE for grain yield ({f0(EXT['rmse_lodo']['TWSO'])} kg ha⁻¹). "
  f"Cross-validation exposed an identifiability limit: when the 23 kg N ha⁻¹ rate was withheld, the two high rates could "
  f"not separate indigenous supply from fertiliser recovery (NSOILBASE {LODO_S[23]['p_NSOILBASE']:.0f} kg N ha⁻¹, recovery "
  f"{LODO_S[23]['p_N_recovery']:.2f}), and the standard model over-predicted the withheld yield by "
  f"{100 * (LODO_S[23]['TWSO_pred'] / LODO_S[23]['TWSO_obs'] - 1):.0f}%, whereas the extension, additionally constrained by "
  f"the leaf-area response, predicted it within {abs(100 * (LODO_E[23]['TWSO_pred'] / LODO_E[23]['TWSO_obs'] - 1)):.0f}%. "
  f"The two versions''')

# ---------------------------------------------------------------- hasil 3.4 cakupan dinamis
rep('''  f"of the six ratios from {rm['std']:.2f} to {rm['ext']:.2f}; in 2022 all LAI ratios, the 60-DAT biomass ratio and the "
  "yield ratio fell within its 95% predictive intervals, whereas none of the LAI ratios did for the standard model.")''',
    '''  f"of the six ratios from {rm['std']:.2f} to {rm['ext']:.2f}. Of the six LAI ratios, "
  f"{sum(v['dalam_95'] for k, v in POST['ext']['skor'].items() if 'rLAI' in k)} fell within the 95% predictive intervals of "
  f"the extension and {sum(v['dalam_95'] for k, v in POST['std']['skor'].items() if 'rLAI' in k)} within those of the "
  "standard model.")''')

# ---------------------------------------------------------------- hasil 3.5 ketidakpastian
rep('''P(f"The posterior of NSOILBASE was bounded by the prior range (95% interval {ci('std', 'NSOILBASE')} kg N ha⁻¹ for the "
  f"standard model) and N recovery was weakly constrained ({ci('std', 'N_recovery', f2)}), reflecting their correlation "
  f"with only three N rates (Table 2). NLEAF was constrained to {ci('ext', 'NLEAF', f2)}. At 23 kg N ha⁻¹, grain yield "''',
    '''P(f"All MCMC stages converged (chain length ≥{lpt_min:.0f}τ, split-R̂ ≤{rhat_max:.2f}, effective sample size "
  f"≥{ess_min:.0f}). Stage 1 constrained SPAN to {ci('tahap1', 'SPAN')} d and AMAXTB@y to {ci('tahap1', 'AMAXTB@y', f2)}. "
  f"With the bound removed, NSOILBASE had a 95% interval of {ci('std', 'NSOILBASE')} kg N ha⁻¹ and N recovery of "
  f"{ci('std', 'N_recovery', f2)} in the standard model, and the two were negatively correlated (r = {rhoNS:.2f}); NLEAF "
  f"was {ci('ext', 'NLEAF', f2)} (Table 2). For the independent LTFE data, the staged posterior of the extension covered "
  f"{100 * POST['ext']['cakupan_95']:.0f}% of the observations within its 95% intervals (standard model "
  f"{100 * POST['std']['cakupan_95']:.0f}%), and the mean CRPS of the LAI ratios was {POST['ext']['crps_rasio_LAI_rata2']:.3f} "
  f"versus {POST['std']['crps_rasio_LAI_rata2']:.3f}. Halving or doubling the ratio errors, or omitting the ratio data, "
  f"changed the 0-N yield predictions by at most "
  f"{max(abs(r['err_Y0_2022'] - ROBD[('dasar (sigma x1)', r['model'])]['err_Y0_2022']) for r in ROB):.1f} percentage points, "
  f"and the extension kept the lower LAI-ratio error in every variant (Table S3). At 23 kg N ha⁻¹, grain yield "''')

# ---------------------------------------------------------------- diskusi: partisi batang & identifiabilitas
rep('''  f"{max(tab_s[d]['TWSO_sim'] / tab_s[d]['TAGP_sim'] for d in (115, 207)):.2f}.")''',
    '''  f"{max(tab_s[d]['TWSO_sim'] / tab_s[d]['TAGP_sim'] for d in (115, 207)):.2f}. The benchmark against ORYZA points to the "
  "same structural element: in the 2016 data stem mass rose by 1–3 t ha⁻¹ after flowering, consistent with continued "
  "sheath and culm growth and temporary storage of non-structural carbohydrates, whereas WOFOST sends all post-anthesis "
  "assimilates to the panicles. Grain yield was nevertheless reproduced because post-anthesis growth in these crops was "
  "source- rather than partitioning-limited, but stem and harvest-index predictions require calibrated post-anthesis "
  "partitioning tables, which ORYZA had and our Step 1 did not.")''')
rep('''  + C("Dobermann et al., 2003b", "pampolino2007") + ".")''',
    '''  + C("Dobermann et al., 2003b", "pampolino2007") + ". Within a site, indigenous supply and fertiliser recovery are "
  f"separable only across a range of N rates: at 23 kg N ha⁻¹ fertiliser adds about {23 * ps['N_recovery']:.0f} kg of "
  f"available N against about {ps['NSOILBASE']:.0f} kg from the soil, so the low rate informs NSOILBASE while the high "
  "rates inform recovery. Without the low rate, any combination giving the same total supply at 115–207 kg N ha⁻¹ fits "
  "equally well " + C("beven2001") + ", which is exactly what the cross-validation showed. The leaf-area response restores "
  "identifiability because it depends on when N deficiency starts, which is governed mainly by indigenous supply; "
  "omission plots and early canopy measurements are therefore complementary rather than redundant.")''')

# ---------------------------------------------------------------- keterbatasan
rep('"datasets from one station and should be tested across sites and varieties. A dedicated field season with weekly green "',
    '"datasets from one station and should be tested across sites and varieties. Post-anthesis partitioning tables were not "\n'
    '  "calibrated, which limits stem and harvest-index predictions, and phenology parameters were fixed in the Bayesian "\n'
    '  "analysis because they were tightly constrained by the reported flowering dates. A dedicated field season with weekly green "')

# ---------------------------------------------------------------- Tabel 2 baris tahap 1 dengan interval posterior
rep('''       ["AMAXTB@y (→ AMAX_REF)", "– (kg CO₂ ha⁻¹ h⁻¹)", f"{f2(POT['parameter']['AMAXTB@y'])} (36.1)", "Step 1"],
       ["SPAN", "d", f1(POT["parameter"]["SPAN"]), "Step 1"],
       ["TDWI", "kg ha⁻¹", f0(POT["parameter"]["TDWI"]), "Step 1"],''',
    '''       ["AMAXTB@y (→ AMAX_REF)", "– (kg CO₂ ha⁻¹ h⁻¹)", f"{f2(POT['parameter']['AMAXTB@y'])} (36.1); {ci('tahap1', 'AMAXTB@y', f2)}", "Step 1 (stage-1 posterior)"],
       ["SPAN", "d", f"{f1(POT['parameter']['SPAN'])}; {ci('tahap1', 'SPAN')}", "Step 1 (stage-1 posterior)"],
       ["TDWI", "kg ha⁻¹", f"{f0(POT['parameter']['TDWI'])}; {ci('tahap1', 'TDWI', f0)}", "Step 1 (stage-1 posterior)"],''')

# ---------------------------------------------------------------- tabel suplemen S2 (ORYZA) & S3 (ketahanan)
rep('''      widths=[3.2, 4.0, 4.6, 4.2])

docx_path''', '''      widths=[3.2, 4.0, 4.6, 4.2])
TABLE("Table S2. Benchmark of the Step-1 calibration against ORYZA v3 calibrated on the same experiments by Agustiani et al. (2018a).",
      ["Statistic", "WOFOST 7.2 (this study)", "ORYZA v3 (Agustiani et al., 2018a)", "Mean experimental SD"],
      [["RMSE AGB (t ha⁻¹)", f"{ORY['semua']['RMSE_AGB_t']:.2f}", "1.6", "1.1"],
       ["RMSE stem (t ha⁻¹)", f"{ORY['semua']['RMSE_batang_t']:.2f}", "0.7", "0.6"],
       ["RMSE LAI, green LAI only / all", f"{ORY['tanpa LAI masak']['RMSE_LAI']:.2f} / {ORY['semua']['RMSE_LAI']:.2f}", "0.5", "0.2"],
       ["Mean normalised RMSE (%)", f"{ORY['tanpa LAI masak']['RMSEn_rata2_pct']:.0f}", "23", "–"],
       ["r² AGB / stem / LAI", f"{ORY['semua']['r2']['TAGP']:.2f} / {ORY['semua']['r2']['TWST']:.2f} / {ORY['tanpa LAI masak']['r2']['LAI']:.2f}", "> 0.93", "–"]],
      widths=[4.5, 4.0, 4.5, 3.0],
      note="ORYZA statistics as reported (one observation excluded). WOFOST: 3 sites × 7, 67 and 112 DAT; 'green LAI only' excludes the maturity LAI, which included senescent leaves.")
TABLE("Table S3. Robustness of calibration and independent prediction to the observation model for the ratio data.",
      ["Variant", "Model", "NSOILBASE", "Recovery", "NLEAF", "0-N error 2022 (%)", "0-N error 2020 (%)", "RMSE LAI ratio"],
      [[r["varian"].replace("dasar (sigma x1)", "baseline (σ × 1)").replace("sigma", "σ").replace("tanpa data rasio", "no ratio data"),
        {"std": "8.1", "ext": "8.1+NLEAF"}[r["model"]], f"{r['NSOILBASE']:.0f}", f"{r['N_recovery']:.2f}",
        (f"{r['NLEAF']:.2f}" if "NLEAF" in r else "–"), f"{r['err_Y0_2022']:+.1f}", f"{r['err_Y0_2020']:+.1f}", f"{r['rmse_rasio_LAI']:.2f}"] for r in ROB],
      widths=[3.0, 1.8, 1.8, 1.6, 1.4, 2.2, 2.2, 2.0], fs=8)

docx_path''')

p.write_text(s, encoding="utf-8")
# gambar 5 memakai posterior bertahap
g = D / "buat_gambar.py"; t = g.read_text(encoding="utf-8")
t = t.replace('P = json.load(open(L / "posterior_n_inpari32.json"))', 'P = json.load(open(L / "posterior_bertahap_n_inpari32.json"))')
g.write_text(t, encoding="utf-8")
print("patch metodologi diterapkan")
