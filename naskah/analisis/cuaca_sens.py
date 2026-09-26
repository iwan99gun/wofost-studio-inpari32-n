"""Poin 3 reviewer: sensitivitas hasil kunci terhadap sumber cuaca (Open-Meteo reanalisis vs NASA POWER).
(a) statistik harian cuaca per periode tanam; (b) kalibrasi respons N Sujinah (parameter final, tanpa refit);
(c) validasi buta petak tanpa N LTFE 2022 & 2020; (d) potensial 7.2 & kalibrasi Agustiani 2016."""
import sys, json, datetime as dt
sys.path.insert(0, r"D:\riset_tani_1")
import numpy as np, pandas as pd
import wofost_app  # noqa
from wofost_app.core.config import SimulationConfig, WeatherConfig, FertilizerEvent, IrrigationEvent
from wofost_app.core.weather import build_weather_provider
from wofost_app.core.simulation import SimulationRunner

R = r"D:\riset_tani_1"; L = f"{R}/data/lapangan"
V = json.load(open(f"{L}/validasi_ltfe_sukamandi.json"))
WP = {}


def wdp(src, lat, lon):
    k = (src, round(lat, 3), round(lon, 3))
    if k not in WP:
        WP[k] = build_weather_provider(WeatherConfig(source=src, latitude=lat, longitude=lon))
    return WP[k]


def wstats(w, start, days):
    rows = []
    for i in range(days):
        d = w(start + dt.timedelta(days=i))
        rows.append(dict(TMIN=d.TMIN, TMAX=d.TMAX, IRRAD=d.IRRAD / 1e6, RAIN=d.RAIN * 10, VAP=d.VAP))
    df = pd.DataFrame(rows)
    return dict(TMIN=df.TMIN.mean(), TMAX=df.TMAX.mean(), IRRAD_MJ=df.IRRAD.mean(), RAIN_mm_total=df.RAIN.sum(), VAP=df.VAP.mean())


out = {"statistik": [], "sujinah": [], "ltfe": [], "agustiani": []}
periods = [("Sujinah MH17/18", -6.35, 107.65, dt.date(2017, 11, 22), 100), ("LTFE MK2022", -6.35, 107.65, dt.date(2022, 5, 1), 90),
           ("LTFE 2020", -6.35, 107.65, dt.date(2020, 8, 2), 90), ("Agustiani Subang", -6.624, 107.746, dt.date(2016, 5, 1), 110),
           ("Agustiani Indramayu", -6.518, 108.291, dt.date(2016, 5, 1), 110), ("Agustiani Bandung", -7.011, 107.746, dt.date(2016, 5, 1), 115)]
for lab, lat, lon, s, n in periods:
    a = wstats(wdp("openmeteo", lat, lon), s, n); b = wstats(wdp("nasapower", lat, lon), s, n)
    out["statistik"].append(dict(periode=lab, **{f"OM_{k}": round(v, 2) for k, v in a.items()}, **{f"NP_{k}": round(v, 2) for k, v in b.items()}))
S = pd.DataFrame(out["statistik"]); print(S.to_string(index=False), flush=True)

# (b) Sujinah: parameter final (proyek per dosis), cuaca diganti
OBS = {23: 5410 * .86, 115: 6920 * .86, 207: 7610 * .86}
for src in ("openmeteo", "nasapower"):
    for d in (23, 115, 207):
        c = SimulationConfig.load(f"{R}/data/projects/sujinah2020_sukamandi_mh2017_inpari32_N{d}.json")
        r = SimulationRunner(c, wdp(src, -6.35, 107.65)).run()
        out["sujinah"].append(dict(cuaca=src, dosis=d, TWSO_obs=round(OBS[d]), TWSO_sim=round(r.summary["TWSO"]), DOA=str(r.summary["DOA"]), DOM=str(r.summary["DOM"])))
print(pd.DataFrame(out["sujinah"]).to_string(index=False), flush=True)

# (c) LTFE: tanpa N, buta (parameter final std), penggenangan
ns = {}; exec(open(str(__import__("pathlib").Path(__file__).with_name("validasi_ltfe.py")), encoding="utf-8").read().split("res = {}")[0], ns)
for src in ("openmeteo", "nasapower"):
    ns["wdp"] = wdp(src, -6.35, 107.65)
    for sk, S_ in ns["SEASONS"].items():
        f = ns["fit_f"]("std", S_["tp"], S_["seed"])
        A = ns["predict"]("std", S_, S_["tp"], f)
        o = V[sk]["obs"]
        out["ltfe"].append(dict(cuaca=src, musim=sk, f_TSUM=round(f, 3), Y0_obs=round(o["Y0"]), Y0_sim=round(A["Y0"]), err_Y0_pct=round(100 * (A["Y0"] / o["Y0"] - 1), 1),
                                Y140_obs=round(o["Y140"]), Y140_sim=round(A["Y140"])))
print(pd.DataFrame(out["ltfe"]).to_string(index=False), flush=True)

# (d) Agustiani: model potensial terkalibrasi (7.2 PP) dengan kedua cuaca
for site in ("subang", "indramayu", "bandung"):
    pj = SimulationConfig.load(f"{R}/data/projects/agustiani2018_{site}_inpari32.json")
    ob = pd.read_csv(f"{L}/obs_{site}_2016_inpari32.csv").TWSO.dropna().iloc[-1]
    row = dict(lokasi=site, TWSO_obs=round(ob))
    for src in ("openmeteo", "nasapower"):
        r = SimulationRunner(pj, wdp(src, pj.weather.latitude, pj.weather.longitude)).run()
        row[f"TWSO_{src}"] = round(r.summary["TWSO"]); row[f"DOA_{src}"] = str(r.summary["DOA"])
    out["agustiani"].append(row)
print(pd.DataFrame(out["agustiani"]).to_string(index=False), flush=True)
json.dump(out, open(f"{L}/sensitivitas_sumber_cuaca.json", "w"), indent=1, default=str)
print("tersimpan")
