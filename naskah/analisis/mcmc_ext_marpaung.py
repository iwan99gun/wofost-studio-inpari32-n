"""Dua analisis lanjutan dengan dataset independen kedua (Marpaung et al. 2024, Inpari-32, Karangploso):

A. PROPAGASI POSTERIOR (validasi probabilistik buta, seperti LTFE): 64 sampel posterior tahap-2 yang sudah
   konvergen (std & ext) -> interval prediksi 95% + CRPS + cakupan untuk rasio hasil (50/100/150 vs 0 N)
   dan rasio LAI 0/100 N pada 28/42/56 HST. NSOILBASE disetel per sampel pada hasil 0-N (protokol LTFE).
   Catatan: rantai std lama (800 langkah, R-hat<=1.10) tidak disimpan; posterior std didekati normal
   multivariat dari median/kuantil/korelasi tersimpan - cukup untuk interval prediksi.

B. PEMBARUAN BAYESIAN (importance sampling): posterior ext diperbarui dengan 3 rasio LAI Marpaung
   -> interval NLEAF menyempit tanpa mengulang MCMC. Bobot w_i = L_Marpaung(theta_i); ESS dilaporkan.
   sigma rasio = sqrt(2) x rasio x CV kolom (konvensi galat-observasi naskah, komponen model-struktur).

Jalankan: python naskah/analisis/mcmc_ext_marpaung.py   (log: mcmc_ext_marpaung.log)
"""
import sys, json, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validasi_marpaung as VM  # noqa: E402
from multiprocessing import Pool  # noqa: E402

L = VM.L
CKPT = L / "posterior_bertahap_n_inpari32_ext_chain.npz"
OUT = L / "validasi_marpaung_karangploso.json"
POSTJ = L / "posterior_bertahap_n_inpari32.json"
NAMES = ["SPAN", "AMAXTB@y", "NSOILBASE", "N_recovery", "NLEAF"]
TP = __import__("datetime").date(2023, 5, 15)

# observasi rasio
OBS_rLAI = {a: VM.OBS["LAI"][a][0] / VM.OBS["LAI"][a][100] for a in (28, 42, 56)}
CV = {28: 0.0938, 42: 0.1332, 56: 0.1004}
SIG = {a: np.sqrt(2) * OBS_rLAI[a] * CV[a] for a in OBS_rLAI}
OBS_rY = {d: VM.OBS["Y"][d] / VM.OBS["Y"][0] for d in (50, 100, 150)}


def _init():
    VM.wdp()


def pred_theta(mk, th):
    """Prediksi Marpaung untuk satu sampel parameter: NSOILBASE disetel pada 0-N, lalu rasio."""
    from scipy import optimize
    p = dict(zip(NAMES, map(float, th)))
    ov = {"SPAN": p["SPAN"], "AMAXTB@y": p["AMAXTB@y"]}
    if mk == "ext":
        ov.update({"NSLA": p["NLEAF"], "NLAI": p["NLEAF"]})

    def one(dose, ns):
        c = VM.make(mk, TP, dose, ns)
        for e in c.fertilization:
            e.recovery = p["N_recovery"]
        c.crop_overrides.update(ov)
        return VM.run(c)

    y0 = VM.OBS["Y"][0]
    def g(ns):
        return one(0, ns).summary["TWSO"] - y0
    try:
        ns = 390.0 if g(390.0) < 0 else optimize.brentq(g, 1.0, 390.0, xtol=1.0)
    except Exception:
        return None
    import pandas as pd, datetime as dt
    out = dict(NSOILBASE=ns)
    daily = {}
    for dose in (0, 50, 100, 150):
        r = one(dose, ns)
        out[f"Y{dose}"] = r.summary["TWSO"]
        daily[dose] = r.daily
    for d in (50, 100, 150):
        out[f"rY{d}"] = out[f"Y{d}"] / out["Y0"]
    for a in (28, 42, 56):
        day = pd.Timestamp(TP + dt.timedelta(days=a))
        out[f"rLAI{a}"] = float(daily[0].loc[day, "LAI"]) / float(daily[100].loc[day, "LAI"])
    return out


def crps(s, y):
    s = np.asarray(s, float)
    return float(np.mean(np.abs(s - y)) - 0.5 * np.mean(np.abs(s[:, None] - s[None, :])))


def band_scores(preds):
    keys = [k for k in preds[0] if k.startswith("rY") or k.startswith("rLAI") or k == "NSOILBASE"]
    band, sc = {}, {}
    for k in keys:
        v = np.array([p[k] for p in preds])
        band[k] = dict(q2_5=float(np.percentile(v, 2.5)), median=float(np.median(v)), q97_5=float(np.percentile(v, 97.5)))
        y = OBS_rY.get(int(k[2:])) if k.startswith("rY") else (OBS_rLAI.get(int(k[4:])) if k.startswith("rLAI") else None)
        if y is not None:
            sc[k] = dict(obs=float(y), crps=crps(v, y), dalam_95=bool(band[k]["q2_5"] <= y <= band[k]["q97_5"]))
    return band, sc


