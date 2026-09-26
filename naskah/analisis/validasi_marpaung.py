"""Validasi independen KEDUA modul N: percobaan dosis N pada INPARI-32 SENDIRI (varietas yang sama
dengan kalibrasi) di Karangploso, Malang, Jawa Timur, MK 2023 (Marpaung et al. 2024, Agro Bali 7(2):423-434,
doi 10.37637/ab.v7i2.1597). Data disalin langsung dari tabel PDF (bukan digitalisasi grafik):
LAI (dari luas daun/rumpun), biomassa kering, anakan pada 14/28/42/56 HST, hasil GKG, N jaringan.

Protokol sama dengan validasi LTFE (blind): NSOILBASE disetel HANYA pada hasil petak 0 N (brentq),
lalu SEMUA rasio respons (hasil 50/100/150 vs 0 N; LAI & biomassa 0 N vs 100 N pada 28/42/56 HST)
diprediksi buta dengan parameter final yang dikalibrasi di Sukamandi/Jawa Barat, TANPA penyesuaian apa pun
(f_tsum = 1 karena varietasnya sama). Konfounder dicatat di data JSON (kontrol tanpa P/K/PGPR; PGPR di
semua petak berpupuk; tanggal tanam & jadwal pupuk tidak dilaporkan -> diuji sensitivitas).

Jalankan: python naskah/analisis/validasi_marpaung.py
"""
import sys, json, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from scipy import optimize
import wofost_app  # noqa
from wofost_app.core.config import SimulationConfig, FertilizerEvent, IrrigationEvent
from wofost_app.core.weather import build_weather_provider
from wofost_app.core.simulation import SimulationRunner

L = ROOT / "data" / "lapangan"
D = json.load(open(L / "marpaung2024_karangploso_inpari32.json", encoding="utf-8"))
KA = 0.86                      # GKG 14% kadar air -> bahan kering
HILL_M2 = 16.0                 # 25 x 25 cm
DOSE_OF = D["perlakuan_N_kg_ha"]
AGES = D["tabel3_luas_daun_cm2_per_rumpun"]["umur_hst"]     # [14, 28, 42, 56]

MODELS = {
    "std": ("Wofost81_NWLP_CWB_CNB", ROOT / "data/projects/sujinah2020_sukamandi_mh2017_inpari32_N115.json"),
    "ext": ("Wofost81_NWLP_CWB_CNB_NLV", ROOT / "data/projects/sujinah2020_sukamandi_mh2017_inpari32_N115_nlv.json"),
}


def dose_mean(tab, idx):
    """Rata-rata per dosis (antar konsentrasi PGPR) untuk kolom umur ke-idx."""
    out = {}
    for p, v in tab.items():
        if not p.startswith("P"):
            continue
        d = DOSE_OF[p]
        out.setdefault(d, []).append(v[idx] if isinstance(v, list) else v)
    return {d: float(np.mean(v)) for d, v in out.items()}


OBS = dict(
    Y={d: v * KA * 1000 for d, v in dose_mean(D["tabel7_hasil"]["hasil_ton_ha"], 0).items()},  # kg BK/ha
    LAI={a: {d: v / 625.0 for d, v in dose_mean(D["tabel3_luas_daun_cm2_per_rumpun"], i).items()}
         for i, a in enumerate(AGES)},
    DM={a: {d: v * HILL_M2 * 10.0 for d, v in dose_mean(D["tabel5_berat_kering_g_per_rumpun"], i).items()}
        for i, a in enumerate(AGES)},
)

_w = {}


def wdp():
    if "w" not in _w:
        c = SimulationConfig.load(MODELS["std"][1])
        c.weather.latitude, c.weather.longitude = D["koordinat_perkiraan"]["lat"], D["koordinat_perkiraan"]["lon"]
        _w["w"] = build_weather_provider(c.weather)
    return _w["w"]


def make(mk, tp, dose, nsoil=None, split=(7, 30, 45)):
    model, pj = MODELS[mk]
    c = SimulationConfig.load(pj)
    c.model_name = model
    c.weather.latitude, c.weather.longitude = D["koordinat_perkiraan"]["lat"], D["koordinat_perkiraan"]["lon"]
    c.crop_start_date, c.crop_end_date, c.seedling_age_days = tp, tp + dt.timedelta(days=200), 14
    if nsoil is not None:
        c.site["NSOILBASE"] = float(nsoil)
    rec = c.fertilization[0].recovery
    c.fertilization = [FertilizerEvent(tp + dt.timedelta(days=d), dose / 3, rec) for d in split] if dose > 0 else []
    c.irrigation = [IrrigationEvent(tp + dt.timedelta(days=d), 2.0, 1.0) for d in range(0, 131, 2)]
    return c


