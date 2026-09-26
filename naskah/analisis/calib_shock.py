"""Kalibrasi ulang Inpari-32 dengan SLA fase awal/akhir terpisah (SLATB@ya, SLATB@yb) dan batas berbasis literatur
(Zhang et al. 2025: SLA padi 0.001-0.0055 ha/kg; IR72 PCSE 0.0045 -> 0.0017). Data: 3 lokasi MK 2016 (LAI, TAGP, TWSO)
+ Sukamandi MH 2017/18 hanya LAI 14 & 28 HST (fase awal, belum terbatas N)."""
import sys, json
sys.path.insert(0, r"D:\riset_tani_1")
import numpy as np, pandas as pd
from scipy import optimize
from wofost_app.core.config import SimulationConfig
from wofost_app.core.weather import build_weather_provider
from wofost_app.core.simulation import SimulationRunner, apply_table_modifiers
from wofost_app.core.calibration import load_observations, compute_metrics, _match

R = r"D:\riset_tani_1"
DS = {s: (f"{R}/data/projects/agustiani2018_{s}_inpari32.json", f"{R}/data/lapangan/obs_{s}_2016_inpari32.csv",
          f"{R}/data/lapangan/agustiani2018_hy_inpari32_long.csv", ["LAI", "TAGP", "TWSO"]) for s in ["subang", "indramayu", "bandung"]}
DS["sukamandi_mh17"] = (f"{R}/data/projects/sujinah2020_sukamandi_mh2017_inpari32.json",
                        f"{R}/data/lapangan/obs_sukamandi_mh2017_inpari32.csv",
                        f"{R}/data/lapangan/sujinah2020_sukamandi_mh2017_inpari32_long.csv", ["LAI"])
runners, obs, uncs, vars_ = {}, {}, {}, {}
for k, (pj, ob, lg, vv) in DS.items():
    cfg = SimulationConfig.load(pj); cfg.crop_overrides = {}; cfg.transplant_shock = True
    runners[k] = SimulationRunner(cfg, build_weather_provider(cfg.weather))
    o = load_observations(ob)
    if k == "sukamandi_mh17":
        o = o.loc[o.index <= pd.Timestamp("2017-12-25")]      # hanya 14 & 28 HST
    obs[k] = o; vars_[k] = vv
    L = pd.read_csv(lg); L["day"] = pd.to_datetime(L["day"])
    uncs[k] = {(v, d): u for v, d, u in zip(L.variable, L.day, L.ketidakpastian)}
obs_full = {k: load_observations(DS[k][1]) for k in DS}
def rdvs(k, x):
    res = runners[k].run({"TSUM1": x[0], "TSUM2": x[1]}); out = []
    for v, (o, s_) in _match(res.daily, obs_full[k], ["DVS"]).items(): out.append((s_ - o) / 0.05)
    return np.concatenate(out)
tsum = {}
for k in DS:
    sol_ = optimize.least_squares(lambda x, k=k: rdvs(k, x), [1400, 800], bounds=([800, 300], [2200, 1400]), diff_step=0.05, max_nfev=30); tsum[k] = sol_.x
print("TSUM (syok aktif) per set:", {k: [round(a) for a in v] for k, v in tsum.items()})
T1 = float(np.mean([tsum[k][0] for k in ["subang", "indramayu", "bandung"]])); T2 = float(np.mean([tsum[k][1] for k in ["subang", "indramayu", "bandung"]]))
TS_MH = {"TSUM1": float(tsum["sukamandi_mh17"][0]), "TSUM2": float(tsum["sukamandi_mh17"][1])}
print("TSUM gabungan 2016:", round(T1), round(T2), "| MH:", {k: round(v) for k, v in TS_MH.items()})


def resid(k, p):
    pp = dict(p)
    if k == "sukamandi_mh17":
        pp.update({"TSUM1": TS_MH["TSUM1"], "TSUM2": TS_MH["TSUM2"]})
    res = runners[k].run(pp); out = []
    for v, (o, s) in _match(res.daily, obs[k], vars_[k]).items():
        days = obs[k][v].dropna().index[: len(o)]
        u = np.array([uncs[k].get((v, d), np.nan) for d in days], float)
        u = np.where(np.isnan(u), np.abs(o) * 0.1 + 1e-6, u)
        out.append((s - o) / u)
    return np.concatenate(out) if out else np.array([1e3])


G = ["AMAXTB@y", "SPAN", "TDWI", "RGRLAI"]
lo = [0.6, 20, 15, 0.002]; hi = [1.4, 60, 200, 0.03]
FIX = {"SLATB@ya": 1.2, "SLATB@yb": 0.9}   # literatur: Zhang 2025 SLA awal 0.0055 (IR72 0.0045); pembungaan 0.0017 (Subang Fig.3 0.0016-0.0020)
n = [0]


def joint(x):
    n[0] += 1
    p = {"TSUM1": T1, "TSUM2": T2, **FIX, **dict(zip(G, x))}
    return np.concatenate([resid(k, p) for k in DS])


starts = [[1.0, 35, 50, 0.0085], [0.9, 36, 100, 0.005], [0.9, 36, 60, 0.006]]
sols = []
for x0 in starts:
    s_ = optimize.least_squares(joint, x0, bounds=(lo, hi), diff_step=0.03, max_nfev=120)
    sols.append(s_); print("start", x0, "->", [round(v, 4) for v in s_.x], "SSE", round(float(np.sum(s_.fun ** 2)), 2))
sol = min(sols, key=lambda s_: float(np.sum(s_.fun ** 2)))
best = {"TSUM1": T1, "TSUM2": T2, **FIX, **{g: float(v) for g, v in zip(G, sol.x)}}
print("hasil:", {k: round(v, 3) for k, v in best.items()}, "| SSE", round(float(np.sum(sol.fun ** 2)), 1), "n_obs", len(sol.fun), "eval", n[0])
from pcse.input import YAMLCropDataProvider
prov = YAMLCropDataProvider(); prov.set_active_crop("rice", "Rice_IR72")
tab = apply_table_modifiers(list(prov["SLATB"]), ya=best["SLATB@ya"], yb=best["SLATB@yb"])
print("SLATB IR72   :", [round(v, 5) for v in prov["SLATB"]])
print("SLATB Inpari :", [round(v, 5) for v in tab])
rows = []
for k in DS:
    p = dict(best)
    if k == "sukamandi_mh17":
        p.update({"TSUM1": TS_MH["TSUM1"], "TSUM2": TS_MH["TSUM2"]})
    res = runners[k].run(p)
    full_obs = load_observations(DS[k][1])
    m = compute_metrics(res.daily, full_obs, ["LAI", "TAGP", "TWSO"]); m.insert(0, "set", k); rows.append(m.reset_index())
    print(f"  {k}: DOA {res.summary['DOA']} DOM {res.summary['DOM']} TWSO {res.summary['TWSO']:.0f} TAGP {res.summary['TAGP']:.0f} LAImax {res.summary['LAIMAX']:.2f}")
met = pd.concat(rows); print(met.round(2).to_string(index=False))
json.dump({"parameter": best, "metrik": met.round(4).to_dict(orient="records")}, open(f"{R}/data/lapangan/hasil_kalibrasi_syok_inpari32.json", "w"), indent=1)
