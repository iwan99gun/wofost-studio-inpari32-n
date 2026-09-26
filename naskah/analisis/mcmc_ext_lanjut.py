"""Ulang MCMC tahap-2 model EKSTENSI (NLEAF) sampai konvergen.

Run awal (800 langkah, StretchMove default) berhenti pada split-R-hat sampai 1.20 dan 15.8 langkah/tau.
Perbaikan di sini:
  1. Moves DEMove(0.8) + DESnookerMove(0.2) - jauh lebih efisien untuk posterior berpunggungan
     (korelasi NLEAF-NSOILBASE-N_recovery) daripada StretchMove.
  2. Walker diinisialisasi menyebar dari posterior run awal (median + kovarian dari korelasi & kuantil,
     dilebarkan 1.5x) -> burn-in pendek TAPI tetap overdispersed sehingga R-hat jujur.
  3. Checkpoint rantai ke npz tiap blok -> bisa dihentikan dan dilanjutkan kapan saja.
  4. Berhenti otomatis bila: langkah >= 1200 DAN max split-R-hat <= 1.05 DAN langkah/tau >= 50; batas keras 3200.

Setelah selesai: posterior + prediksi LTFE (64 sampel, CRPS, cakupan 95%) dihitung ulang persis seperti
mcmc_bersama.py, entri 'ext' di posterior_bertahap_n_inpari32.json DIGANTI (yang lama disimpan sebagai
'ext_awal_800langkah'), n_step & sampler dicatat.

Jalankan: python naskah/analisis/mcmc_ext_lanjut.py   (log: mcmc_ext_lanjut.log)
"""
import sys, json, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mcmc_bersama as M  # noqa: E402  (import ringan; kerja berat ada di M._init)
import emcee  # noqa: E402
from multiprocessing import Pool  # noqa: E402

L = M.L
CKPT = L / "posterior_bertahap_n_inpari32_ext_chain.npz"
OUT = L / "posterior_bertahap_n_inpari32.json"
NAMES = M.S2["ext"]
ND = len(NAMES)
NW = 24
BLOK = 100
MIN_STEP, MAX_STEP = 1200, 3200
TARGET_RHAT, TARGET_LPT = 1.05, 50.0


