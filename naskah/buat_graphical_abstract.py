"""Graphical abstract untuk European Journal of Agronomy (wajib saat submit).
Ukuran: 6.6 x 2.64 in (rasio 2.5:1; minimum Elsevier 1328 x 531 px) pada 400 dpi -> 2640 x 1056 px, TIFF + PNG.
Semua angka dibaca dari JSON hasil (sumber tunggal, sama dengan naskah).
Jalankan: python naskah/buat_graphical_abstract.py"""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
L = ROOT / "data" / "lapangan"
OUT = Path(__file__).resolve().parent / "gambar"
plt.rcParams.update({"font.family": "Arial", "font.size": 8.5, "axes.linewidth": 0.7})
C_STD, C_EXT, C_OBS = "#1f77b4", "#e6862b", "#c0392b"      # sama dengan Fig. 3-5 naskah
INK, MUTED = "#222222", "#666666"

V = json.load(open(L / "validasi_ltfe_sukamandi.json"))
MEK = json.load(open(L / "mekanisme_n_daun.json"))
MAR = json.load(open(L / "validasi_marpaung_karangploso.json"))
POST = json.load(open(L / "posterior_bertahap_n_inpari32.json"))
FIN = json.load(open(L / "hasil_kalibrasi_n5_inpari32.json"))["final"]

# ---- panel A: strategi kanopi, 0-N / N-tinggi (rata-rata LTFE)
S = [r for r in MEK["strategi_N"] if r["model"] == "std"]
obs_lai = np.mean([r["obs_rasio_LAI"] for r in S])
obs_spad = np.mean([r["obs_rasio_SPAD"] for r in S if r["obs_rasio_SPAD"] is not None])
std_lai = np.mean([r["sim_rasio_LAI"] for r in S])
std_sln = np.mean([r["sim_rasio_SLN"] for r in S])

# ---- panel B: prediksi buta rasio LAI (3 dataset, 2 lokasi, 2 varietas)
o22, o20 = V["S2022"]["obs"], V["S2020"]["obs"]
sets = [("LTFE\n2022\nInpari-33", o22["rLAI60"], V["S2022"]["std"]["A"]["rLAI60"], V["S2022"]["ext"]["A"]["rLAI60"]),
        ("LTFE\n2020\nInpari-33", o20["rLAIFL"], V["S2020"]["std"]["A"]["rLAIFL"], V["S2020"]["ext"]["A"]["rLAIFL"]),
        ("Karangploso\n2023\nInpari-32", MAR["observasi"]["rLAI"]["56"], MAR["std"]["rLAI"]["56"], MAR["ext"]["rLAI"]["56"])]

# ---- angka utama
err0 = max(abs(100 * (V[s]["std"]["A"]["Y0"] / V[s]["obs"]["Y0"] - 1)) for s in ("S2022", "S2020"))
nsb = [V[s]["std"]["NSOILBASE_B"] for s in ("S2022", "S2020")]
nl = POST["ext"]["posterior"]["NLEAF"]

fig = plt.figure(figsize=(6.6, 2.64))
gs = fig.add_gridspec(1, 3, width_ratios=[0.95, 1.55, 0.95], left=0.085, right=0.985, top=0.80, bottom=0.30, wspace=0.52)

# ---------------- A
ax = fig.add_subplot(gs[0])
x = np.arange(2); w = 0.36
ax.bar(x - w / 2, [obs_lai, obs_spad], w, color=C_OBS, label="Observed")
ax.bar(x + w / 2, [std_lai, std_sln], w, color=C_STD, label="WOFOST 8.1")
for xi, v in zip(x - w / 2, [obs_lai, obs_spad]): ax.text(xi, v + 0.02, f"{v:.2f}", ha="center", fontsize=7.2, color=INK)
for xi, v in zip(x + w / 2, [std_lai, std_sln]): ax.text(xi, v + 0.02, f"{v:.2f}", ha="center", fontsize=7.2, color=INK)
ax.axhline(1, color=MUTED, lw=0.7, ls="--")
ax.set_xticks(x); ax.set_xticklabels(["Leaf\narea", "Leaf N\nper area"], fontsize=8)
ax.set_ylim(0, 1.3); ax.set_yticks([0, 0.5, 1.0]); ax.set_ylabel("0-N / high-N ratio", fontsize=8)
ax.set_title("Two opposite canopy strategies", fontsize=8.8, fontweight="bold", color=INK, loc="left", pad=6)

