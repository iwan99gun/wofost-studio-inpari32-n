"""Simpan data LTFE (CSV), figur validasi, dan ulang uji transfer Agustiani dengan penggenangan."""
import sys, json, datetime as dt
sys.path.insert(0, r"D:\riset_tani_1")
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import wofost_app  # noqa
from wofost_app.core.config import SimulationConfig, FertilizerEvent, IrrigationEvent
from wofost_app.core.weather import build_weather_provider
from wofost_app.core.simulation import SimulationRunner

R = r"D:\riset_tani_1"; L = f"{R}/data/lapangan"
V = json.load(open(f"{L}/validasi_ltfe_sukamandi.json"))

# ---- CSV data sumber
rows = []
src = {"S2022": "Susanti et al. 2023, IOP Conf. Ser. Earth Environ. Sci. 1165:012026, doi:10.1088/1755-1315/1165/1/012026 (Tabel 3, 4)",
       "S2020": "Hikmah et al. 2021, J. Agron. Indonesia 49(3):242-250, doi:10.24831/jai.v49i3.38323 (Tabel 3, 4)"}
musim = {"S2022": "MK 2022", "S2020": "Jul-Des 2020"}
for sk in ("S2022", "S2020"):
    ob = V[sk]["obs"]
    for k, v in ob.items():
        rows.append(dict(set=sk, musim=musim[sk], varietas="Inpari 33", lokasi="LTFE KP Sukamandi (6.20 S, 107.65 E, 16 m)",
                         variabel=k, nilai=round(v, 4), satuan=("kg BK/ha" if k.startswith("Y") and not k.startswith("rY") else "-"),
                         catatan="0 = petak +PK (tanpa N); 140 = +NPK 140 kg N/ha; LAI = luas daun/rumpun x 16 rumpun/m2; hasil x 0.86",
                         sumber=src[sk]))
pd.DataFrame(rows).to_csv(f"{L}/ltfe_sukamandi_omisi_n.csv", index=False)

res2 = json.load(open(f"{L}/hasil_kalibrasi_n5_inpari32.json")); p = res2["final"]["std"]
# ---- figur
fig, ax = plt.subplots(1, 3, figsize=(11, 3.4), dpi=150)
# (a) hasil 0-N buta vs obs; tambah Sujinah 23 N sebagai titik kalibrasi
pts = [("LTFE MK2022", V["S2022"]["obs"]["Y0"], V["S2022"]["std"]["A"]["Y0"]), ("LTFE 2020", V["S2020"]["obs"]["Y0"], V["S2020"]["std"]["A"]["Y0"])]
for lab, o, s in pts:
    ax[0].plot(o, s, "o", ms=6, label=lab)
ax[0].plot([2500, 4500], [2500, 4500], "k--", lw=.8)
ax[0].set_xlabel("Hasil petak tanpa N obs [kg BK/ha]"); ax[0].set_ylabel("Simulasi buta [kg BK/ha]"); ax[0].legend(fontsize=7)
ax[0].set_title("(a) Pasokan N tanah (tanpa kalibrasi ulang)", fontsize=8)
# (b) NSOILBASE dari petak omisi vs kalibrasi
nb = [V["S2022"]["std"]["NSOILBASE_B"], V["S2020"]["std"]["NSOILBASE_B"]]
ax[1].bar(["Kalibrasi\nSujinah 2017/18", "Omisi\nMK2022", "Omisi\n2020"], [p["NSOILBASE"], *nb], color=["C7", "C0", "C1"])
ax[1].set_ylabel("NSOILBASE [kg N/ha]"); ax[1].set_title("(b) INS: kalibrasi vs petak omisi independen", fontsize=8)
for i, v in enumerate([p["NSOILBASE"], *nb]):
    ax[1].text(i, v + 1, f"{v:.1f}", ha="center", fontsize=7)
