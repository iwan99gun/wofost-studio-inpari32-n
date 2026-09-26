"""Validasi independen modul N WOFOST 8.1 dengan petak omisi N LTFE KP Sukamandi (BB Padi).

Data (literatur terbuka, stasiun yang sama dengan Sujinah et al. 2020, musim & varietas berbeda):
  S2022: Susanti et al. 2023, IOP Conf. Ser. EES 1165:012026 (CC BY 3.0). MK 2022, Inpari-33, bibit 21 HSS, 25x25 cm.
         +PK (0 N) vs +NPK (140 kg N/ha). Tabel 3: BK & luas daun per rumpun 21/35/60 HST; Tabel 4: hasil 14 % KA.
  S2020: Hikmah et al. 2021, J. Agron. Indonesia 49(3):242-250. Jul-Des 2020, Inpari-33, bibit 18 HSS, 25x25 cm.
         Tanpa N vs NPK (140 kg N/ha; urea 7 HST, 30 HST, primordia). Tabel 3: luas daun 21/35 HST & berbunga; Tabel 4: GKG.
Tanggal tanam tidak dilaporkan -> asumsi + uji sensitivitas +/-21 hari. Fenologi Inpari-33 (umur 107 HSS, deskripsi
varietas BB Padi) vs Inpari-32 (120 HSS): TSUM1/TSUM2 diskalakan sama rata agar durasi lapang = 107 - umur bibit.

Dua tahap:
  A (buta): parameter N kalibrasi Sujinah (NSOILBASE Sukamandi) tanpa perubahan -> prediksi semua.
  B (INS dari petak omisi, praktik SSNM Dobermann et al. 2003): NSOILBASE diestimasi HANYA dari hasil petak 0-N
    musim itu; lalu diprediksi hasil 140 N, rasio hasil, rasio LAI 3 fase, rasio biomasa (independen dari kalibrasi).
"""
import sys, json, datetime as dt
sys.path.insert(0, r"D:\riset_tani_1")
import numpy as np, pandas as pd
from scipy import optimize
import wofost_app  # noqa
from wofost_app.core.config import SimulationConfig, FertilizerEvent, IrrigationEvent
from wofost_app.core.weather import build_weather_provider
from wofost_app.core.simulation import SimulationRunner

R = r"D:\riset_tani_1"
HILLS = 16.0        # 25 x 25 cm
KA = 0.86           # 14 % KA -> bahan kering
SEASONS = {
    "S2022": dict(tp=dt.date(2022, 5, 1), seed=21, sumber="Susanti et al. 2023 IOP EES 1165:012026",
                  Y0=4.01, Y140=6.87, LA={21: (222.34, 233.58), 35: (568.45, 860.93), 60: (1232.40, 2741.00)},
                  DM={35: (7.65, 9.98), 60: (43.56, 58.91)}, CV_LA={21: .1464, 35: .1422, 60: .196}, CV_DM={35: .1491, 60: .141}),
    "S2020": dict(tp=dt.date(2020, 8, 2), seed=18, sumber="Hikmah et al. 2021 J. Agron. Indonesia 49(3):242-250",
                  Y0=3.80, Y140=4.70, LA={21: (272.00, 386.13), 35: (658.30, 1224.80), "FL": (980.50, 2890.80)},
                  DM={}, CV_LA={21: .15, 35: .15, "FL": .20}, CV_DM={}),
}
MODELS = {
    "std": ("Wofost81_NWLP_CWB_CNB", f"{R}/data/projects/sujinah2020_sukamandi_mh2017_inpari32_N115.json"),
    "ext": ("Wofost81_NWLP_CWB_CNB_NLV", f"{R}/data/projects/sujinah2020_sukamandi_mh2017_inpari32_N115_nlv.json"),
}
wdp = build_weather_provider(SimulationConfig.load(MODELS["std"][1]).weather)


def make(model_key, tp, seed, dose, f_tsum, nsoil=None, pi_day=35):
    model, pj = MODELS[model_key]
    c = SimulationConfig.load(pj)
    c.model_name = model
    c.crop_start_date, c.crop_end_date, c.seedling_age_days = tp, tp + dt.timedelta(days=200), int(seed)
    c.crop_overrides["TSUM1"] = c.crop_overrides["TSUM1"] * f_tsum
    c.crop_overrides["TSUM2"] = c.crop_overrides["TSUM2"] * f_tsum
    if nsoil is not None:
        c.site["NSOILBASE"] = float(nsoil)
    rec = c.fertilization[0].recovery
    c.fertilization = [FertilizerEvent(tp + dt.timedelta(days=d), dose / 3, rec) for d in (7, 30, pi_day)] if dose > 0 else []
    # petak LTFE digenangi terus (2-3 cm) -> irigasi 2 cm tiap 2 hari (efisiensi 1) agar tidak ada cekaman air buatan model
    c.irrigation = [IrrigationEvent(tp + dt.timedelta(days=d), 2.0, 1.0) for d in range(0, 121, 2)]
    return c


def run(c):
    r = SimulationRunner(c, wdp).run()
    return r