# ---------------- B
ax = fig.add_subplot(gs[1])
xs = np.arange(len(sets)); w = 0.26
for k, (c, lab, col) in enumerate(((1, "Observed", C_OBS), (2, "WOFOST 8.1", C_STD), (3, "8.1 + leaf-N extension", C_EXT))):
    vals = [s[c] for s in sets]
    ax.bar(xs + (k - 1) * w, vals, w, color=col, label=lab)
    for xi, v in zip(xs + (k - 1) * w, vals): ax.text(xi, v + 0.02, f"{v:.2f}", ha="center", fontsize=6.6, color=INK)
ax.axhline(1, color=MUTED, lw=0.7, ls="--")
ax.text(-0.45, 1.115, "1.0 = no response", fontsize=6.6, color=MUTED, ha="left", va="bottom")
ax.set_xticks(xs); ax.set_xticklabels([s[0] for s in sets], fontsize=7.0)
ax.set_ylim(0, 1.3); ax.set_yticks([0, 0.5, 1.0]); ax.set_ylabel("LAI ratio 0-N / high-N", fontsize=8)
ax.set_title("Blind prediction, independent trials", fontsize=8.8, fontweight="bold", color=INK, loc="left", pad=6)

# ---------------- C: key results
ax = fig.add_subplot(gs[2]); ax.set_axis_off(); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax.set_title("Key results", fontsize=8.8, fontweight="bold", color=INK, loc="left", pad=6)
MU = MAR["pembaruan_NLEAF"]["NLEAF_sesudah"]
rows = [(f"≤{err0:.0f}%", "error in blind 0-N yield\n(two omission seasons)"),
        (f"{nsb[0]:.0f}–{nsb[1]:.0f}", f"kg N ha$^{{-1}}$ soil N supply from\nomission plots (calibrated: {FIN['std']['NSOILBASE']:.0f})"),
        (f"{MU[1]:.1f}", f"leaf-N coefficient NLEAF\n(95% interval {MU[0]:.1f}–{MU[2]:.1f}; > 0)")]
for i, (big, small) in enumerate(rows):
    y = 0.90 - i * 0.315
    ax.text(0.0, y, big, fontsize=13, fontweight="bold", color=C_EXT if i == 2 else C_STD, va="center", ha="left")
    ax.text(0.0, y - 0.085, small, fontsize=6.6, color=INK, va="top", ha="left", linespacing=1.15)

# legenda bersama di bawah (tidak menimpa data)
h, l = [], []
for a in fig.axes[:2]:
    for hh, ll in zip(*a.get_legend_handles_labels()):
        if ll not in l: h.append(hh); l.append(ll)
fig.legend(h, l, loc="lower left", bbox_to_anchor=(0.085, 0.0), ncol=3, frameon=False, fontsize=7.6, handlelength=1.1,
           columnspacing=1.6, handletextpad=0.5)
fig.suptitle("N-limited WOFOST 8.1 for tropical rice: enforcing parameter consistency and leaf-area plasticity",
             x=0.085, y=0.985, ha="left", fontsize=9.2, fontweight="bold", color=INK)

OUT.mkdir(exist_ok=True)
fig.savefig(OUT / "Graphical_abstract.png", dpi=400)
fig.savefig(OUT / "Graphical_abstract.tif", dpi=400, pil_kwargs={"compression": "tiff_lzw"})
print("obs LAI", round(obs_lai, 2), "SPAD", round(obs_spad, 2), "| std LAI", round(std_lai, 2), "SLN", round(std_sln, 2))
print("tersimpan gambar/Graphical_abstract.png/.tif")