def run(c):
    return SimulationRunner(c, wdp()).run()


def sim_all(mk, tp, nsoil, split=(7, 30, 45)):
    import pandas as pd
    out = {}
    for dose in (0, 50, 100, 150):
        r = run(make(mk, tp, dose, nsoil, split))
        dd = r.daily
        g = lambda v, day: float(dd.loc[pd.Timestamp(tp + dt.timedelta(days=day)), v])
        out[dose] = dict(Y=r.summary["TWSO"], DOM=(r.summary["DOM"] - tp).days,
                         LAI={a: g("LAI", a) for a in AGES}, DM={a: g("TAGP", a) for a in AGES})
    return out


def predict(mk, tp, split=(7, 30, 45)):
    y0 = OBS["Y"][0]
    def g(ns):
        return run(make(mk, tp, 0, ns, split)).summary["TWSO"] - y0
    lo, hi = 1.0, 390.0
    if g(hi) < 0:
        ns = hi
    else:
        ns = optimize.brentq(g, lo, hi, xtol=0.5)
    S = sim_all(mk, tp, ns, split)
    A = dict(NSOILBASE_fit=float(ns), DOM_0N=S[0]["DOM"], DOM_100N=S[100]["DOM"],
             Y={d: S[d]["Y"] for d in S},
             rY={d: S[d]["Y"] / S[0]["Y"] for d in (50, 100, 150)},
             rLAI={a: S[0]["LAI"][a] / S[100]["LAI"][a] for a in (28, 42, 56)},
             rDM={a: S[0]["DM"][a] / S[100]["DM"][a] for a in (28, 42, 56)})
    return A


def main():
    obs = dict(rY={d: OBS["Y"][d] / OBS["Y"][0] for d in (50, 100, 150)},
               rLAI={a: OBS["LAI"][a][0] / OBS["LAI"][a][100] for a in (28, 42, 56)},
               rDM={a: OBS["DM"][a][0] / OBS["DM"][a][100] for a in (28, 42, 56)},
               LAI56={d: OBS["LAI"][56][d] for d in (0, 50, 100, 150)},
               Y_kgBK_ha=OBS["Y"])
    print("OBSERVASI (rata-rata dosis):")
    print(" hasil BK kg/ha:", {d: round(v) for d, v in OBS["Y"].items()})
    print(" rasio hasil vs 0N:", {d: round(v, 3) for d, v in obs["rY"].items()})
    print(" rasio LAI 0/100N:", {a: round(v, 3) for a, v in obs["rLAI"].items()})
    print(" rasio DM  0/100N:", {a: round(v, 3) for a, v in obs["rDM"].items()})

    tp0 = dt.date(2023, 5, 15)
    res = dict(observasi=obs)
    for mk in ("std", "ext"):
        A = predict(mk, tp0)
        res[mk] = A
        print(f"\n[{mk}] NSOILBASE(fit 0N) = {A['NSOILBASE_fit']:.1f} kg N/ha; DOM 0N/100N = {A['DOM_0N']}/{A['DOM_100N']} HST")
        print("  prediksi rY  :", {d: round(v, 3) for d, v in A["rY"].items()})
        print("  prediksi rLAI:", {a: round(v, 3) for a, v in A["rLAI"].items()})
        print("  prediksi rDM :", {a: round(v, 3) for a, v in A["rDM"].items()})
        # sensitivitas tanggal tanam & jadwal pupuk
        sens = {}
        for lab, tp, split in (("tanam_1Mei", dt.date(2023, 5, 1), (7, 30, 45)),
                               ("tanam_1Juni", dt.date(2023, 6, 1), (7, 30, 45)),
                               ("pupuk_7_21_35", tp0, (7, 21, 35))):
            B = predict(mk, tp, split)
            sens[lab] = dict(NSOILBASE_fit=B["NSOILBASE_fit"],
                             rY100=B["rY"][100], rLAI56=B["rLAI"][56])
        res[mk]["sensitivitas"] = sens
        print("  sensitivitas:", {k: {kk: round(vv, 3) for kk, vv in v.items()} for k, v in sens.items()})

    json.dump(res, open(L / "validasi_marpaung_karangploso.json", "w"), indent=1, default=float)
    print("\ntersimpan -> data/lapangan/validasi_marpaung_karangploso.json")


if __name__ == "__main__":
    main()
