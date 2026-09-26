"""MCMC bertahap-Bayesian (menjawab keberatan metodologis 2 & 4):
Tahap 1  : posterior parameter produksi potensial (AMAXTB@y, SPAN, TDWI, RGRLAI) dari data Agustiani 2016 (3 lokasi)
           + LAI 14/28 HST Sukamandi; WOFOST 7.2 + syok tanam pindah; prior seragam dalam batas.
Tahap 2  : posterior parameter N (NSOILBASE, N_recovery[, NLEAF]) BERSAMA SPAN dan AMAXTB@y, dengan posterior tahap 1
           sebagai prior (normal multivariat) -> ketidakpastian tahap 1 ikut dipropagasikan.
Diagnosis: waktu autokorelasi terintegrasi (tau), rasio langkah/tau (pedoman emcee > 50), ESS, split-R-hat antar walker.
Prediksi : 64 sampel posterior -> interval 95 % dan CRPS untuk data independen LTFE.
Jalankan: python naskah/analisis/mcmc_bersama.py   (sekitar 1 jam dengan 8 proses)"""
import sys, json, datetime as dt, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np, pandas as pd
import wofost_app  # noqa
from wofost_app.core.config import SimulationConfig, FertilizerEvent
from wofost_app.core.weather import build_weather_provider
from wofost_app.core.simulation import SimulationRunner
from wofost_app.core.calibration import load_observations, _match

L = ROOT / "data" / "lapangan"; PJ = ROOT / "data" / "projects"
_R = {}


def _init():
    if _R:
        return
    # ---- tahap 1: tiga lokasi Agustiani + LAI awal Sukamandi
    ds = {s: (PJ / f"agustiani2018_{s}_inpari32.json", L / f"obs_{s}_2016_inpari32.csv", L / "agustiani2018_hy_inpari32_long.csv", ["LAI", "TAGP", "TWSO"])
          for s in ("subang", "indramayu", "bandung")}
    ds["suka"] = (PJ / "sujinah2020_sukamandi_mh2017_inpari32.json", L / "obs_sukamandi_mh2017_inpari32.csv",
                  L / "sujinah2020_sukamandi_mh2017_inpari32_long.csv", ["LAI"])
    _R["s1"] = {}
    for k, (pj, ob, lg, vv) in ds.items():
        cfg = SimulationConfig.load(pj); cfg.model_name = "Wofost72_PP"
        base = {kk: v for kk, v in cfg.crop_overrides.items() if kk in ("TSUM1", "TSUM2", "SLATB@ya", "SLATB@yb")}
        cfg.crop_overrides = base
        o = load_observations(ob)
        if k == "suka":
            o = o.loc[o.index <= pd.Timestamp("2017-12-25")]
        U = pd.read_csv(lg); U["day"] = pd.to_datetime(U["day"])
        unc = {(v, d): u for v, d, u in zip(U.variable, U.day, U.ketidakpastian)}
        _R["s1"][k] = (SimulationRunner(cfg, build_weather_provider(cfg.weather)), o, vv, unc)
    # ---- tahap 2: Sujinah per dosis (proyek final, model std / ext)
    _R["s2"] = {}
    for key, suf in (("std", ""), ("ext", "_nlv")):
        for d in (23, 115, 207):
            cfg = SimulationConfig.load(PJ / f"sujinah2020_sukamandi_mh2017_inpari32_N{d}{suf}.json")
            _R["s2"][(key, d)] = SimulationRunner(cfg, build_weather_provider(cfg.weather))


S1_NAMES = ["AMAXTB@y", "SPAN", "TDWI", "RGRLAI"]
S1_LO, S1_HI = np.array([0.6, 20, 15, 0.002]), np.array([1.4, 60, 250, 0.03])


def logp1(x):
    if np.any(x < S1_LO) or np.any(x > S1_HI):
        return -np.inf
    _init(); p = dict(zip(S1_NAMES, map(float, x))); out = []
    try:
        for k, (run, o, vv, unc) in _R["s1"].items():
            res = run.run(p)
            for v, (ob, sim) in _match(res.daily, o, vv).items():
                days = o[v].dropna().index[: len(ob)]
                u = np.array([unc.get((v, d), np.nan) for d in days], float)
                u = np.where(np.isnan(u), np.abs(ob) * 0.1 + 1e-6, u)
                out.append((sim - ob) / u)
    except Exception:
        return -np.inf
    return -0.5 * float(np.sum(np.square(np.concatenate(out))))


