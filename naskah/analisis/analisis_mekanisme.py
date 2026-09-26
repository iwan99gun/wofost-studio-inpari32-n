"""Bukti kuantitatif untuk pembahasan mekanistik (disimpan ke data/lapangan/mekanisme_n_daun.json):
1. Dekomposisi log rasio LAI (0N/140N) = log rasio jumlah anakan + log rasio luas daun per anakan (data LTFE).
2. Strategi N daun: SPAD (proksi N per luas daun) observasi vs N daun spesifik (SLN) simulasi std & ekstensi.
3. Intersepsi cahaya 1 - exp(-k LAI) observasi vs rasio biomasa/hasil: seberapa jauh penurunan LAI menjelaskan hasil.
4. Rasio biomasa per satuan luas daun (proksi SLA terbalik) observasi vs simulasi."""
import sys, json, math, datetime as dt
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np, pandas as pd
import wofost_app  # noqa
from wofost_app.core.simulation import crop_provider_for, get_model_class
from pcse.util import Afgen

L = ROOT / "data" / "lapangan"
ns = {}
exec(open(str(Path(__file__).with_name("validasi_ltfe.py")), encoding="utf-8").read().split("res = {}")[0], ns)
V = json.load(open(L / "validasi_ltfe_sukamandi.json"))
prov = crop_provider_for(get_model_class("Wofost81_NWLP_CWB_CNB")); prov.set_active_crop("rice", "Rice_IR72")
kdif = Afgen(prov["KDIFTB"])

# data observasi LTFE (Susanti 2023 Tabel 2-3; Hikmah 2021 Tabel 3)
OBS = {
    "S2022": {"tiller": {35: (13.94, 15.88), 60: (14.93, 18.80)}, "LA": {35: (568.45, 860.93), 60: (1232.40, 2741.00)},
              "DM": {35: (7.65, 9.98), 60: (43.56, 58.91)}, "SPAD": {}, "Y": (4.01, 6.87)},
    "S2020": {"tiller": {35: (16.1, 22.1), "FL": (14.2, 19.2)}, "LA": {35: (658.30, 1224.80), "FL": (980.50, 2890.80)},
              "DM": {}, "SPAD": {35: (33.50, 37.18), "FL": (36.94, 40.28)}, "Y": (3.80, 4.70)},
}
out = {"dekomposisi": [], "strategi_N": [], "intersepsi": [], "biomasa_per_luas_daun": []}
for sk, O in OBS.items():
    for t, (la0, la1) in O["LA"].items():
        if t in O["tiller"]:
            ti0, ti1 = O["tiller"][t]
            rl, rt = math.log(la0 / la1), math.log(ti0 / ti1)
            out["dekomposisi"].append(dict(musim=sk, waktu=t, rasio_LAI=la0 / la1, rasio_anakan=ti0 / ti1,
                                           rasio_luas_per_anakan=(la0 / ti0) / (la1 / ti1), porsi_anakan=rt / rl))
    for t, (dm0, dm1) in O["DM"].items():
        la0, la1 = O["LA"][t]
        out["biomasa_per_luas_daun"].append(dict(musim=sk, waktu=t, obs_rasio=(dm0 / la0) / (dm1 / la1)))

# simulasi: SLN dan intersepsi
for sk, S in ns["SEASONS"].items():
    f = V[sk]["std"]["f_tsum"]
    for mk in ("std", "ext"):
        r140 = ns["run"](ns["make"](mk, S["tp"], S["seed"], 140, f, None, V[sk][mk]["A"]["PI"]))
        r0 = ns["run"](ns["make"](mk, S["tp"], S["seed"], 0, f, None, V[sk][mk]["A"]["PI"]))
        doa = r140.summary["DOA"]
        for t in OBS[sk]["LA"]:
            day = doa if t == "FL" else S["tp"] + dt.timedelta(days=t)
            row = {}
            for lab, r in (("0", r0), ("140", r140)):
                d = r.daily.loc[str(day)]
                row[f"LAI{lab}"] = float(d.LAI); row[f"SLN{lab}"] = float(d.NamountLV) * 0.1 / max(float(d.LAI), 1e-6)
                row[f"WLV{lab}"] = float(d.WLV); row[f"DVS{lab}"] = float(d.DVS)
            obs_spad = OBS[sk]["SPAD"].get(t)
            out["strategi_N"].append(dict(musim=sk, model=mk, waktu=t, sim_rasio_LAI=row["LAI0"] / row["LAI140"],
                                          sim_rasio_SLN=row["SLN0"] / row["SLN140"], SLN0=row["SLN0"], SLN140=row["SLN140"],
                                          obs_rasio_LAI=OBS[sk]["LA"][t][0] / OBS[sk]["LA"][t][1],
                                          obs_rasio_SPAD=(obs_spad[0] / obs_spad[1]) if obs_spad else None,
                                          sim_rasio_WLV_per_LAI=(row["WLV0"] / row["LAI0"]) / (row["WLV140"] / row["LAI140"])))
    # intersepsi dari LAI observasi pada 60 HST / berbunga, k = KDIF pada DVS ~1
    t = 60 if sk == "S2022" else "FL"
    la0, la1 = OBS[sk]["LA"][t]
    lai0, lai1 = la0 * 16 / 1e4, la1 * 16 / 1e4
    k = float(kdif(1.0))
    i0, i1 = 1 - math.exp(-k * lai0), 1 - math.exp(-k * lai1)
    y0, y1 = OBS[sk]["Y"]
    out["intersepsi"].append(dict(musim=sk, waktu=t, k=k, LAI0=lai0, LAI140=lai1, f_int0=i0, f_int140=i1, rasio_intersepsi=i0 / i1,
                                  rasio_hasil=y0 / y1, rasio_hasil_per_intersepsi=(y0 / y1) / (i0 / i1)))

for k_, v in out.items():
    print(f"\n== {k_}")
    print(pd.DataFrame(v).round(3).to_string(index=False))
json.dump(out, open(L / "mekanisme_n_daun.json", "w"), indent=1, default=float)
print("\ntersimpan")
