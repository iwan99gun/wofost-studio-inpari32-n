"""Figur naskah: semua simulasi dijalankan lewat inti WOFOST Studio (wofost_app.core) dan diekspor dengan
fungsi ekspor jurnal aplikasi (save_figure_journal: Arial 8 pt, lebar Elsevier 90/140/190 mm, TIFF-LZW 600 dpi)
serta PNG 300 dpi untuk disisipkan ke DOCX. Jalankan: python naskah/buat_gambar.py"""
import sys, json, datetime as dt
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import wofost_app  # noqa
from wofost_app.core.config import SimulationConfig, FertilizerEvent
from wofost_app.core.weather import build_weather_provider
from wofost_app.core.simulation import SimulationRunner, crop_provider_for, get_model_class
from wofost_app.ui.widgets import save_figure_journal

L = ROOT / "data" / "lapangan"; PJ = ROOT / "data" / "projects"
OUT = ROOT / "naskah" / "gambar"; OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family": "Arial", "font.size": 8, "axes.linewidth": 0.6, "lines.linewidth": 1.0})
C_STD, C_EXT, C_OBS = "#1f77b4", "#e6862b", "#c0392b"
W = {}


def wdp(cfg):
    k = (cfg.weather.source, cfg.weather.latitude, cfg.weather.longitude)
    if k not in W:
        W[k] = build_weather_provider(cfg.weather)
    return W[k]


def save(fig, name, w_mm, h_mm, fs=8.0):
    save_figure_journal(fig, str(OUT / f"{name}.tif"), width_mm=w_mm, height_mm=h_mm, dpi=600, fmt="tiff", fontsize=fs)
    save_figure_journal(fig, str(OUT / f"{name}.png"), width_mm=w_mm, height_mm=h_mm, dpi=300, fmt="png", fontsize=fs)
    plt.close(fig)
    print("  tersimpan", name)


def panel_label(ax, s):
    ax.text(-0.16, 1.04, s, transform=ax.transAxes, fontweight="bold", fontsize=9, va="bottom")


# ---------------------------------------------------------------- Fig. 1 alur kerja
def fig1():
    fig, ax = plt.subplots(figsize=(7.48, 3.6)); ax.set_axis_off(); ax.set_xlim(0, 100); ax.set_ylim(0, 50)
    def box(x, y, w, h, t, fc):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc=fc, ec="0.35", lw=0.6))
        ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=6.6, wrap=True)
    def arr(x1, y1, x2, y2):
        ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", lw=0.7, color="0.3"))
    ax.text(12, 48, "Literature-mined data", ha="center", fontsize=7.5, fontweight="bold")
    ax.text(50, 48, "Model development (WOFOST Studio / PCSE 6.0.13)", ha="center", fontsize=7.5, fontweight="bold")
    ax.text(88, 48, "Evaluation", ha="center", fontsize=7.5, fontweight="bold")
    box(1, 34, 22, 10, "Agustiani et al. (2018)\n3 sites, DS 2016, Inpari-32\nLAI, biomass, yield (digitised)", "#eaf2fb")
    box(1, 20, 22, 10, "Sujinah et al. (2020)\nSukamandi WS 2017/18\n23 / 115 / 207 kg N ha$^{-1}$", "#eaf2fb")
    box(1, 6, 22, 10, "LTFE Sukamandi\nDS 2022, 2020 (Inpari-33)\n0-N vs 140 kg N ha$^{-1}$", "#fdf0e3")
    box(29, 34, 42, 10, "Step 1: potential production (WOFOST 7.2)\nphenology, SLA (literature-bounded), AMAX, SPAN,\nTDWI, RGRLAI + ORYZA-type transplanting shock", "#eef7ee")
    box(29, 20, 42, 10, "Step 2: N-limited production (WOFOST 8.1)\ncode fixes: RGRLAI_MIN ratio, AMAX_REF <- AMAXTB\nN supply (NSOILBASE, recovery) + leaf-N extension NLEAF", "#eef7ee")
    box(29, 6, 42, 10, "Uncertainty\nMCMC (emcee), Sobol (SALib), weather source\n(Open-Meteo vs NASA POWER), variety & date assumptions", "#eef7ee")
    box(77, 27, 22, 14, "Internal: leave-one-dose-out\ncross-validation (LODO)\nAICc model comparison", "#f4eefb")
    box(77, 8, 22, 14, "Independent: blind prediction\nof LTFE omission plots\n(no re-calibration)", "#fdf0e3")
    arr(23, 39, 29, 39); arr(23, 25, 29, 25); arr(50, 34, 50, 30); arr(50, 20, 50, 16)
    arr(71, 25, 77, 33); arr(71, 22, 77, 15)
    ax.plot([12, 12, 88], [5.5, 2.0, 2.0], color="0.3", lw=0.7); arr(88, 2.0, 88, 7.6)
    save(fig, "Fig1_workflow", 190, 95, fs=6.2)