def diag_chain(ch, acc_mean):
    """Diagnosis dari array rantai (steps, walkers, dim) - setara M.diag tapi tanpa objek sampler."""
    ns_, nw, nd = ch.shape
    tau = emcee.autocorr.integrated_time(ch, tol=0)
    burn = int(min(ns_ // 2, max(100, 5 * np.max(tau))))
    post = ch[burn:]
    ess = (post.shape[0] * nw) / tau
    rhat = []
    for j in range(nd):
        half = post.shape[0] // 2
        chains = np.concatenate([post[:half, :, j].T, post[half:2 * half, :, j].T], axis=0)
        m, n = chains.shape
        W = chains.var(axis=1, ddof=1).mean(); B = n * chains.mean(axis=1).var(ddof=1)
        rhat.append(float(np.sqrt(((n - 1) / n * W + B / n) / W)))
    d = dict(tau=dict(zip(NAMES, np.round(tau, 1).tolist())), langkah_per_tau=float(ns_ / np.max(tau)), burn=burn,
             ess=dict(zip(NAMES, np.round(ess, 0).tolist())), rhat=dict(zip(NAMES, np.round(rhat, 3).tolist())),
             penerimaan=float(acc_mean))
    return d, post.reshape(-1, nd)


def init_walkers(res, rng):
    """Sebar walker dari posterior run awal: median + kovarian (sd dari kuantil, korelasi tersimpan), x1.5."""
    p = res["ext_awal_800langkah"]["posterior"] if "ext_awal_800langkah" in res else res["ext"]["posterior"]
    kor = np.array((res.get("ext_awal_800langkah") or res["ext"])["korelasi"], float)
    med = np.array([p[n]["median"] for n in NAMES])
    sd = np.array([(p[n]["q97_5"] - p[n]["q2_5"]) / 3.92 for n in NAMES]) * 1.5
    cov = kor * np.outer(sd, sd)
    x = rng.multivariate_normal(med, cov, size=NW)
    lo = np.array([M.S2_B[n][0] for n in NAMES]) + 1e-6
    hi = np.array([M.S2_B[n][1] for n in NAMES]) - 1e-6
    return np.clip(x, lo, hi)


def main():
    t0 = time.time(); rng = np.random.default_rng(23)
    res = json.load(open(OUT))
    # prior tahap-1 (identik dengan mcmc_bersama.py)
    z = np.load(M.STAGE1_CACHE, allow_pickle=True); flat1 = z["flat1"]
    idx = [M.S1_NAMES.index("SPAN"), M.S1_NAMES.index("AMAXTB@y")]
    mu = flat1[:, idx].mean(axis=0); icov = np.linalg.inv(np.cov(flat1[:, idx].T))

    if CKPT.exists():
        zc = np.load(CKPT)
        chain = zc["chain"]; acc_sum = float(zc["acc_sum"]); n_blok = int(zc["n_blok"])
        p_last = chain[-1]
        print(f"[lanjut] dimuat {chain.shape[0]} langkah dari {CKPT.name}", flush=True)
    else:
        chain = np.empty((0, NW, ND)); acc_sum = 0.0; n_blok = 0
        p_last = init_walkers(res, rng)
        print("[mulai] walker diinisialisasi dari posterior run awal (x1.5 overdispersed)", flush=True)

    moves = [(emcee.moves.DEMove(), 0.8), (emcee.moves.DESnookerMove(), 0.2)]
    with Pool(8, initializer=M._init) as pool:
        while chain.shape[0] < MAX_STEP:
            sb = emcee.EnsembleSampler(NW, ND, M.logp2, args=("ext", mu, icov), pool=pool, moves=moves)
            state = sb.run_mcmc(p_last, BLOK, progress=False, skip_initial_state_check=True)
            chain = np.concatenate([chain, sb.get_chain()]); p_last = state.coords
            acc_sum += float(np.mean(sb.acceptance_fraction)); n_blok += 1
            np.savez(CKPT, chain=chain, acc_sum=acc_sum, n_blok=n_blok)
            d, _ = diag_chain(chain, acc_sum / n_blok)
            rh = max(d["rhat"].values())
            print(f"[{chain.shape[0]:4d} langkah, {time.time()-t0:.0f}s] max R-hat {rh:.3f}  "
                  f"langkah/tau {d['langkah_per_tau']:.1f}  penerimaan {d['penerimaan']:.3f}", flush=True)
            if chain.shape[0] >= MIN_STEP and rh <= TARGET_RHAT and d["langkah_per_tau"] >= TARGET_LPT:
                break

        d2, flat2 = diag_chain(chain, acc_sum / n_blok)
        q = np.percentile(flat2, [2.5, 50, 97.5], axis=0)
        print(f"[final] diag {d2}", flush=True)
        for i, n in enumerate(NAMES):
            print(f"   {n}: {q[1, i]:.4g} [{q[0, i]:.4g}, {q[2, i]:.4g}]", flush=True)

        # ---- prediksi LTFE persis seperti mcmc_bersama.py
        V = json.load(open(L / "validasi_ltfe_sukamandi.json"))
        draws = flat2[rng.choice(len(flat2), 64, replace=False)]
        preds = pool.starmap(M.ltfe_pred, [("ext", dict(zip(NAMES, map(float, dr)))) for dr in draws])
    band, sc = {}, {}
    for sk in preds[0]:
        band[sk] = {}; ob = V[sk]["obs"]
        for k in preds[0][sk]:
            v = np.array([pp[sk][k] for pp in preds])
            band[sk][k] = dict(q2_5=float(np.percentile(v, 2.5)), median=float(np.median(v)), q97_5=float(np.percentile(v, 97.5)))
            if k in ob:
                y = ob[k]; vv = v / y if k in ("Y0", "Y140") else v; yy = 1.0 if k in ("Y0", "Y140") else y
                sc[f"{sk}_{k}"] = dict(crps=M.crps(vv, yy), dalam_95=bool(band[sk][k]["q2_5"] <= y <= band[sk][k]["q97_5"]))
    lai_c = [v["crps"] for k, v in sc.items() if "rLAI" in k]

    res = json.load(open(OUT))
    if "ext_awal_800langkah" not in res:
        res["ext_awal_800langkah"] = res["ext"]
    res["ext"] = dict(diagnosis=d2, posterior={n: dict(q2_5=float(q[0, i]), median=float(q[1, i]), q97_5=float(q[2, i])) for i, n in enumerate(NAMES)},
                      korelasi=np.corrcoef(flat2.T).round(2).tolist(), urutan=NAMES, n_walker=NW, n_step=int(chain.shape[0]),
                      sampler="DEMove(0.8)+DESnookerMove(0.2), init dari posterior awal 1.5x overdispersed",
                      prediksi_ltfe=band, skor=sc, crps_rasio_LAI_rata2=float(np.mean(lai_c)),
                      cakupan_95=float(np.mean([v["dalam_95"] for v in sc.values()])))
    json.dump(res, open(OUT, "w"), indent=1)
    print(f"   CRPS rasio LAI {np.mean(lai_c):.3f}; cakupan 95% {res['ext']['cakupan_95']:.2f}", flush=True)
    print(f"selesai {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
