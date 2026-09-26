"""Perbaikan kalibrasi respons N Inpari-32 (WOFOST 8.1):
 (1) bug konsistensi RGRLAI_MIN > RGRLAI diperbaiki lewat RGRLAI_MIN_FR,
 (2) data ditambah: respons RELATIF dosis N pada luas daun & biomasa 28 HST dan berbunga (efek utama dosis, Tabel 6 & 7
     Sujinah 2020; rasio terhadap 115 N sehingga bias level LAI awal tidak ikut) + hasil & biomasa masak Inpari-32 (Tabel 8, 10),
 (3) validasi: leave-one-dose-out (LODO) + uji transfer independen ke 3 lokasi Agustiani 2016 (126 kg N/ha, 7/24/42 HST)."""
import sys, json, datetime as dt
sys.path.insert(0, r"D:\riset_tani_1")
import numpy as np, pandas as pd
from scipy import optimize
import wofost_app  # noqa
from wofost_app.core.config import SimulationConfig, FertilizerEvent
from wofost_app.core.weather import build_weather_provider
from wofost_app.core.simulation import SimulationRunner

R = r"D:\riset_tani_1"
base = SimulationConfig.load(f"{R}/data/projects/sujinah2020_sukamandi_mh2017_inpari32.json")
base.model_name = "Wofost81_NWLP_CWB_CNB"
wdp = build_weather_provider(base.weather)
start = base.crop_start_date
D28, DFL = start + dt.timedelta(days=28), start + dt.timedelta(days=67)
GKG2BK = 0.86
DOSES = (23, 115, 207)
ABS = {23: dict(TAGP=10065.3, TWSO=5410 * GKG2BK), 115: dict(TAGP=15538.9, TWSO=6920 * GKG2BK), 207: dict(TAGP=15468.0, TWSO=7610 * GKG2BK)}
CV_ABS = {"TAGP": 0.168, "TWSO": 0.0875}
# efek utama dosis (rata-rata 6 genotipe): luas daun cm2/rumpun (Tabel 6), biomasa g/m2 (Tabel 7)
MAIN = {"LAI28": {23: 804, 115: 1079, 207: 1240}, "LAIFL": {23: 2327, 115: 3617, 207: 4039},
        "TAGP28": {23: 100.72, 115: 136.06, 207: 158.96}, "TAGPFL": {23: 896.16, 115: 1099.14, 207: 1212.03}}
CV_MAIN = {"LAI28": 0.0877, "LAIFL": 0.156, "TAGP28": 0.1226, "TAGPFL": 0.1798}   # CV per petak dari tabel
SIG_RATIO = {k: np.sqrt(2) * v for k, v in CV_MAIN.items()}                        # rasio dua rataan -> konservatif
RATIO = {k: {d: MAIN[k][d] / MAIN[k][115] for d in (23, 207)} for k in MAIN}
MODEL = {"m": "Wofost81_NWLP_CWB_CNB"}
NAMES = ["NSOILBASE", "N_recovery"]


def make_cfg(dose, x, extra=None, proj=None, split=(7, 28, 42)):
    p = dict(zip(NAMES, map(float, x)))
    cfg = SimulationConfig.from_dict((proj or base).to_dict())
    cfg.model_name = MODEL["m"]
    cfg.site.update(NAVAILI=0.0, NSOILBASE=p["NSOILBASE"], NSOILBASE_FR=0.01, BG_N_SUPPLY=0.0)
    s0 = cfg.crop_start_date
    cfg.fertilization = [FertilizerEvent(s0 + dt.timedelta(days=d), dose / 3, p["N_recovery"]) for d in split]
    cfg.crop_overrides.update({"NMAXSO": 0.0144, "RGRLAI_MIN_FR": 0.5})
    if "NLEAF" in p:
        cfg.crop_overrides.update({"NSLA": p["NLEAF"], "NLAI": p["NLEAF"]})
    if MODEL["m"].endswith("_NLV"):
        cfg.crop_overrides["NPART"] = 0.0
    if extra:
        cfg.crop_overrides.update(extra)
    return cfg