# ---------------------------------------------------------------- Fig. 2 kalibrasi potensial
def fig2():
    obs = pd.read_csv(L / "agustiani2018_hy_inpari32_long.csv", parse_dates=["day"])
    sites = [("subang", "Subang"), ("indramayu", "Indramayu"), ("bandung", "Bandung")]
    vars_ = [("LAI", "LAI (m$^2$ m$^{-2}$)", 1), ("TAGP", "AGB (t ha$^{-1}$)", 1e-3), ("TWSO", "Grain (t ha$^{-1}$)", 1e-3)]
    fig, axs = plt.subplots(3, 3, figsize=(7.48, 5.6), sharex="col")
    for j, (key, lab) in enumerate(sites):
        cfg = SimulationConfig.load(PJ / f"agustiani2018_{key}_inpari32.json")
        r = SimulationRunner(cfg, wdp(cfg)).run(); d = r.daily
        dat = (d.index - pd.Timestamp(cfg.crop_start_date)).days
        for i, (v, yl, sc) in enumerate(vars_):
            ax = axs[i, j]
            ax.plot(dat, d[v] * sc, color=C_STD, label="WOFOST 7.2 (calibrated)")
            o = obs[(obs.lokasi == lab) & (obs.variable == v)]
            ax.errorbar(o.DAT, o.value * sc, yerr=o.ketidakpastian * sc, fmt="o", ms=3.5, color=C_OBS, capsize=2, lw=0.7, label="Observed")
            if i == 0:
                ax.set_title(lab)
            if j == 0:
                ax.set_ylabel(yl)
            if i == 2:
                ax.set_xlabel("Days after transplanting")
            ax.grid(alpha=.25)
    axs[0, 0].legend(fontsize=6.5, loc="upper left", frameon=False)
    for k, ax in enumerate(axs.flat):
        panel_label(ax, "abcdefghi"[k])
    fig.tight_layout()
    save(fig, "Fig2_potential_calibration", 190, 142)


# ---------------------------------------------------------------- helper Sukamandi per dosis
def suka(dose, ext=False):
    return SimulationConfig.load(PJ / f"sujinah2020_sukamandi_mh2017_inpari32_N{dose}{'_nlv' if ext else ''}.json")


def with_dose(cfg, dose):
    c = SimulationConfig.from_dict(cfg.to_dict()); rec = c.fertilization[0].recovery
    c.fertilization = [FertilizerEvent(c.crop_start_date + dt.timedelta(days=d), dose / 3, rec) for d in (7, 28, 42)] if dose > 0 else []
    return c