# ---- tahap 2
s0 = dt.date(2017, 11, 22)
D28, DFL = s0 + dt.timedelta(days=28), s0 + dt.timedelta(days=67)
ABS = {23: dict(TAGP=10065.3, TWSO=5410 * .86), 115: dict(TAGP=15538.9, TWSO=6920 * .86), 207: dict(TAGP=15468.0, TWSO=7610 * .86)}
CV_ABS = {"TAGP": 0.168, "TWSO": 0.0875}
MAIN = {"LAI28": {23: 804, 115: 1079, 207: 1240}, "LAIFL": {23: 2327, 115: 3617, 207: 4039},
        "TAGP28": {23: 100.72, 115: 136.06, 207: 158.96}, "TAGPFL": {23: 896.16, 115: 1099.14, 207: 1212.03}}
SIG = {k: np.sqrt(2) * v for k, v in {"LAI28": 0.0877, "LAIFL": 0.156, "TAGP28": 0.1226, "TAGPFL": 0.1798}.items()}
RATIO = {k: {d: MAIN[k][d] / MAIN[k][115] for d in (23, 207)} for k in MAIN}
S2 = {"std": ["SPAN", "AMAXTB@y", "NSOILBASE", "N_recovery"], "ext": ["SPAN", "AMAXTB@y", "NSOILBASE", "N_recovery", "NLEAF"]}
S2_B = {"SPAN": (20, 60), "AMAXTB@y": (0.6, 1.4), "NSOILBASE": (10, 300), "N_recovery": (0.2, 0.8), "NLEAF": (0.0, 4.0)}
PRIOR = {}


def sim2(key, p, d):
    run = _R["s2"][(key, d)]
    cfg = run.cfg
    cfg.site["NSOILBASE"] = p["NSOILBASE"]
    for e in cfg.fertilization:
        e.recovery = p["N_recovery"]
    ov = {"SPAN": p["SPAN"], "AMAXTB@y": p["AMAXTB@y"]}
    if "NLEAF" in p:
        ov.update({"NSLA": p["NLEAF"], "NLAI": p["NLEAF"]})
    r = run.run(ov); dd = r.daily
    g = lambda v, day: float(dd.loc[pd.Timestamp(day), v])
    return dict(TAGP=r.summary["TAGP"], TWSO=r.summary["TWSO"], LAI28=g("LAI", D28), LAIFL=g("LAI", DFL), TAGP28=g("TAGP", D28), TAGPFL=g("TAGP", DFL))


def logp2(x, key, mu, icov):
    names = S2[key]
    if any(not (S2_B[n][0] <= v <= S2_B[n][1]) for n, v in zip(names, x)):
        return -np.inf
    _init(); p = dict(zip(names, map(float, x)))
    z = np.array([p["SPAN"], p["AMAXTB@y"]]) - mu
    lp_prior = -0.5 * float(z @ icov @ z)
    try:
        S = {d: sim2(key, p, d) for d in (23, 115, 207)}
    except Exception:
        return -np.inf
    r = [(S[d][v] - ABS[d][v]) / (CV_ABS[v] * ABS[d][v]) for d in (23, 115, 207) for v in ("TAGP", "TWSO")]
    r += [(S[d][k] / S[115][k] - RATIO[k][d]) / SIG[k] for d in (23, 207) for k in MAIN]
    return lp_prior - 0.5 * float(np.sum(np.square(r)))


def ltfe_pred(key, p):
    if "ltfe" not in _R:
        ns = {}
        exec(open(HERE / "validasi_ltfe.py", encoding="utf-8").read().split("res = {}")[0], ns)
        _R["ltfe"] = (ns, ns["make"])
    ns, orig = _R["ltfe"]
    def make(mk, tp, seed, dose, f, nsoil=None, pi_day=35):
        c = orig(mk, tp, seed, dose, f, nsoil, pi_day)
        c.site["NSOILBASE"] = p["NSOILBASE"]
        for e in c.fertilization:
            e.recovery = p["N_recovery"]
        c.crop_overrides.update({"SPAN": p["SPAN"], "AMAXTB@y": p["AMAXTB@y"]})
        if "NLEAF" in p:
            c.crop_overrides.update({"NSLA": p["NLEAF"], "NLAI": p["NLEAF"]})
        return c
    ns["make"] = make
    V = json.load(open(L / "validasi_ltfe_sukamandi.json"))
    out = {}
    for sk, S in ns["SEASONS"].items():
        A = ns["predict"](key, S, S["tp"], V[sk]["std"]["f_tsum"])
        out[sk] = {k: A[k] for k in A if k in ("Y0", "Y140", "rY") or k.startswith("rLAI") or k.startswith("rDM")}
    return out