def main():
    t0 = time.time(); rng = np.random.default_rng(7)
    res = json.load(open(OUT))
    P = json.load(open(POSTJ))

    # ---- sampel posterior
    z = np.load(CKPT); ch = z["chain"]                       # ext: rantai konvergen
    flat_ext = ch[100:].reshape(-1, ch.shape[2])
    # std: aproksimasi normal multivariat dari ringkasan tersimpan (rantai tidak disimpan)
    ps = P["std"]["posterior"]; names_std = P["std"]["urutan"]
    med = np.array([ps[n]["median"] for n in names_std])
    sd = np.array([(ps[n]["q97_5"] - ps[n]["q2_5"]) / 3.92 for n in names_std])
    cov = np.array(P["std"]["korelasi"]) * np.outer(sd, sd)
    draws_std = rng.multivariate_normal(med, cov, size=64)
    draws_std = np.column_stack([draws_std, np.full(64, np.nan)])          # kolom NLEAF dummy
    idx = rng.choice(len(flat_ext), 64, replace=False)
    draws_ext = flat_ext[idx]

    with Pool(8, initializer=_init) as pool:
        for mk, dr in (("std", draws_std), ("ext", draws_ext)):
            preds = [p for p in pool.starmap(pred_theta, [(mk, th) for th in dr]) if p]
            band, sc = band_scores(preds)
            lai_c = [v["crps"] for k, v in sc.items() if k.startswith("rLAI")]
            res[mk]["prediksi_posterior"] = dict(n_sampel=len(preds), band=band, skor=sc,
                                                 crps_rasio_LAI_rata2=float(np.mean(lai_c)),
                                                 cakupan_95=float(np.mean([v["dalam_95"] for v in sc.values()])))
            print(f"[A {mk}] {len(preds)} sampel, {time.time()-t0:.0f}s; CRPS rLAI {np.mean(lai_c):.3f}; "
                  f"cakupan {res[mk]['prediksi_posterior']['cakupan_95']:.2f}", flush=True)

        # ---- B. pembaruan Bayesian NLEAF (importance sampling, hanya ext)
        n_is = 1024
        idx = rng.choice(len(flat_ext), n_is, replace=False)
        th_is = flat_ext[idx]
        preds = pool.starmap(pred_theta, [("ext", th) for th in th_is])
    ok = np.array([p is not None for p in preds])
    th_ok = th_is[ok]; preds = [p for p in preds if p]
    logw = np.zeros(len(preds))
    for i, p in enumerate(preds):
        logw[i] = -0.5 * sum(((p[f"rLAI{a}"] - OBS_rLAI[a]) / SIG[a]) ** 2 for a in (28, 42, 56))
    w = np.exp(logw - logw.max()); w /= w.sum()
    ess = float(1.0 / np.sum(w ** 2))
    def wq(x, qs=(2.5, 50, 97.5)):
        o = np.argsort(x); cw = np.cumsum(w[o])
        return [float(np.interp(q / 100, cw, x[o])) for q in qs]
    upd = {}
    for j, n in enumerate(NAMES):
        q = wq(th_ok[:, j])
        upd[n] = dict(q2_5=q[0], median=q[1], q97_5=q[2])
    nl0 = P["ext"]["posterior"]["NLEAF"]
    res["pembaruan_NLEAF"] = dict(
        metode="importance sampling pada posterior ext konvergen; likelihood = 3 rasio LAI Marpaung "
               "(sigma = sqrt2 x rasio x CV); NSOILBASE per sampel disetel pada hasil 0-N Karangploso",
        n_sampel=len(preds), ESS=ess, posterior_diperbarui=upd,
        NLEAF_sebelum=[nl0["q2_5"], nl0["median"], nl0["q97_5"]],
        NLEAF_sesudah=[upd["NLEAF"]["q2_5"], upd["NLEAF"]["median"], upd["NLEAF"]["q97_5"]])
    print(f"[B] ESS {ess:.0f}/{len(preds)}; NLEAF {nl0['median']:.2f} [{nl0['q2_5']:.2f},{nl0['q97_5']:.2f}] "
          f"-> {upd['NLEAF']['median']:.2f} [{upd['NLEAF']['q2_5']:.2f},{upd['NLEAF']['q97_5']:.2f}]", flush=True)

    json.dump(res, open(OUT, "w"), indent=1, default=float)
    print(f"selesai {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