# ---------------------------------------------------------------- Fig. 3 respons N
def fig3():
    doses = [0, 23, 60, 115, 160, 207, 260]
    S = {}
    for lab, ext in (("std", False), ("ext", True)):
        base = suka(115, ext); S[lab] = {}
        for dz in doses:
            r = SimulationRunner(with_dose(base, dz), wdp(base)).run()
            fl = base.crop_start_date + dt.timedelta(days=67)
            S[lab][dz] = dict(TWSO=r.summary["TWSO"], TAGP=r.summary["TAGP"], LAIFL=float(r.daily.loc[str(fl), "LAI"]))
    OBS = {23: dict(TWSO=5410 * .86, TAGP=10065.3), 115: dict(TWSO=6920 * .86, TAGP=15538.9), 207: dict(TWSO=7610 * .86, TAGP=15468.0)}
    RL = {23: 2327 / 3617, 115: 1.0, 207: 4039 / 3617}
    fig, ax = plt.subplots(1, 3, figsize=(7.48, 2.6))
    for i, (v, yl, cv) in enumerate([("TWSO", "Grain yield (t ha$^{-1}$)", .0875), ("TAGP", "AGB at maturity (t ha$^{-1}$)", .168)]):
        ax[i].plot(doses, [S["std"][d][v] / 1e3 for d in doses], "-o", ms=3, color=C_STD, label="WOFOST 8.1")
        ax[i].plot(doses, [S["ext"][d][v] / 1e3 for d in doses], "--s", ms=3, color=C_EXT, label="WOFOST 8.1 + NLEAF")
        ax[i].errorbar(list(OBS), [OBS[d][v] / 1e3 for d in OBS], yerr=[OBS[d][v] * cv / 1e3 for d in OBS], fmt="D", ms=4, color=C_OBS, capsize=2, label="Observed")
        ax[i].set_ylabel(yl)
    for lab, st, c in (("std", "-o", C_STD), ("ext", "--s", C_EXT)):
        ax[2].plot(doses, [S[lab][d]["LAIFL"] / S[lab][115]["LAIFL"] for d in doses], st, ms=3, color=c)
    ax[2].errorbar(list(RL), list(RL.values()), yerr=[0 if d == 115 else 2 ** .5 * .156 for d in RL], fmt="D", ms=4, color=C_OBS, capsize=2)
    ax[2].set_ylabel("LAI at flowering / LAI at 115 N")
    for k, a in enumerate(ax):
        a.set_xlabel("N rate (kg N ha$^{-1}$)"); a.grid(alpha=.25); panel_label(a, "abc"[k])
    ax[0].legend(fontsize=6.5, frameon=False, loc="lower right")
    fig.tight_layout(); save(fig, "Fig3_N_response", 190, 66)


# ---------------------------------------------------------------- Fig. 4 mekanisme: NNI & LAI
def nni_series(r, prov):
    from pcse.util import Afgen
    nm = Afgen(prov["NMAXLV_TB"]); d = r.daily; out = []
    for _, row in d.iterrows():
        vbm = row.WLV + row.WST
        if vbm <= 0:
            out.append(np.nan); continue
        m = float(nm(row.DVS))
        crit = (prov["NCRIT_FR"] * m * row.WLV + prov["NCRIT_FR"] * prov["NMAXST_FR"] * m * row.WST) / vbm
        res = (prov["NRESIDLV"] * row.WLV + prov["NRESIDST"] * row.WST) / vbm
        out.append(min(1, max(0.001, ((row.NamountLV + row.NamountST) / vbm - res) / (crit - res))))
    return np.array(out)


def fig4():
    prov = crop_provider_for(get_model_class("Wofost81_NWLP_CWB_CNB")); prov.set_active_crop("rice", "Rice_IR72")
    fig, ax = plt.subplots(1, 3, figsize=(7.48, 2.5))
    cols = {23: "#8e44ad", 115: "#16a085", 207: "#2c3e50"}
    for dz in (23, 115, 207):
        for ext, ls in ((False, "-"), (True, "--")):
            c = suka(dz, ext); r = SimulationRunner(c, wdp(c)).run(); d = r.daily
            dat = (d.index - pd.Timestamp(c.crop_start_date)).days
            if not ext:
                ax[0].plot(dat, nni_series(r, prov), ls, color=cols[dz], label=f"{dz} kg N ha$^{{-1}}$")
            ax[1 if not ext else 2].plot(dat, d.LAI, ls, color=cols[dz], label=f"{dz} N")
    ax[0].axvspan(0, 21, color="0.9", lw=0); ax[0].text(10, 0.52, "juvenile\nwindow", ha="center", fontsize=6)
    ax[0].set_ylabel("Nitrogen nutrition index"); ax[0].set_ylim(0.4, 1.03); ax[0].legend(fontsize=6.3, frameon=False)
    ax[1].set_title("WOFOST 8.1", fontsize=8); ax[2].set_title("WOFOST 8.1 + NLEAF", fontsize=8)
    for a in ax[1:]:
        a.set_ylabel("LAI (m$^2$ m$^{-2}$)"); a.set_ylim(0, 5.6)
    for k, a in enumerate(ax):
        a.set_xlabel("Days after transplanting"); a.set_xlim(0, 105); a.grid(alpha=.25); panel_label(a, "abc"[k])
    fig.tight_layout(); save(fig, "Fig4_NNI_LAI_mechanism", 190, 64)