def diag(sampler, names):
    ch = sampler.get_chain()                     # (steps, walkers, dim)
    ns_, nw, nd = ch.shape
    tau = sampler.get_autocorr_time(tol=0)
    burn = int(min(ns_ // 2, max(100, 5 * np.max(tau))))
    post = ch[burn:]
    ess = (post.shape[0] * nw) / tau
    rhat = []
    for j in range(nd):                          # split-R-hat, walker sebagai rantai
        half = post.shape[0] // 2
        chains = np.concatenate([post[:half, :, j].T, post[half:2 * half, :, j].T], axis=0)
        m, n = chains.shape
        W = chains.var(axis=1, ddof=1).mean(); B = n * chains.mean(axis=1).var(ddof=1)
        rhat.append(float(np.sqrt(((n - 1) / n * W + B / n) / W)))
    return dict(tau=dict(zip(names, tau.round(1).tolist())), langkah_per_tau=float(ns_ / np.max(tau)), burn=burn,
                ess=dict(zip(names, ess.round(0).tolist())), rhat=dict(zip(names, np.round(rhat, 3).tolist())),
                penerimaan=float(np.mean(sampler.acceptance_fraction))), post.reshape(-1, nd)


def crps(samples, y):
    s = np.asarray(samples, float)
    return float(np.mean(np.abs(s - y)) - 0.5 * np.mean(np.abs(s[:, None] - s[None, :])))


STAGE1_CACHE = L / "posterior_bertahap_n_inpari32_tahap1_chain.npz"


def run_or_load_stage1(pool, rng):
    """Jalankan MCMC tahap 1, atau muat dari cache npz jika sudah pernah dijalankan (agar bisa dilanjutkan tanpa
    mengulang ~65 menit tahap 1 setelah proses dihentikan)."""
    import emcee
    if STAGE1_CACHE.exists():
        z = np.load(STAGE1_CACHE, allow_pickle=True)
        flat1 = z["flat1"]; d1 = json.loads(str(z["diag"]))
        print(f"[tahap1] dimuat dari cache {STAGE1_CACHE.name}: {len(flat1)} sampel", flush=True)
        return d1, flat1
    s1_start = np.array([0.902, 36.6, 143.8, 0.0035])
    nw, nst = 24, 1000
    p0 = np.clip(s1_start * (1 + 0.02 * rng.standard_normal((nw, 4))), S1_LO, S1_HI)
    sa = emcee.EnsembleSampler(nw, 4, logp1, pool=pool)
    sa.run_mcmc(p0, nst, progress=False, skip_initial_state_check=True)
    d1, flat1 = diag(sa, S1_NAMES)
    np.savez(STAGE1_CACHE, flat1=flat1, diag=json.dumps(d1))
    return d1, flat1


def main():
    import emcee
    from multiprocessing import Pool
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("stages", nargs="*", default=["std", "ext"], help="tahap-2 yang dijalankan: std, ext, atau keduanya")
    args = ap.parse_args()
    t0 = time.time(); rng = np.random.default_rng(11)
    res = {}
    if (L / "posterior_bertahap_n_inpari32.json").exists():
        res = json.load(open(L / "posterior_bertahap_n_inpari32.json"))
    with Pool(8, initializer=_init) as pool:
        # ---------------- tahap 1 (dari cache bila sudah pernah dijalankan)
        d1, flat1 = run_or_load_stage1(pool, rng)
        nw, nst = 24, 1000
        q = np.percentile(flat1, [2.5, 50, 97.5], axis=0)
        res["tahap1"] = dict(diagnosis=d1, posterior={n: dict(q2_5=float(q[0, i]), median=float(q[1, i]), q97_5=float(q[2, i])) for i, n in enumerate(S1_NAMES)},
                             korelasi=np.corrcoef(flat1.T).round(2).tolist(), n_walker=nw, n_step=nst)
        json.dump(res, open(L / "posterior_bertahap_n_inpari32.json", "w"), indent=1)
        print(f"[tahap1] {time.time() - t0:.0f}s diag {d1}", flush=True)
        for i, n in enumerate(S1_NAMES):
            print(f"   {n}: {q[1, i]:.4g} [{q[0, i]:.4g}, {q[2, i]:.4g}]", flush=True)
        idx = [S1_NAMES.index("SPAN"), S1_NAMES.index("AMAXTB@y")]
        mu = flat1[:, idx].mean(axis=0); cov = np.cov(flat1[:, idx].T); icov = np.linalg.inv(cov)
        res["prior_tahap2"] = dict(mu=mu.tolist(), cov=cov.tolist(), urutan=["SPAN", "AMAXTB@y"])
        # ---------------- tahap 2
        fin = json.load(open(L / "hasil_kalibrasi_n5_inpari32.json"))["final"]
        V = json.load(open(L / "validasi_ltfe_sukamandi.json"))
        for key in args.stages:
            if key in res and "posterior" in res[key]:
                print(f"[tahap2 {key}] sudah ada di {('posterior_bertahap_n_inpari32.json')}, dilewati (hapus entri untuk menjalankan ulang)", flush=True)
                continue
            names = S2[key]; nd = len(names)
            st = {"SPAN": mu[0], "AMAXTB@y": mu[1], **fin[key]}
            x0 = np.array([st[n] for n in names], float)
            span = np.array([S2_B[n][1] - S2_B[n][0] for n in names])
            p0 = x0 + 0.02 * span * rng.standard_normal((nw, nd))
            p0 = np.clip(p0, [S2_B[n][0] + 1e-6 for n in names], [S2_B[n][1] - 1e-6 for n in names])
            sb = emcee.EnsembleSampler(nw, nd, logp2, args=(key, mu, icov), pool=pool)
            sb.run_mcmc(p0, 800, progress=False, skip_initial_state_check=True)
            d2, flat2 = diag(sb, names)
            q = np.percentile(flat2, [2.5, 50, 97.5], axis=0)
            print(f"[tahap2 {key}] {time.time() - t0:.0f}s diag {d2}", flush=True)
            for i, n in enumerate(names):
                print(f"   {n}: {q[1, i]:.4g} [{q[0, i]:.4g}, {q[2, i]:.4g}]", flush=True)
            draws = flat2[rng.choice(len(flat2), 64, replace=False)]
            preds = pool.starmap(ltfe_pred, [(key, dict(zip(names, map(float, dr)))) for dr in draws])
            band, sc = {}, {}
            for sk in preds[0]:
                band[sk] = {}; ob = V[sk]["obs"]
                for k in preds[0][sk]:
                    v = np.array([pp[sk][k] for pp in preds])
                    band[sk][k] = dict(q2_5=float(np.percentile(v, 2.5)), median=float(np.median(v)), q97_5=float(np.percentile(v, 97.5)))
                    if k in ob:
                        y = ob[k]; vv = v / y if k in ("Y0", "Y140") else v; yy = 1.0 if k in ("Y0", "Y140") else y
                        sc[f"{sk}_{k}"] = dict(crps=crps(vv, yy), dalam_95=bool(band[sk][k]["q2_5"] <= y <= band[sk][k]["q97_5"]))
            lai_c = [v["crps"] for k, v in sc.items() if "rLAI" in k]
            res[key] = dict(diagnosis=d2, posterior={n: dict(q2_5=float(q[0, i]), median=float(q[1, i]), q97_5=float(q[2, i])) for i, n in enumerate(names)},
                            korelasi=np.corrcoef(flat2.T).round(2).tolist(), urutan=names, n_walker=nw, n_step=800,
                            prediksi_ltfe=band, skor=sc, crps_rasio_LAI_rata2=float(np.mean(lai_c)),
                            cakupan_95=float(np.mean([v["dalam_95"] for v in sc.values()])))
            print(f"   CRPS rasio LAI {np.mean(lai_c):.3f}; cakupan 95% {res[key]['cakupan_95']:.2f}", flush=True)
            json.dump(res, open(L / "posterior_bertahap_n_inpari32.json", "w"), indent=1)
    print(f"selesai {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