def sim(dose, x, extra=None):
    r = SimulationRunner(make_cfg(dose, x, extra), wdp).run()
    d = r.daily
    return dict(TAGP=r.summary["TAGP"], TWSO=r.summary["TWSO"], LAI28=float(d.loc[pd.Timestamp(D28), "LAI"]),
                LAIFL=float(d.loc[pd.Timestamp(DFL), "LAI"]), TAGP28=float(d.loc[pd.Timestamp(D28), "TAGP"]),
                TAGPFL=float(d.loc[pd.Timestamp(DFL), "TAGP"]), LAIMAX=r.summary["LAIMAX"], NUPT=r.summary["NuptakeTotal"])


def residuals(x, abs_doses=DOSES, ratio_doses=(23, 207), extra=None):
    S = {d: sim(d, x, extra) for d in set(abs_doses) | set(ratio_doses) | ({115} if ratio_doses else set())}
    out = [(S[d][v] - ABS[d][v]) / (CV_ABS[v] * ABS[d][v]) for d in abs_doses for v in ("TAGP", "TWSO")]
    out += [(S[d][k] / S[115][k] - RATIO[k][d]) / SIG_RATIO[k] for d in ratio_doses for k in MAIN]
    return np.array(out)


def report(x, label, extra=None):
    S = {d: sim(d, x, extra) for d in DOSES}
    rows = []
    for d in DOSES:
        rows.append(dict(dosis=d, TWSO_obs=round(ABS[d]["TWSO"]), TWSO_sim=round(S[d]["TWSO"]), TAGP_obs=round(ABS[d]["TAGP"]),
                         TAGP_sim=round(S[d]["TAGP"]), rLAI28_obs=round(MAIN["LAI28"][d] / MAIN["LAI28"][115], 3),
                         rLAI28_sim=round(S[d]["LAI28"] / S[115]["LAI28"], 3), rLAIFL_obs=round(MAIN["LAIFL"][d] / MAIN["LAIFL"][115], 3),
                         rLAIFL_sim=round(S[d]["LAIFL"] / S[115]["LAIFL"], 3), rTAGPFL_obs=round(MAIN["TAGPFL"][d] / MAIN["TAGPFL"][115], 3),
                         rTAGPFL_sim=round(S[d]["TAGPFL"] / S[115]["TAGPFL"], 3), LAIFL_sim=round(S[d]["LAIFL"], 2), Nupt=round(S[d]["NUPT"], 1)))
    t = pd.DataFrame(rows)
    print(f"\n== {label}\n{t.to_string(index=False)}")
    return t