# ---------------------------------------------------------------- Fig. 5 validasi independen LTFE
def fig5():
    V = json.load(open(L / "validasi_ltfe_sukamandi.json")); P = json.load(open(L / "posterior_bertahap_n_inpari32.json"))
    fin = json.load(open(L / "hasil_kalibrasi_n5_inpari32.json"))["final"]
    fig, ax = plt.subplots(1, 3, figsize=(7.48, 2.7), gridspec_kw={"width_ratios": [1, 0.8, 1.6]})
    for sk, lab, mk in (("S2022", "LTFE DS 2022", "o"), ("S2020", "LTFE 2020", "s")):
        o = V[sk]["obs"]["Y0"] / 1e3
        for m, c in (("std", C_STD), ("ext", C_EXT)):
            b = P[m]["prediksi_ltfe"][sk]["Y0"]
            ax[0].errorbar(o, b["median"] / 1e3, yerr=[[(b["median"] - b["q2_5"]) / 1e3], [(b["q97_5"] - b["median"]) / 1e3]],
                           fmt=mk, color=c, ms=4, capsize=2, lw=0.7, label=f"{lab}, {'8.1' if m == 'std' else '8.1+NLEAF'}")
    ax[0].plot([2, 4.2], [2, 4.2], "k--", lw=0.6); ax[0].set_xlim(2, 4.2); ax[0].set_ylim(2, 4.2)
    ax[0].set_xlabel("Observed 0-N yield (t ha$^{-1}$)"); ax[0].set_ylabel("Blind prediction (t ha$^{-1}$)"); ax[0].legend(fontsize=5.6, loc="upper left", frameon=True, framealpha=1.0, edgecolor="none", borderpad=0.4, handletextpad=0.5)
    vals = [fin["std"]["NSOILBASE"], V["S2022"]["std"]["NSOILBASE_B"], V["S2020"]["std"]["NSOILBASE_B"]]
    ax[1].bar(["Calib.\nWS17/18", "Omis.\nDS2022", "Omis.\n2020"], vals, color=["0.6", C_STD, C_EXT], width=0.6)
    lo, hi = P["std"]["posterior"]["NSOILBASE"]["q2_5"], P["std"]["posterior"]["NSOILBASE"]["q97_5"]
    ax[1].errorbar([0], [vals[0]], yerr=[[vals[0] - lo], [hi - vals[0]]], fmt="none", color="k", capsize=3, lw=0.7)
    for i, v in enumerate(vals):
        ax[1].text(i, v + 2, f"{v:.1f}", ha="center", fontsize=6.5)
    ax[1].set_ylabel("NSOILBASE (kg N ha$^{-1}$)"); ax[1].set_ylim(0, 115); ax[1].tick_params(axis="x", labelsize=6)
    labs, x = [], 0
    for sk, keys in (("S2022", ["rLAI21", "rLAI35", "rLAI60"]), ("S2020", ["rLAI21", "rLAI35", "rLAIFL"])):
        for k in keys:
            ob = V[sk]["obs"][k]
            ax[2].plot(x, ob, "D", color=C_OBS, ms=4, label="Observed" if x == 0 else None)
            for m, c, dx, mk in (("std", C_STD, -0.15, "o"), ("ext", C_EXT, 0.15, "s")):
                b = P[m]["prediksi_ltfe"][sk][k]
                ax[2].errorbar(x + dx, b["median"], yerr=[[b["median"] - b["q2_5"]], [b["q97_5"] - b["median"]]], fmt=mk, color=c, ms=3.5,
                               capsize=2, lw=0.7, label=({"std": "WOFOST 8.1", "ext": "WOFOST 8.1 + NLEAF"}[m] if x == 0 else None))
            labs.append(f"{'2022' if sk == 'S2022' else '2020'}\n{k[4:].replace('FL', 'flow.')}{'' if k.endswith('FL') else ' DAT'}")
            x += 1
    ax[2].set_xticks(range(len(labs))); ax[2].set_xticklabels(labs, fontsize=6); ax[2].set_ylim(0, 1.1)
    ax[2].set_ylabel("LAI$_{0N}$ / LAI$_{140N}$"); ax[2].legend(fontsize=6, frameon=False, loc="lower left")
    for k, a in enumerate(ax):
        a.grid(alpha=.25); panel_label(a, "abc"[k])
    fig.tight_layout(); save(fig, "Fig5_independent_validation", 190, 76, fs=7)