ax[1].set_ylim(0, 110)
# (c) rasio LAI 0N/140N
lab_x, o_, s_, e_ = [], [], [], []
for sk, keys in (("S2022", ["rLAI21", "rLAI35", "rLAI60"]), ("S2020", ["rLAI21", "rLAI35", "rLAIFL"])):
    for k in keys:
        lab_x.append(f"{sk[1:]}\n{k[4:]}"); o_.append(V[sk]["obs"][k]); s_.append(V[sk]["std"]["B"][k]); e_.append(V[sk]["ext"]["B"][k])
x = np.arange(len(lab_x))
ax[2].plot(x, o_, "D", color="C3", label="obs")
ax[2].plot(x, s_, "o", color="C0", label="8.1 standar")
ax[2].plot(x, e_, "s", color="C1", label="8.1 + N-daun (NLEAF)")
ax[2].set_xticks(x); ax[2].set_xticklabels(lab_x, fontsize=6.5); ax[2].set_ylim(0, 1.1)
ax[2].set_ylabel("LAI tanpa N / LAI 140 N"); ax[2].legend(fontsize=7); ax[2].set_title("(c) Respons luas daun (HST; FL = berbunga)", fontsize=8)
for a in ax:
    a.grid(alpha=.3)
fig.suptitle("Validasi independen modul N: LTFE KP Sukamandi, Inpari-33, petak tanpa N vs 140 kg N/ha", fontsize=8.5)
fig.tight_layout(); fig.savefig(f"{L}/validasi_ltfe_sukamandi.png")

# ---- RMSE rasio LAI
def rmse(a, b):
    return float(np.sqrt(np.mean((np.array(a) - np.array(b)) ** 2)))
V["rmse_rasio_LAI"] = {"std": rmse(s_, o_), "ext": rmse(e_, o_)}
print("RMSE rasio LAI std", round(V["rmse_rasio_LAI"]["std"], 3), "ext", round(V["rmse_rasio_LAI"]["ext"], 3))

# ---- ulang transfer Agustiani dengan penggenangan
res2 = json.load(open(f"{L}/hasil_kalibrasi_n5_inpari32.json"))
p = res2["final"]["std"]
out = []
for site in ("subang", "indramayu", "bandung"):
    pj = SimulationConfig.load(f"{R}/data/projects/agustiani2018_{site}_inpari32.json")
    ob = pd.read_csv(f"{L}/obs_{site}_2016_inpari32.csv").TWSO.dropna().iloc[-1]
    w = build_weather_provider(pj.weather)
    res_site = {}
    for lab, nsb, dose, rec in (("126N_INS_Sukamandi", p["NSOILBASE"], 126, p["N_recovery"]), ("N_jenuh", 100, 600, 1.0)):
        c = SimulationConfig.from_dict(pj.to_dict()); c.model_name = "Wofost81_NWLP_CWB_CNB"
        c.site.update(NAVAILI=0.0, NSOILBASE=nsb, NSOILBASE_FR=0.01, BG_N_SUPPLY=0.0)
        c.crop_overrides.update({"NMAXSO": 0.0144, "RGRLAI_MIN_FR": 0.5})
        c.fertilization = [FertilizerEvent(c.crop_start_date + dt.timedelta(days=d), dose / 3, rec) for d in (7, 24, 42)]
        c.irrigation = [IrrigationEvent(c.crop_start_date + dt.timedelta(days=d), 2.0, 1.0) for d in range(0, 131, 2)]
        r = SimulationRunner(c, w).run()
        res_site[lab] = round(r.summary["TWSO"]); res_site[lab + "_RFTRAmin"] = round(float(r.daily.RFTRA.min()), 2)
    out.append(dict(lokasi=site, TWSO_obs=round(ob), **res_site, err_126N_pct=round(100 * (res_site["126N_INS_Sukamandi"] / ob - 1), 1),
                    err_jenuh_pct=round(100 * (res_site["N_jenuh"] / ob - 1), 1)))
T = pd.DataFrame(out); print(T.to_string(index=False))
V["transfer_agustiani_tergenang"] = T.to_dict("records")
json.dump(V, open(f"{L}/validasi_ltfe_sukamandi.json", "w"), indent=1, default=float)
print("ok")
