"""Poin 2 reviewer: apakah kesimpulan validasi LTFE (Inpari-33) bergantung pada asumsi varietas?
Variasi: fenologi (tanpa skala = fenologi Inpari-32; skala +/-10 %), potensi fotosintesis AMAXTB x0.9/x1.1,
SLA x0.9/x1.1. Prediksi buta (parameter N final, tanpa refit) untuk std dan ekstensi.
Poin 5a: diagnosis NNI awal musim Sujinah 23 vs 207 N (mengapa LAI 21-35 HST tidak merespons N)."""
import sys, json, datetime as dt
sys.path.insert(0, r"D:\riset_tani_1")
import numpy as np, pandas as pd
import wofost_app  # noqa
from wofost_app.core.config import SimulationConfig
from wofost_app.core.simulation import SimulationRunner, crop_provider_for, get_model_class

R = r"D:\riset_tani_1"; L = f"{R}/data/lapangan"
SP = str(__import__("pathlib").Path(__file__).parent)
ns = {}
exec(open(f"{SP}/validasi_ltfe.py", encoding="utf-8").read().split("res = {}")[0], ns)
V = json.load(open(f"{L}/validasi_ltfe_sukamandi.json"))
FIT = {sk: V[sk]["std"]["f_tsum"] for sk in ("S2022", "S2020")}
VARIANTS = [("dasar (skala fenologi Inpari-33)", 1.0, {}), ("fenologi Inpari-32 (tanpa skala)", None, {}),
            ("fenologi -10 %", 0.9, {}), ("fenologi +10 %", 1.1, {}),
            ("AMAX x0.9", 1.0, {"AMAXTB@y": 0.9}), ("AMAX x1.1", 1.0, {"AMAXTB@y": 1.1}),
            ("SLA x0.9", 1.0, {"SLATB@y": 0.9}), ("SLA x1.1", 1.0, {"SLATB@y": 1.1})]
rows = []
orig_make = ns["make"]
for key in ("std", "ext"):
    for lab, fmul, extra in VARIANTS:
        def make(mk, tp, seed, dose, f, nsoil=None, pi_day=35, _extra=extra):
            c = orig_make(mk, tp, seed, dose, f, nsoil, pi_day)
            for k, v in _extra.items():
                c.crop_overrides[k] = c.crop_overrides.get(k, 1.0) * v
            return c
        ns["make"] = make
        for sk, S in ns["SEASONS"].items():
            f = 1.0 if fmul is None else FIT[sk] * fmul
            A = ns["predict"](key, S, S["tp"], f)
            ob = V[sk]["obs"]
            rl = [k for k in ob if k.startswith("rLAI")]
            rows.append(dict(model=key, varian=lab, musim=sk, DOM_HST=A["DOM_HST"], err_Y0_pct=round(100 * (A["Y0"] / ob["Y0"] - 1), 1),
                             err_Y140_pct=round(100 * (A["Y140"] / ob["Y140"] - 1), 1), rY=round(A["rY"], 3), rY_obs=round(ob["rY"], 3),
                             rmse_rLAI=round(float(np.sqrt(np.mean([(A[k] - ob[k]) ** 2 for k in rl]))), 3)))
        print(pd.DataFrame(rows[-2:]).to_string(index=False, header=len(rows) <= 2), flush=True)
ns["make"] = orig_make
T = pd.DataFrame(rows)
summ = T.groupby(["model", "musim"]).agg(err_Y0_min=("err_Y0_pct", "min"), err_Y0_max=("err_Y0_pct", "max"),
                                         rmse_rLAI_min=("rmse_rLAI", "min"), rmse_rLAI_max=("rmse_rLAI", "max"))
print("\nRingkasan rentang:\n", summ.to_string(), flush=True)

# ---- 5a: NNI awal Sujinah
prov = crop_provider_for(get_model_class("Wofost81_NWLP_CWB_CNB")); prov.set_active_crop("rice", "Rice_IR72")
from pcse.util import Afgen
nmaxlv = Afgen(prov["NMAXLV_TB"])
diag = []
for d in (23, 207):
    c = SimulationConfig.load(f"{R}/data/projects/sujinah2020_sukamandi_mh2017_inpari32_N{d}.json")
    r = SimulationRunner(c, ns["wdp"]).run(); x = r.daily
    for h in (7, 14, 21, 28, 35, 42, 56):
        row = x.loc[str(c.crop_start_date + dt.timedelta(days=h))]
        vbm = row.WLV + row.WST; nm = float(nmaxlv(row.DVS))
        ncrit = (prov["NCRIT_FR"] * nm * row.WLV + prov["NCRIT_FR"] * prov["NMAXST_FR"] * nm * row.WST) / vbm
        nres = (prov["NRESIDLV"] * row.WLV + prov["NRESIDST"] * row.WST) / vbm
        nni = min(1.0, max(0.001, ((row.NamountLV + row.NamountST) / vbm - nres) / (ncrit - nres)))
        diag.append(dict(dosis=d, HST=h, NNI=round(nni, 3), NAVAIL=round(row.NAVAIL, 1), LAI=round(row.LAI, 2), Nuptake=round(row.NuptakeTotal, 1)))
D = pd.DataFrame(diag); print("\nNNI awal (Sujinah, 8.1 standar):\n", D.pivot(index="HST", columns="dosis", values=["NNI", "NAVAIL", "LAI"]).to_string(), flush=True)
json.dump({"varietas": rows, "ringkasan": summ.reset_index().to_dict("records"), "nni_awal": diag},
          open(f"{L}/sensitivitas_asumsi_varietas.json", "w"), indent=1)
print("tersimpan")
