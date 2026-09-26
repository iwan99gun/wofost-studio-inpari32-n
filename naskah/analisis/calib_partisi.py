"""Kalibrasi bersama parameter produksi potensial + PART_DELAY (penundaan alokasi pasca-antesis ke organ simpan),
menjawab pertanyaan: bisakah partisi pasca-berbunga dikalibrasi untuk memperbaiki kecocokan TWST/TAGP?
Data: 3 lokasi Agustiani et al. 2018 MK 2016 (LAI, TAGP, TWST, TWSO pada 7/67/112 HST) + LAI awal Sukamandi
(TSUM tetap seperti Langkah 1 asli, tidak dikalibrasi ulang di sini -> perbandingan adil, hanya menambah PART_DELAY
dan mengizinkan SPAN/AMAXTB@y/TDWI/RGRLAI menyesuaikan)."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np, pandas as pd
from scipy import optimize
import wofost_app  # noqa
from wofost_app.core.config import SimulationConfig
from wofost_app.core.weather import build_weather_provider
from wofost_app.core.simulation import SimulationRunner
from wofost_app.core.calibration import load_observations, _match

L = ROOT / "data" / "lapangan"; PJ = ROOT / "data" / "projects"
SITES = ["subang", "indramayu", "bandung"]
FIX = {"TSUM1": 1365.30912, "TSUM2": 796.02769, "SLATB@ya": 1.2, "SLATB@yb": 0.9}   # dari kalibrasi TSUM Langkah 1
VARS = ["LAI", "TAGP", "TWST", "TWSO"]
runners, obs, uncs = {}, {}, {}
for s in SITES:
    cfg = SimulationConfig.load(PJ / f"agustiani2018_{s}_inpari32.json"); cfg.crop_overrides = dict(FIX); cfg.transplant_shock = True
    runners[s] = SimulationRunner(cfg, build_weather_provider(cfg.weather))
    obs[s] = load_observations(L / f"obs_{s}_2016_inpari32.csv")
    U = pd.read_csv(L / "agustiani2018_hy_inpari32_long.csv"); U["day"] = pd.to_datetime(U["day"])
    uncs[s] = {(v, d): u for v, d, u in zip(U.variable, U.day, U.ketidakpastian)}


def resid(s, p):
    res = runners[s].run(p); out = []
    for v, (o, sim) in _match(res.daily, obs[s], VARS).items():
        days = obs[s][v].dropna().index[: len(o)]
        u = np.array([uncs[s].get((v, d), np.nan) for d in days], float)
        u = np.where(np.isnan(u), np.abs(o) * 0.1 + 1e-6, u)
        out.append((sim - o) / u)
    return np.concatenate(out) if out else np.array([])


NAMES = ["AMAXTB@y", "SPAN", "TDWI", "RGRLAI", "PART_DELAY"]
LO = [0.6, 20, 15, 0.002, 0.0]
HI = [1.4, 60, 250, 0.03, 0.8]


def joint(x, use_part_delay=True):
    p = {**FIX, **dict(zip(NAMES, x))}
    if not use_part_delay:
        p = {k: v for k, v in p.items() if k != "PART_DELAY"}
    return np.concatenate([resid(s, p) for s in SITES])


def joint_baseline(x):
    p = {**FIX, "AMAXTB@y": x[0], "SPAN": x[1], "TDWI": x[2], "RGRLAI": x[3]}
    return np.concatenate([resid(s, p) for s in SITES])


print("=== A. Dasar (tanpa PART_DELAY, parameter Langkah 1 saat ini) ===")
x0_base = [0.90186, 36.64537, 143.83359, 0.0035]
r0 = joint_baseline(x0_base)
print("SSE dasar (parameter final saat ini, tanpa refit):", round(float(np.sum(r0 ** 2)), 2), "n_obs", len(r0))
sol_base = optimize.least_squares(joint_baseline, x0_base, bounds=(LO[:4], HI[:4]), diff_step=0.03, max_nfev=150)
print("Refit tanpa PART_DELAY:", dict(zip(NAMES[:4], np.round(sol_base.x, 4))), "SSE", round(float(np.sum(sol_base.fun ** 2)), 2))

print("\n=== B. Dengan PART_DELAY (multi-start) ===")
starts = [x0_base + [0.0], x0_base + [0.3], sol_base.x.tolist() + [0.2], sol_base.x.tolist() + [0.4]]
sols = []
for x0 in starts:
    s_ = optimize.least_squares(joint, x0, bounds=(LO, HI), diff_step=0.03, max_nfev=200)
    sols.append(s_)
    print("start", [round(v, 3) for v in x0], "->", dict(zip(NAMES, np.round(s_.x, 4))), "SSE", round(float(np.sum(s_.fun ** 2)), 2))
sol = min(sols, key=lambda s_: float(np.sum(s_.fun ** 2)))
best = {**FIX, **dict(zip(NAMES, map(float, sol.x)))}
n_obs = len(sol.fun); k = len(NAMES)
sse_b = float(np.sum(sol.fun ** 2))
aicc_b = sse_b + 2 * k + 2 * k * (k + 1) / max(n_obs - k - 1, 1)
sse_a = float(np.sum(sol_base.fun ** 2))
aicc_a = sse_a + 2 * 4 + 2 * 4 * 5 / max(n_obs - 4 - 1, 1)
print(f"\nTerbaik dengan PART_DELAY: {dict(zip(NAMES, np.round(sol.x, 4)))}")
print(f"SSE tanpa PART_DELAY (k=4): {sse_a:.2f}  AICc {aicc_a:.2f}")
print(f"SSE dengan PART_DELAY (k=5): {sse_b:.2f}  AICc {aicc_b:.2f}  (n_obs={n_obs})")

print("\n=== C. Detail per lokasi (nilai akhir 112 HST) ===")
rows = []
for s in SITES:
    r_a = runners[s].run({**FIX, **dict(zip(NAMES[:4], sol_base.x))})
    r_b = runners[s].run(best)
    o = obs[s]
    row = dict(lokasi=s)
    for v in ("TAGP", "TWST", "TWSO"):
        ov = o[v].dropna().iloc[-1]
        row[f"{v}_obs"] = round(ov)
        row[f"{v}_A_tanpaPD"] = round(r_a.summary[v])
        row[f"{v}_B_PART_DELAY"] = round(r_b.summary[v])
        row[f"{v}_errA_%"] = round(100 * (r_a.summary[v] / ov - 1), 1)
        row[f"{v}_errB_%"] = round(100 * (r_b.summary[v] / ov - 1), 1)
    rows.append(row)
T = pd.DataFrame(rows)
for v in ("TAGP", "TWST", "TWSO"):
    print(f"\n-- {v} --")
    print(T[["lokasi", f"{v}_obs", f"{v}_A_tanpaPD", f"{v}_errA_%", f"{v}_B_PART_DELAY", f"{v}_errB_%"]].to_string(index=False))

out = dict(parameter_A_tanpa_PART_DELAY={n: float(v) for n, v in zip(NAMES[:4], sol_base.x)},
          parameter_B_dengan_PART_DELAY=best, SSE_A=sse_a, AICc_A=aicc_a, SSE_B=sse_b, AICc_B=aicc_b, n_obs=n_obs,
          detail_per_lokasi=T.to_dict("records"),
          catatan="A = refit SPAN/AMAXTB@y/TDWI/RGRLAI tanpa PART_DELAY (k=4); B = + PART_DELAY (k=5), TSUM/SLATB tetap.")
json.dump(out, open(L / "kalibrasi_partisi_pascaberbunga.json", "w"), indent=1, default=float)
print("\ntersimpan -> data/lapangan/kalibrasi_partisi_pascaberbunga.json")
