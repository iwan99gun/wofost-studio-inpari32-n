"""Poin 5: apakah kesimpulan bergantung pada model observasi rasio (sigma = sqrt(2) x CV, data rata-rata 6 genotipe)?
Varian: sigma rasio x0,5 ; x1 (dasar) ; x2 ; tanpa data rasio (hanya 6 observasi absolut Inpari-32).
Untuk tiap varian: kalibrasi kuadrat terkecil (std: NSOILBASE, N_recovery; ext: + NLEAF), lalu prediksi buta LTFE."""
import sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[1]))
import numpy as np
from scipy import optimize
import mcmc_bersama as M

L = HERE.parents[1] / "data" / "lapangan"
FIX = {"SPAN": 36.64537, "AMAXTB@y": 0.90186}
NAMES = {"std": ["NSOILBASE", "N_recovery"], "ext": ["NSOILBASE", "N_recovery", "NLEAF"]}
B = {"NSOILBASE": (10, 300), "N_recovery": (0.2, 0.8), "NLEAF": (0.0, 4.0)}


def resid(x, key, mult):
    p = {**FIX, **dict(zip(NAMES[key], map(float, x)))}
    S = {d: M.sim2(key, p, d) for d in (23, 115, 207)}
    r = [(S[d][v] - M.ABS[d][v]) / (M.CV_ABS[v] * M.ABS[d][v]) for d in (23, 115, 207) for v in ("TAGP", "TWSO")]
    if mult is not None:
        r += [(S[d][k] / S[115][k] - M.RATIO[k][d]) / (M.SIG[k] * mult) for d in (23, 207) for k in M.MAIN]
    return np.array(r)


def main():
    M._init()
    V = json.load(open(L / "validasi_ltfe_sukamandi.json"))
    fin = json.load(open(L / "hasil_kalibrasi_n5_inpari32.json"))["final"]
    rows = []
    for lab, mult in (("sigma x0.5", 0.5), ("dasar (sigma x1)", 1.0), ("sigma x2", 2.0), ("tanpa data rasio", None)):
        for key in ("std", "ext"):
            names = NAMES[key]; x0 = [fin[key][n] for n in names]
            sol = optimize.least_squares(resid, x0, args=(key, mult), bounds=([B[n][0] for n in names], [B[n][1] for n in names]),
                                         diff_step=0.05, max_nfev=60)
            p = {**FIX, **dict(zip(names, map(float, sol.x)))}
            pr = M.ltfe_pred(key, p)
            e0 = [100 * (pr[s]["Y0"] / V[s]["obs"]["Y0"] - 1) for s in ("S2022", "S2020")]
            rl = [(pr[s][k] - V[s]["obs"][k]) ** 2 for s in ("S2022", "S2020") for k in V[s]["obs"] if k.startswith("rLAI")]
            J = sol.jac; se = np.sqrt(np.diag(np.linalg.pinv(J.T @ J) * max(float(np.sum(sol.fun ** 2)) / max(len(sol.fun) - len(names), 1), 1.0)))
            row = dict(varian=lab, model=key, **{n: round(float(v), 3) for n, v in zip(names, sol.x)},
                       **{f"SE_{n}": round(float(s_), 3) for n, s_ in zip(names, se)},
                       err_Y0_2022=round(e0[0], 1), err_Y0_2020=round(e0[1], 1), rmse_rasio_LAI=round(float(np.sqrt(np.mean(rl))), 3))
            rows.append(row); print(row, flush=True)
    json.dump(rows, open(L / "ketahanan_model_observasi.json", "w"), indent=1)
    print("tersimpan")


if __name__ == "__main__":
    main()
