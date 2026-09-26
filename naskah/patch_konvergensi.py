"""Perbarui naskah setelah MCMC ekstensi konvergen (1200 langkah, DE moves, split-R-hat <= 1.02):
metode 2.9, hasil 3.5, keterbatasan 4.7, judul+catatan Tabel S4, + 2 referensi ter Braak."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
F = HERE / "buat_naskah.py"
s = F.read_text(encoding="utf-8")

# ---- 0. pustaka terverifikasi: tambah terbraak2006 & terbraak2008
PJ = HERE / "pustaka_terverifikasi.json"
pus = json.load(open(PJ, encoding="utf-8"))
pus["terbraak2006"] = dict(
    ref="ter Braak, C.J.F., 2006. A Markov Chain Monte Carlo version of the genetic algorithm Differential "
        "Evolution: easy Bayesian computing for real parameter spaces. Statistics and Computing 16, 239-249. "
        "https://doi.org/10.1007/s11222-006-8769-1",
    cite="ter Braak, 2006", sortkey="ter braak 2006", doi="10.1007/s11222-006-8769-1")
pus["terbraak2008"] = dict(
    ref="ter Braak, C.J.F., Vrugt, J.A., 2008. Differential Evolution Markov Chain with snooker updater and fewer "
        "chains. Statistics and Computing 18, 435-446. https://doi.org/10.1007/s11222-008-9104-9",
    cite="ter Braak and Vrugt, 2008", sortkey="ter braak 2008", doi="10.1007/s11222-008-9104-9")
json.dump(pus, open(PJ, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

# ---- 1. metode 2.9: sampler tahap-2 ekstensi
old = ('sampled them jointly with the N parameters (24 walkers × 800 steps); uncertainty from Step 1 was thereby '
       'propagated to "\n  "the N parameters and predictions.')
new = ('sampled them jointly with the N parameters (24 walkers; 800 steps for the standard model); uncertainty from '
       'Step 1 was thereby "\n  "propagated to the N parameters and predictions. Because the extension posterior '
       'contains a ridge along which NLEAF, "\n  "NSOILBASE and N recovery trade off (Section 4.2), the default '
       'stretch move mixed slowly for this stage; it was "\n  "therefore sampled with differential-evolution moves '
       '(80% DEMove, 20% snooker move; " + C("terbraak2006") + "; "\n  + C("terbraak2008") + "), initialised '
       'overdispersed around the posterior of a preliminary 800-step run, and extended "\n  "in blocks of 100 steps '
       'until split-R̂ ≤ 1.05 and the chain exceeded 50τ (reached at 1200 steps).')
assert old in s, "metode 2.9 tidak ketemu"
s = s.replace(old, new)

# ---- 2. hasil 3.5: paragraf konvergensi
old = ('P(f"Convergence diagnostics differed among stages (Table S4). Stage 1 (production parameters, 1000 steps) reached "\n'
       '  f"split-R̂ ≤ {max(DG[\'tahap1\'][\'rhat\'].values()):.2f} and a chain length of {DG[\'tahap1\'][\'langkah_per_tau\']:.0f}τ. "\n'
       '  f"Stage 2 for the standard model (NSOILBASE and N recovery jointly with SPAN and AMAXTB@y; 800 steps) reached "\n'
       '  f"split-R̂ ≤ {max(DG[\'std\'][\'rhat\'].values()):.2f} and {DG[\'std\'][\'langkah_per_tau\']:.0f}τ, within the range usually "\n'
       '  f"considered acceptable. Stage 2 for the NLEAF extension did not fully converge by the same criterion (split-R̂ up to "\n'
       '  f"{max(DG[\'ext\'][\'rhat\'].values()):.2f} for N recovery, {DG[\'ext\'][\'langkah_per_tau\']:.0f}τ), reflecting the weak "\n'
       '  "identifiability of NLEAF discussed in Section 4.2: because NLEAF, NSOILBASE and N recovery trade off along a ridge of "\n'
       '  "similar likelihood, the chains explored this ridge more slowly than the other parameters. The reported intervals for "\n'
       '  "the extension are therefore wider than with full convergence and should be read as indicative of the order of "\n'
       '  "magnitude of the uncertainty rather than as exact bounds; this is noted as a limitation in Section 4.7. "')
new = ('P(f"All stages converged (Table S4). Stage 1 (production parameters, 1000 steps) reached "\n'
       '  f"split-R̂ ≤ {max(DG[\'tahap1\'][\'rhat\'].values()):.2f} and a chain length of {DG[\'tahap1\'][\'langkah_per_tau\']:.0f}τ, and stage 2 for the standard model "\n'
       '  f"(NSOILBASE and N recovery jointly with SPAN and AMAXTB@y; 800 steps) split-R̂ ≤ {max(DG[\'std\'][\'rhat\'].values()):.2f} "\n'
       '  f"and {DG[\'std\'][\'langkah_per_tau\']:.0f}τ. For the NLEAF extension a preliminary 800-step run with the default stretch move had not "\n'
       '  "converged (split-R̂ up to 1.20), because NLEAF, NSOILBASE and N recovery trade off along a ridge of similar "\n'
       '  "likelihood (Section 4.2) that the stretch move explored slowly; with differential-evolution moves (Section 2.9) "\n'
       '  f"the chains converged cleanly (split-R̂ ≤ {max(DG[\'ext\'][\'rhat\'].values()):.2f}, "\n'
       '  f"{DG[\'ext\'][\'langkah_per_tau\']:.0f}τ, minimum effective sample size {min(DG[\'ext\'][\'ess\'].values()):.0f}). "')
assert old in s, "hasil 3.5 tidak ketemu"
s = s.replace(old, new)

# ---- 3. keterbatasan 4.7
old = ('P(f"The MCMC chain for the NLEAF extension did not reach full convergence (split-R̂ up to {max(DG[\'ext\'][\'rhat\'].values()):.2f}; "\n'
       '  "Section 3.5, Table S4), so its posterior intervals are approximate; a longer run, a reparameterisation that separates "\n'
       '  "NLEAF from NSOILBASE and N recovery, or a larger N-rate dataset would be needed to resolve this ridge in the "\n'
       '  "likelihood. The point estimate and the qualitative conclusion, that the extension improves the independent leaf-area "\n'
       '  "response, are not expected to change, because they are also supported by the leave-one-dose-out cross-validation, the "\n'
       '  "blind LTFE prediction and the observation-model robustness check (Table S3), none of which depend on chain "\n'
       '  "convergence. ')
new = ('P(f"Although the MCMC chains converged for all stages (split-R̂ ≤ {max(DG[\'ext\'][\'rhat\'].values()):.2f} for the extension; "\n'
       '  f"Section 3.5, Table S4), the posterior of NLEAF remains wide ({ci(\'ext\', \'NLEAF\', f2)}) because NLEAF, NSOILBASE "\n'
       '  "and N recovery trade off along a ridge of similar likelihood; a larger N-rate dataset, or an independent measurement "\n'
       '  "of the indigenous N supply, would be needed to narrow it. The point estimate and the qualitative conclusion, that the "\n'
       '  "extension improves the independent leaf-area response, do not depend on this width: they are also supported by the "\n'
       '  "leave-one-dose-out cross-validation, the blind LTFE prediction and the observation-model robustness check (Table S3). ')
assert old in s, "keterbatasan 4.7 tidak ketemu"
s = s.replace(old, new)

# ---- 4. Tabel S4: judul + catatan
old = 'TABLE("Table S4. MCMC convergence diagnostics per stage (emcee, affine-invariant ensemble sampler).",'
new = 'TABLE("Table S4. MCMC convergence diagnostics per stage (emcee ensemble sampler).",'
assert old in s
s = s.replace(old, new)
old = ('note="Split-R̂ computed across walkers treated as chains (Gelman and Rubin, 1992); τ, integrated autocorrelation time; "\n'
       '           "ESS, effective sample size. A split-R̂ close to 1 and a chain length well above the autocorrelation time indicate "\n'
       '           "convergence; the NLEAF extension (stage 2, ext) did not fully meet this criterion (Section 3.5, 4.7).")')
new = ('note="Split-R̂ computed across walkers treated as chains (Gelman and Rubin, 1992); τ, integrated autocorrelation time; "\n'
       '           "ESS, effective sample size. A split-R̂ close to 1 and a chain length well above the autocorrelation time indicate "\n'
       '           "convergence. Stages 1 and 2 (std) used the affine-invariant stretch move; stage 2 (ext) used "\n'
       '           "differential-evolution moves because of the NLEAF–NSOILBASE–N-recovery ridge (Section 2.9).")')
assert old in s
s = s.replace(old, new)

# ---- 5. daftar referensi: sisip ter Braak sebelum van Diepen
old = '    ("van Diepen, C.A., Wolf, J., van Keulen, H., Rappoldt, C., 1989.'
new = ('    ("ter Braak, C.J.F., 2006. A Markov Chain Monte Carlo version of the genetic algorithm Differential Evolution: "\n'
       '     "easy Bayesian computing for real parameter spaces. Stat. Comput. 16, 239–249. https://doi.org/10.1007/s11222-006-8769-1", False),\n'
       '    ("ter Braak, C.J.F., Vrugt, J.A., 2008. Differential Evolution Markov Chain with snooker updater and fewer chains. "\n'
       '     "Stat. Comput. 18, 435–446. https://doi.org/10.1007/s11222-008-9104-9", False),\n') + old
assert old in s
s = s.replace(old, new)

F.write_text(s, encoding="utf-8")
print("patch ok")
