"""Poin 6: pembanding dengan ORYZA v3 yang dikalibrasi Agustiani et al. (2018a) pada eksperimen yang sama.
Statistik ORYZA (teks hlm. 14): RMSEn 23 %; RMSE AGB 1,6 t/ha, batang 0,7 t/ha, LAI 0,5 (satu observasi dikecualikan);
SD eksperimen rata-rata 1,1 t/ha, 0,6 t/ha, 0,2. Di sini dihitung statistik yang sama untuk WOFOST 7.2 terkalibrasi
(tahap 1) pada 3 lokasi x 3 waktu (7, 67, 112 HST), dengan dan tanpa LAI masak (daun menguning ikut terukur)."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np, pandas as pd
import wofost_app  # noqa
from wofost_app.core.config import SimulationConfig
from wofost_app.core.weather import build_weather_provider
from wofost_app.core.simulation import SimulationRunner

L = ROOT / "data" / "lapangan"
obs = pd.read_csv(L / "agustiani2018_hy_inpari32_long.csv", parse_dates=["day"])
rows = []
for s, lab in (("subang", "Subang"), ("indramayu", "Indramayu"), ("bandung", "Bandung")):
    cfg = SimulationConfig.load(ROOT / "data" / "projects" / f"agustiani2018_{s}_inpari32.json")
    d = SimulationRunner(cfg, build_weather_provider(cfg.weather)).run().daily
    for v in ("TAGP", "TWST", "LAI"):
        for _, o in obs[(obs.lokasi == lab) & (obs.variable == v)].iterrows():
            day = min(o.day, d.index.max())          # obs 112 HST bisa sesudah masak simulasi -> nilai akhir
            rows.append(dict(lokasi=lab, var=v, DAT=o.DAT, obs=o.value, sim=float(d.loc[day, v])))
T = pd.DataFrame(rows)
sc = {"TAGP": 1e-3, "TWST": 1e-3, "LAI": 1.0}
out = {}
for lab, sub in (("semua", T), ("tanpa LAI masak", T[~((T["var"] == "LAI") & (T.DAT >= 100))])):
    r = {}
    for v in ("TAGP", "TWST", "LAI"):
        t = sub[sub["var"] == v]
        r[v] = float(np.sqrt(np.mean((t.sim - t.obs) ** 2)) * sc[v])
    x = sub.assign(o=sub.obs * sub["var"].map(sc), s=sub.sim * sub["var"].map(sc))
    rmsen = float(np.mean([np.sqrt(np.mean((g.s - g.o) ** 2)) / g.o.mean() for _, g in x.groupby("var")]) * 100)
    r2 = {v: float(np.corrcoef(g.s, g.o)[0, 1] ** 2) for v, g in x.groupby("var")}
    out[lab] = dict(RMSE_AGB_t=r["TAGP"], RMSE_batang_t=r["TWST"], RMSE_LAI=r["LAI"], RMSEn_rata2_pct=rmsen, r2=r2)
out["ORYZA_Agustiani2018"] = dict(RMSE_AGB_t=1.6, RMSE_batang_t=0.7, RMSE_LAI=0.5, RMSEn_pct=23, catatan="satu observasi dikecualikan; r2 > 0.93")
out["SD_eksperimen"] = dict(AGB_t=1.1, batang_t=0.6, LAI=0.2)
print(json.dumps(out, indent=1))
json.dump(out, open(L / "pembanding_oryza.json", "w"), indent=1)