# ---------------------------------------------------------------- Fig. 6 Sobol
def fig6():
    S = json.load(open(L / "sobol_model_final_n.json"))["hasil"]
    fig, ax = plt.subplots(1, 2, figsize=(7.48, 2.9), sharey=True)
    params = [r["index"] if "index" in r else list(r.values())[0] for r in S["N23_TWSO"]]
    key = "index" if "index" in S["N23_TWSO"][0] else list(S["N23_TWSO"][0].keys())[0]
    order = [r[key] for r in sorted(S["N23_LAIMAX"], key=lambda r: -r["ST"])]
    y = np.arange(len(order))
    for k, (tgt, lab) in enumerate((("TWSO", "Grain yield"), ("LAIMAX", "Maximum LAI"))):
        for off, dz, c in ((-0.2, 23, "#8e44ad"), (0.2, 207, "#2c3e50")):
            tab = {r[key]: r for r in S[f"N{dz}_{tgt}"]}
            ax[k].barh(y + off, [max(tab[p]["ST"], 0) for p in order], height=0.38, color=c, xerr=[tab[p]["ST_conf"] for p in order],
                       error_kw=dict(lw=0.5, capsize=1.5), label=f"{dz} kg N ha$^{{-1}}$")
        ax[k].set_title(lab, fontsize=8); ax[k].set_xlabel("Total-order Sobol index (S$_T$)"); ax[k].grid(alpha=.25, axis="x")
        panel_label(ax[k], "ab"[k])
    ax[0].set_yticks(y); ax[0].set_yticklabels(order, fontsize=6.5); ax[0].invert_yaxis(); ax[1].legend(fontsize=6.5, frameon=False, loc="lower right")
    fig.tight_layout(); save(fig, "Fig6_Sobol", 190, 76)