def fit_f(model_key, tp, seed):
    target = 107 - seed
    def dur(f):
        r = run(make(model_key, tp, seed, 140, f))
        return (r.summary["DOM"] - tp).days - target
    lo, hi = 0.6, 1.1
    for _ in range(14):
        mid = 0.5 * (lo + hi)
        if dur(mid) > 0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def predict(model_key, S, tp, f, nsoil=None):
    r140 = run(make(model_key, tp, S["seed"], 140, f, nsoil))
    doa = r140.summary["DOA"]
    pi = max(25, (doa - tp).days - 25)
    r140 = run(make(model_key, tp, S["seed"], 140, f, nsoil, pi))
    r0 = run(make(model_key, tp, S["seed"], 0, f, nsoil, pi))
    out = dict(Y0=r0.summary["TWSO"], Y140=r140.summary["TWSO"], DOA_HST=(doa - tp).days, DOM_HST=(r140.summary["DOM"] - tp).days, PI=pi)
    for k in S["LA"]:
        day = doa if k == "FL" else tp + dt.timedelta(days=k)
        l0 = float(r0.daily.loc[str(day), "LAI"]); l1 = float(r140.daily.loc[str(day), "LAI"])
        out[f"LAI{k}_0"], out[f"LAI{k}_140"], out[f"rLAI{k}"] = l0, l1, l0 / l1
    for k in S["DM"]:
        day = tp + dt.timedelta(days=k)
        b0 = float(r0.daily.loc[str(day), "TAGP"]); b1 = float(r140.daily.loc[str(day), "TAGP"])
        out[f"rDM{k}"] = b0 / b1
    out["rY"] = out["Y0"] / out["Y140"]
    return out


def obs_table(S):
    o = dict(Y0=S["Y0"] * KA * 1000, Y140=S["Y140"] * KA * 1000, rY=S["Y0"] / S["Y140"])
    for k, (a, b) in S["LA"].items():
        o[f"LAI{k}_0"], o[f"LAI{k}_140"], o[f"rLAI{k}"] = a * HILLS / 1e4, b * HILLS / 1e4, a / b
    for k, (a, b) in S["DM"].items():
        o[f"rDM{k}"] = a / b
    return o


res = {}
for sk, S in SEASONS.items():
    ob = obs_table(S)
    print(f"\n######## {sk} ({S['sumber']}); tanam asumsi {S['tp']}, bibit {S['seed']} HSS", flush=True)
    print("obs:", {k: round(v, 3) for k, v in ob.items()}, flush=True)
    res[sk] = {"obs": ob, "sumber": S["sumber"], "tanam_asumsi": str(S["tp"])}
    for mk in MODELS:
        f = fit_f(mk, S["tp"], S["seed"])
        A = predict(mk, S, S["tp"], f)
        # tahap B: NSOILBASE dari hasil petak 0-N saja
        g = lambda ns: run(make(mk, S["tp"], S["seed"], 0, f, ns, A["PI"])).summary["TWSO"] - ob["Y0"]
        try:
            ns = optimize.brentq(g, 0.0, 300.0, xtol=0.5)
        except ValueError:
            ns = 0.0 if g(0.0) > 0 else 300.0
        B = predict(mk, S, S["tp"], f, ns)
        # sensitivitas tanggal tanam untuk tahap B (NSOILBASE dipasang ulang per tanggal)
        sens = []
        for dd in (-21, 21):
            tp2 = S["tp"] + dt.timedelta(days=dd)
            f2 = fit_f(mk, tp2, S["seed"])
            g2 = lambda ns_: run(make(mk, tp2, S["seed"], 0, f2, ns_, A["PI"])).summary["TWSO"] - ob["Y0"]
            try:
                ns2 = optimize.brentq(g2, 0.0, 300.0, xtol=0.5)
            except ValueError:
                ns2 = 0.0 if g2(0.0) > 0 else 300.0
            sens.append(dict(geser_hari=dd, NSOILBASE=round(ns2, 1), **{k: round(v, 3) for k, v in predict(mk, S, tp2, f2, ns2).items()}))
        res[sk][mk] = dict(f_tsum=f, A=A, B=B, NSOILBASE_B=ns, sensitivitas=sens)
        keys = ["Y0", "Y140", "rY"] + [k for k in ob if k.startswith("rLAI") or k.startswith("rDM")] + [k for k in ob if k.startswith("LAI") and k.endswith("_140")]
        print(f"  [{mk}] f_TSUM {f:.3f}; DOA {A['DOA_HST']} HST, DOM {A['DOM_HST']} HST; NSOILBASE tahap B = {ns:.1f}", flush=True)
        print("   " + " | ".join(f"{k}: obs {ob[k]:.3g} A {A[k]:.3g} B {B[k]:.3g}" for k in keys), flush=True)
        print("   sensitivitas tanggal (B):", [(s["geser_hari"], s["NSOILBASE"], s["Y140"], s["rY"]) for s in sens], flush=True)

res["catatan"] = "Irigasi 2 cm/2 hari meniru penggenangan LTFE; tanggal tanam asumsi; fenologi Inpari-33 via skala TSUM."
json.dump(res, open(f"{R}/data/lapangan/validasi_ltfe_sukamandi.json", "w"), indent=1, default=float)
print("tersimpan", flush=True)