BOUNDS = {"NSOILBASE": (10.0, 300.0), "N_recovery": (0.2, 0.8), "NLEAF": (0.0, 4.0)}
X0 = {"NSOILBASE": 80.0, "N_recovery": 0.45, "NLEAF": 1.0}
OUT = {}
for label, model, names in [("WOFOST 8.1 standar", "Wofost81_NWLP_CWB_CNB", ["NSOILBASE", "N_recovery"]),
                            ("WOFOST 8.1 + ekstensi N-daun (NLEAF = NSLA = NLAI)", "Wofost81_NWLP_CWB_CNB_NLV", ["NSOILBASE", "N_recovery", "NLEAF"])]:
    MODEL["m"] = model; NAMES[:] = names
    lo = [BOUNDS[n][0] for n in names]; hi = [BOUNDS[n][1] for n in names]
    sol = optimize.least_squares(residuals, [X0[n] for n in names], bounds=(lo, hi), diff_step=0.05, max_nfev=80)
    sse = float(np.sum(sol.fun ** 2)); n = len(sol.fun); k = len(names)
    aicc_ls = n * np.log(sse / n) + 2 * k + 2 * k * (k + 1) / max(n - k - 1, 1)
    aicc = sse + 2 * k + 2 * k * (k + 1) / max(n - k - 1, 1)   # sigma diketahui (bobot tetap): -2lnL = SSE + konstanta
    J = sol.jac; cov = np.linalg.pinv(J.T @ J) * max(sse / max(n - k, 1), 1.0); se = np.sqrt(np.diag(cov))
    best = {nm: float(v) for nm, v in zip(names, sol.x)}
    print(f"\n##### {label}: {({a: round(b, 4) for a, b in best.items()})} SE {dict(zip(names, se.round(4)))} SSE {sse:.2f} n {n} AICc {aicc:.2f}", flush=True)
    t = report(sol.x, label)
    lodo = []
    for h in DOSES:
        abs_d = tuple(d for d in DOSES if d != h)
        rat_d = () if h == 115 else tuple(d for d in (23, 207) if d != h)
        s = optimize.least_squares(lambda x: residuals(x, abs_d, rat_d), sol.x, bounds=(lo, hi), diff_step=0.05, max_nfev=50)
        pr = sim(h, s.x)
        lodo.append(dict(ditahan=h, TWSO_obs=round(ABS[h]["TWSO"]), TWSO_pred=round(pr["TWSO"]), TAGP_obs=round(ABS[h]["TAGP"]), TAGP_pred=round(pr["TAGP"]),
                         **{f"p_{a}": round(float(b), 3) for a, b in zip(names, s.x)}))
    L = pd.DataFrame(lodo)
    ry = float(np.sqrt(np.mean((L.TWSO_pred - L.TWSO_obs) ** 2))); rb = float(np.sqrt(np.mean((L.TAGP_pred - L.TAGP_obs) ** 2)))
    print("LODO:\n", L.to_string(index=False), f"\nRMSE LODO hasil {ry:.0f} ({100*ry/L.TWSO_obs.mean():.1f} %), biomasa {rb:.0f} ({100*rb/L.TAGP_obs.mean():.1f} %)", flush=True)
    trans = []
    for site in ("subang", "indramayu", "bandung"):
        pj = SimulationConfig.load(f"{R}/data/projects/agustiani2018_{site}_inpari32.json")
        ob = pd.read_csv(f"{R}/data/lapangan/obs_{site}_2016_inpari32.csv", parse_dates=["day"]).set_index("day")
        w = build_weather_provider(pj.weather)
        r81 = SimulationRunner(make_cfg(126, sol.x, proj=pj, split=(7, 24, 42)), w).run()
        pp = SimulationConfig.from_dict(pj.to_dict()); pp.model_name = "Wofost72_PP"
        s72 = SimulationRunner(pp, w).run().summary
        tw = float(ob["TWSO"].dropna().iloc[-1]); tg = float(ob["TAGP"].dropna().iloc[-1])
        lai67o = float(ob["LAI"].dropna().iloc[1]); d67 = ob["LAI"].dropna().index[1]
        trans.append(dict(lokasi=site, TWSO_obs=round(tw), TWSO_sim=round(r81.summary["TWSO"]), TWSO_72PP=round(s72["TWSO"]),
                          err_pct=round(100 * (r81.summary["TWSO"] / tw - 1), 1), TAGP_obs=round(tg), TAGP_sim=round(r81.summary["TAGP"]),
                          LAI67_obs=round(lai67o, 2), LAI67_sim=round(float(r81.daily.loc[d67, "LAI"]), 2)))
    T = pd.DataFrame(trans); print("Transfer Agustiani 2016 (126 N):\n", T.to_string(index=False), flush=True)
    OUT[model] = dict(label=label, parameter=best, SE=dict(zip(names, map(float, se))), SSE=sse, n_obs=n, k=k, AICc=float(aicc), AICc_lama_nlnSSE=float(aicc_ls),
                      tabel=t.to_dict("records"), lodo=L.to_dict("records"), rmse_lodo={"TWSO": ry, "TAGP": rb}, transfer=T.to_dict("records"))
OUT["pengaturan"] = {"AMAX_REF": "mengikuti AMAXTB@y", "NPART": 0.0, "NSOILBASE_FR": 0.01, "NAVAILI": 0.0, "NMAXSO": 0.0144, "RGRLAI_MIN_FR": 0.5, "pembagian_N_HST": [7, 28, 42],
                     "observasi_rasio": {k: {str(d): v for d, v in RATIO[k].items()} for k in RATIO}, "sigma_rasio": SIG_RATIO}
json.dump(OUT, open(f"{R}/data/lapangan/hasil_kalibrasi_n5_inpari32.json", "w"), indent=1, default=float)
print("tersimpan", flush=True)