# ---------------------------------------------------------------- Fig. S1 cuaca, S2 varietas
def figS1():
    D = json.load(open(L / "sensitivitas_sumber_cuaca.json"))
    st = pd.DataFrame(D["statistik"])
    fig, ax = plt.subplots(1, 3, figsize=(7.48, 2.6))
    x = np.arange(len(st)); lab = [{"Sujinah MH17/18": "Suk. WS17", "LTFE MK2022": "LTFE22", "LTFE 2020": "LTFE20", "Agustiani Subang": "Subang", "Agustiani Indramayu": "Indram.", "Agustiani Bandung": "Bandung"}[p] for p in st.periode]
    for k, (v, yl) in enumerate((("TMAX", "Mean T$_{max}$ (°C)"), ("IRRAD_MJ", "Radiation (MJ m$^{-2}$ d$^{-1}$)"))):
        ax[k].bar(x - 0.2, st[f"OM_{v}"], 0.4, label="Open-Meteo (ERA5)", color="#5d6d7e")
        ax[k].bar(x + 0.2, st[f"NP_{v}"], 0.4, label="NASA POWER", color="#f5b041")
        ax[k].set_xticks(x); ax[k].set_xticklabels(lab, rotation=40, ha="right"); ax[k].set_ylabel(yl)
        ax[k].set_ylim(st[[f"OM_{v}", f"NP_{v}"]].values.min() * 0.85, st[[f"OM_{v}", f"NP_{v}"]].values.max() * 1.05)
    ax[0].legend(fontsize=6, frameon=False)
    lt = pd.DataFrame(D["ltfe"]); sj = pd.DataFrame(D["sujinah"])
    rows = [(f"Suj. {r.dosis} N", r.cuaca, 100 * (r.TWSO_sim / r.TWSO_obs - 1)) for r in sj.itertuples()]
    rows += [(f"LTFE {r.musim[1:]} 0N", r.cuaca, r.err_Y0_pct) for r in lt.itertuples()]
    Rw = pd.DataFrame(rows, columns=["case", "src", "err"])
    cases = list(dict.fromkeys(Rw.case)); xx = np.arange(len(cases))
    for off, src, c in ((-0.2, "openmeteo", "#5d6d7e"), (0.2, "nasapower", "#f5b041")):
        ax[2].bar(xx + off, [Rw[(Rw.case == cs) & (Rw.src == src)].err.values[0] for cs in cases], 0.4, color=c)
    ax[2].axhline(0, color="k", lw=0.5); ax[2].set_xticks(xx); ax[2].set_xticklabels(cases, fontsize=5.5, rotation=30, ha="right")
    ax[2].set_ylabel("Yield error (%)")
    for k, a in enumerate(ax):
        a.grid(alpha=.25, axis="y"); panel_label(a, "abc"[k])
    fig.tight_layout(); save(fig, "FigS1_weather_source", 190, 76, fs=7)


def figS2():
    D = json.load(open(L / "sensitivitas_asumsi_varietas.json"))
    T = pd.DataFrame(D["varietas"])
    fig, ax = plt.subplots(1, 2, figsize=(7.48, 2.8), sharey=True)
    vars_ = list(dict.fromkeys(T.varian)); y = np.arange(len(vars_))
    en = {"dasar (skala fenologi Inpari-33)": "baseline (Inpari-33 phenology)", "fenologi Inpari-32 (tanpa skala)": "Inpari-32 phenology",
          "fenologi -10 %": "phenology -10%", "fenologi +10 %": "phenology +10%", "AMAX x0.9": "AMAX x0.9", "AMAX x1.1": "AMAX x1.1",
          "SLA x0.9": "SLA x0.9", "SLA x1.1": "SLA x1.1"}
    for m, c, off in (("std", C_STD, -0.2), ("ext", C_EXT, 0.2)):
        for sk, mk in (("S2022", "o"), ("S2020", "s")):
            t = T[(T.model == m) & (T.musim == sk)].set_index("varian").loc[vars_]
            ax[0].plot(t.err_Y0_pct, y + off, mk, color=c, ms=3.5, mfc=c if sk == "S2022" else "white",
                       label=f"{'8.1' if m == 'std' else '8.1+NLEAF'}, {sk[1:]}")
            ax[1].plot(t.rmse_rLAI, y + off, mk, color=c, ms=3.5, mfc=c if sk == "S2022" else "white")
    ax[0].axvline(0, color="k", lw=0.5); ax[0].set_xlabel("0-N yield error (%)"); ax[1].set_xlabel("RMSE of LAI ratio")
    ax[0].set_yticks(y); ax[0].set_yticklabels([en[v] for v in vars_], fontsize=6.5); ax[0].invert_yaxis(); ax[0].legend(fontsize=6, frameon=False)
    for k, a in enumerate(ax):
        a.grid(alpha=.25); panel_label(a, "ab"[k])
    fig.tight_layout(); save(fig, "FigS2_variety_assumption", 190, 72)


if __name__ == "__main__":
    sel = sys.argv[1:]
    for f in (fig1, fig2, fig3, fig4, fig5, fig6, figS1, figS2):
        if sel and f.__name__ not in sel:
            continue
        print(f.__name__, flush=True); f()
    print("selesai")
