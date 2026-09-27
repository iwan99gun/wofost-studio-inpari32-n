"""Menyusun draf naskah (DOCX + PDF) dari hasil WOFOST Studio. Semua angka dibaca dari data/lapangan/*.json.
Jalankan setelah naskah/buat_gambar.py:  python naskah/buat_naskah.py"""
import json, sys, datetime as dt
from pathlib import Path
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
L = ROOT / "data" / "lapangan"; G = ROOT / "naskah" / "gambar"; OUT = ROOT / "naskah"
J = lambda n: json.load(open(L / n, encoding="utf-8"))
POT = J("hasil_kalibrasi_syok_inpari32.json"); N4 = J("hasil_kalibrasi_n5_inpari32.json"); V = J("validasi_ltfe_sukamandi.json")
POST = J("posterior_bertahap_n_inpari32.json"); ROB = J("ketahanan_model_observasi.json"); ORY = J("pembanding_oryza.json"); KP = J("kalibrasi_partisi_pascaberbunga.json"); SOB = J("sobol_model_final_n.json"); WX = J("sensitivitas_sumber_cuaca.json")
VAR = J("sensitivitas_asumsi_varietas.json")
STD, EXT = N4["Wofost81_NWLP_CWB_CNB"], N4["Wofost81_NWLP_CWB_CNB_NLV"]
ps, pe = STD["parameter"], EXT["parameter"]
LODO_S = {r["ditahan"]: r for r in STD["lodo"]}; LODO_E = {r["ditahan"]: r for r in EXT["lodo"]}
cal_err = max(abs(100 * (r["TWSO_sim"] / r["TWSO_obs"] - 1)) for r in STD["tabel"])
DG = {k: POST[k]["diagnosis"] for k in ("tahap1", "std", "ext")}
lpt_min = min(d["langkah_per_tau"] for d in DG.values()); rhat_max = max(max(d["rhat"].values()) for d in DG.values())
ess_min = min(min(d["ess"].values()) for d in DG.values())
rhoNS = POST["std"]["korelasi"][POST["std"]["urutan"].index("NSOILBASE")][POST["std"]["urutan"].index("N_recovery")]
ROBD = {(r["varian"], r["model"]): r for r in ROB}

f0 = lambda x: f"{x:.0f}"; f1 = lambda x: f"{x:.1f}"; f2 = lambda x: f"{x:.2f}"; f3 = lambda x: f"{x:.3f}"
pct = lambda sim, obs: 100 * (sim / obs - 1)


def ci(m, k, fmt=f1):
    q = POST[m]["posterior"][k]
    return f"{fmt(q['median'])} ({fmt(q['q2_5'])}–{fmt(q['q97_5'])})"


# ------------------------------------------------------------------ angka turunan
o22, o20 = V["S2022"]["obs"], V["S2020"]["obs"]
A = {m: {s: V[s][m]["A"] for s in ("S2022", "S2020")} for m in ("std", "ext")}
err0 = {m: {s: pct(A[m][s]["Y0"], V[s]["obs"]["Y0"]) for s in A[m]} for m in A}
err140 = {m: {s: pct(A[m][s]["Y140"], V[s]["obs"]["Y140"]) for s in A[m]} for m in A}
nsbB = {s: V[s]["std"]["NSOILBASE_B"] for s in ("S2022", "S2020")}
rm = V["rmse_rasio_LAI"]
TR = {r["lokasi"]: r for r in V["transfer_agustiani_tergenang"]}
tab_s = {r["dosis"]: r for r in STD["tabel"]}; tab_e = {r["dosis"]: r for r in EXT["tabel"]}
met = {(r["set"], r["variabel"]): r for r in POT["metrik"]}
sob = {k: {r.get("index", list(r.values())[0]): r for r in v} for k, v in SOB["hasil"].items()}
wl = {(r["cuaca"], r["musim"]): r for r in WX["ltfe"]}
wsj = {(r["cuaca"], r["dosis"]): r for r in WX["sujinah"]}
wst = {r["periode"]: r for r in WX["statistik"]}
vr = {(r["model"], r["musim"]): r for r in VAR["ringkasan"]}
nni = {(r["dosis"], r["HST"]): r["NNI"] for r in VAR["nni_awal"]}

# ------------------------------------------------------------------ dokumen
# Mode: "kirim" (naskah untuk jurnal: 1 kolom, spasi 1,5, nomor baris) atau "baca" (tata letak artikel: 2 kolom)
BACA = "baca" in sys.argv[1:]
FINAL = "final" in sys.argv[1:]
from docx.enum.section import WD_SECTION
doc = Document()
st = doc.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(9.5 if BACA else 11)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
st.paragraph_format.line_spacing = 1.08 if BACA else 1.5; st.paragraph_format.space_after = Pt(3 if BACA else 4)
if BACA:
    st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
for lvl, size in (((1, 10.5), (2, 9.5), (3, 9.5)) if BACA else ((1, 13), (2, 11.5), (3, 11))):
    h = doc.styles[f"Heading {lvl}"]; h.font.name = "Times New Roman"; h.font.size = Pt(size); h.font.bold = True
    h.font.color.rgb = RGBColor(0, 0, 0); h.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        h.element.rPr.rFonts.attrib.pop(qn(a), None)
    h.paragraph_format.space_before = Pt(8 if BACA else 10); h.paragraph_format.space_after = Pt(3 if BACA else 4)
    h.paragraph_format.keep_with_next = True
sec = doc.sections[0]
sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
if BACA:
    sec.left_margin = sec.right_margin = Cm(1.8); sec.top_margin = Cm(2.0); sec.bottom_margin = Cm(1.8)
    hp = sec.header.paragraphs[0]; hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    hr = hp.add_run("Draft (not peer reviewed) — N-limited WOFOST 8.1 for tropical transplanted rice"); hr.italic = True; hr.font.size = Pt(8)
else:
    sec.left_margin = sec.right_margin = Cm(2.5); sec.top_margin = sec.bottom_margin = Cm(2.3)
    # nomor baris (untuk reviewer)
    ln = OxmlElement("w:lnNumType"); ln.set(qn("w:countBy"), "1"); ln.set(qn("w:restart"), "continuous"); ln.set(qn("w:distance"), "283")
    cols = sec._sectPr.find(qn("w:cols"))
    (cols.addprevious(ln) if cols is not None else sec._sectPr.append(ln))
TEXT_W = 17.4 if BACA else 16.0


def set_cols(n, new_page=False):
    """Mulai section baru (kontinu) dengan n kolom; dipakai hanya pada mode baca."""
    s = doc.add_section(WD_SECTION.NEW_PAGE if new_page else WD_SECTION.CONTINUOUS)
    c = s._sectPr.find(qn("w:cols"))
    if c is None:
        c = OxmlElement("w:cols"); s._sectPr.append(c)
    c.set(qn("w:num"), str(n)); c.set(qn("w:space"), str(int(0.6 * 567)))
    return s
fp = sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
for tag, txt in (("begin", None), (None, "PAGE"), ("end", None)):
    r = fp.add_run()
    if tag:
        e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), tag); r._r.append(e)
    else:
        e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = txt; r._r.append(e)


def P(text, bold=False, italic=False, align=None, size=None, verify=False, style=None):
    p = doc.add_paragraph(style=style)
    r = p.add_run(text); r.bold = bold; r.italic = italic
    if size:
        r.font.size = Pt(size)
    if align:
        p.alignment = align
    if verify:
        r.font.highlight_color = WD_COLOR_INDEX.YELLOW
    return p


def PR(parts, style=None):
    """Paragraf dengan potongan [(teks, 'b'|'i'|'v'|'')]; 'v' = sorot kuning (perlu verifikasi)."""
    p = doc.add_paragraph(style=style)
    for t, f in parts:
        r = p.add_run(t)
        r.bold = "b" in f; r.italic = "i" in f
        if "v" in f:
            r.font.highlight_color = WD_COLOR_INDEX.YELLOW
    return p


def H(t, lvl=1):
    doc.add_heading(t, level=lvl)


def FIG(name, caption, width=None):
    if BACA:
        set_cols(1)
    doc.add_picture(str(G / f"{name}.png"), width=Cm(width or TEXT_W))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[-1].paragraph_format.keep_with_next = True
    p = doc.add_paragraph(); p.paragraph_format.line_spacing = 1.0 if BACA else 1.15
    cs = 8.5 if BACA else 9.5
    r = p.add_run(caption.split(".", 1)[0] + "."); r.bold = True; r.font.size = Pt(cs)
    r2 = p.add_run(caption.split(".", 1)[1]); r2.font.size = Pt(cs)
    if BACA:
        p.paragraph_format.space_after = Pt(8)
        set_cols(2)


def TABLE(caption, header, rows, widths=None, note=None, fs=8.5):
    if BACA:
        set_cols(1)
        fs = min(fs, 8.0)
        if widths:
            k = TEXT_W / sum(widths); widths = [w * k for w in widths]
    p = doc.add_paragraph(); p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.keep_with_next = True
    r = p.add_run(caption.split(".", 1)[0] + "."); r.bold = True; r.font.size = Pt(9.5)
    r2 = p.add_run(caption.split(".", 1)[1]); r2.font.size = Pt(9.5)
    t = doc.add_table(rows=1, cols=len(header)); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]; c.text = ""; rr = c.paragraphs[0].add_run(h); rr.bold = True; rr.font.size = Pt(fs)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""; rr = cells[i].paragraphs[0].add_run(str(v)); rr.font.size = Pt(fs)
    for row in t.rows:
        for j, c in enumerate(row.cells):
            for pp in c.paragraphs:
                pp.paragraph_format.line_spacing = 1.0; pp.paragraph_format.space_after = Pt(0)
                pp.alignment = WD_ALIGN_PARAGRAPH.LEFT
            if widths:
                c.width = Cm(widths[j])
    if note:
        q = doc.add_paragraph(); q.paragraph_format.line_spacing = 1.0; q.alignment = WD_ALIGN_PARAGRAPH.LEFT
        rr = q.add_run(note); rr.font.size = Pt(8); rr.italic = True
    doc.add_paragraph()
    if BACA:
        set_cols(2)


# ================================================================== halaman judul
if not FINAL:
    P("DRAFT manuscript generated from WOFOST Studio results on " + dt.date.today().strftime("%d %B %Y")
      + ". Text highlighted in yellow must be verified or completed by the authors before submission.", italic=True, size=9, verify=True)
    P("Target journal: European Journal of Agronomy (alternatives: Agricultural Systems; Environmental Modelling & Software).", italic=True, size=9)
TITLE = ("Nitrogen-limited WOFOST 8.1 for tropical transplanted rice: parameter-consistency fixes, a leaf-level "
         "nitrogen extension and independent omission-plot validation in West Java, Indonesia")
P(TITLE, bold=True, size=15, align=WD_ALIGN_PARAGRAPH.CENTER)
P("Zainal Arifinᵃ*, Iwan Gunawanᵇ", bold=True, size=11, align=WD_ALIGN_PARAGRAPH.CENTER)
PR([("ᵃ ", ""), ("Department of Agribusiness, Vocational School, Universitas Sebelas Maret, Indonesia", "")]).alignment = WD_ALIGN_PARAGRAPH.CENTER
PR([("ᵇ ", ""), ("Department of Mechanical Engineering, Universitas Khairun, Ternate 97719, Indonesia", "")]).alignment = WD_ALIGN_PARAGRAPH.CENTER
P("ORCID: Zainal Arifin https://orcid.org/0009-0008-0345-3167; Iwan Gunawan https://orcid.org/0000-0002-2784-4436",
  size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
P("* Corresponding author: Zainal Arifin, zainal.arifin@staff.uns.ac.id. Co-author e-mail: Iwan Gunawan, iwan99gun@unkhair.ac.id",
  size=9.5, align=WD_ALIGN_PARAGRAPH.CENTER)

# ---- blok 1: pustaka terverifikasi, highlights, abstrak, pendahuluan (disisipkan ke buat_naskah.py) ----
import re as _re
MEK = J("mekanisme_n_daun.json")
MAR = J("validasi_marpaung_karangploso.json"); MRD = J("marpaung2024_karangploso_inpari32.json")
_mo = MAR["observasi"]
mar_rmse = {m: (sum((MAR[m]["rLAI"][a] - _mo["rLAI"][a]) ** 2 for a in ("28", "42", "56")) / 3) ** 0.5
            for m in ("std", "ext")}
_mnj = MRD["tabel9_N_jaringan"]["N_jaringan_persen"]
mar_nj0 = _mnj["P1"]; mar_njF = sum(v for k, v in _mnj.items() if k != "P1") / 9
_mt = {k: v[3] for k, v in MRD["tabel4_jumlah_anakan_per_rumpun"].items() if k.startswith("P")}
_ml = {k: v[3] for k, v in MRD["tabel3_luas_daun_cm2_per_rumpun"].items() if k.startswith("P")}
_m100 = [k for k, d in MRD["perlakuan_N_kg_ha"].items() if d == 100]
mar_rtil = _mt["P1"] / (sum(_mt[k] for k in _m100) / 3)
mar_rlpt = (_ml["P1"] / _mt["P1"]) / (sum(_ml[k] for k in _m100) / 3 / (sum(_mt[k] for k in _m100) / 3))
MARU = MAR["pembaruan_NLEAF"]
PUS = json.load(open(ROOT / "naskah" / "pustaka_terverifikasi.json", encoding="utf-8"))
_FIXREF = {
    "iizumi2009": ("IIZUMI, T., YOKOZAWA, M., NISHIMORI, M.,", "Iizumi, T., Yokozawa, M., Nishimori, M.,"),
    "monsi2005": ("MONSI, M.,", "Monsi, M., Saeki, T.,"),
    "vos2005": ("Putten, P.v.d., Birch, C.,", "van der Putten, P.E.L., Birch, C.J.,"),
    "buresh2008": ("Buresh, R., Ramesh Reddy, K., van Kessel, C., 2008. Nitrogen Transformations in Submerged Soils. Agronomy Monographs None, 401-436.",
                   "Buresh, R.J., Reddy, K.R., van Kessel, C., 2008. Nitrogen transformations in submerged soils. In: Schepers, J.S., "
                   "Raun, W.R. (Eds.), Nitrogen in Agricultural Systems. Agronomy Monograph 49. ASA, CSSA, SSSA, Madison, WI, pp. 401–436."),
    "lemaire1997": ("In: Diagnosis of the Nitrogen Status in Crops. Springer Berlin Heidelberg,", "In: Lemaire, G. (Ed.), Diagnosis of the Nitrogen Status in Crops. Springer, Berlin,"),
}
for _k, (_a, _b) in _FIXREF.items():
    PUS[_k]["ref"] = PUS[_k]["ref"].replace(_a, _b)
PUS["iizumi2009"]["cite"] = "Iizumi et al., 2009"
PUS["gelman1992"]["ref"] = PUS["gelman1992"]["ref"].replace("Statistical Science 7.", "Statistical Science 7, 457–472.")
PUS["liu2026"]["ref"] = PUS["liu2026"]["ref"].replace("Plant and Soil None.", "Plant and Soil, in press."); PUS["monsi2005"]["cite"] = "Monsi and Saeki, 2005"
for _k in PUS:  # tanda pisah halaman (hanya di luar DOI)
    _t, _, _d = PUS[_k]["ref"].partition(" https://doi.org/")
    PUS[_k]["ref"] = _re.sub(r"(\d)-(\d)", r"\1–\2", _t) + (" https://doi.org/" + _d if _d else "")


def C(*ks, pre=""):
    """Sitasi dalam kurung dari kunci pustaka terverifikasi."""
    return "(" + pre + "; ".join(PUS[k]["cite"] if k in PUS else k for k in ks) + ")"


dek = {(r["musim"], str(r["waktu"])): r for r in MEK["dekomposisi"]}
strat = {(r["musim"], r["model"], str(r["waktu"])): r for r in MEK["strategi_N"]}
inter = {r["musim"]: r for r in MEK["intersepsi"]}
bpl = {(r["musim"], str(r["waktu"])): r["obs_rasio"] for r in MEK["biomasa_per_luas_daun"]}
spad_red = [100 * (1 - strat[("S2020", "std", t)]["obs_rasio_SPAD"]) for t in ("35", "FL")]
lai_red_obs = [100 * (1 - strat[(s, "std", t)]["obs_rasio_LAI"]) for s, t in (("S2022", "35"), ("S2022", "60"), ("S2020", "35"), ("S2020", "FL"))]
sln_red_std = [100 * (1 - strat[(s, "std", t)]["sim_rasio_SLN"]) for s, t in (("S2022", "35"), ("S2022", "60"), ("S2020", "35"), ("S2020", "FL"))]
sln_ratio_ext = [strat[(s, "ext", t)]["sim_rasio_SLN"] for s, t in (("S2022", "35"), ("S2022", "60"), ("S2020", "35"), ("S2020", "FL"))]
til_share = [dek[(s, t)]["porsi_anakan"] for s, t in (("S2022", "60"), ("S2020", "FL"))]

H("Highlights")
for h in ("Three parameter-consistency problems were found in the default WOFOST 8.1 setup",
          f"Blind prediction of independent 0-N omission plots was within {max(abs(err0['std']['S2022']), abs(err0['std']['S2020'])):.1f}% error",
          "Indigenous soil N supply was stable over five years at the calibration station",
          "N-deficient rice kept leaf N per area and cut leaf area; WOFOST 8.1 did the opposite",
          f"A one-parameter leaf-N extension cut the LAI-response RMSE from {rm['std']:.2f} to {rm['ext']:.2f}"):
    P("• " + h)

H("Abstract")
ABSTRACT = (
    "Nitrogen (N)-limited crop models increasingly guide fertiliser management in tropical rice, but are rarely tested for "
    "internal consistency or against independent N-omission data. We evaluated WOFOST 8.1 for the Indonesian "
    "rice Inpari-32 with published data from West Java. Potential-production parameters were calibrated on three 2016 "
    "experiments and N parameters on an N-rate trial (23–207 kg N ha⁻¹); evaluation combined staged Bayesian inference, "
    "cross-validation and blind prediction of two seasons of 0-N omission plots. Three consistency problems were corrected: "
    "a recalibrated RGRLAI below RGRLAI_MIN inverted the juvenile N-stress response, calibrated AMAXTB was ignored by the "
    "N-dependent photosynthesis, and N stress acted on leaf expansion only in a juvenile window that closed before deficiency "
    "developed. The corrected model reproduced grain yield at all "
    f"N rates (error ≤{cal_err:.0f}%) and predicted independent 0-N yields within "
    f"{max(abs(err0['std']['S2022']), abs(err0['std']['S2020'])):.1f}%; indigenous N supply inferred from omission plots "
    f"({f1(nsbB['S2022'])}–{f1(nsbB['S2020'])} kg N ha⁻¹) matched the calibrated value ({f1(ps['NSOILBASE'])}). "
    f"N-deficient rice kept leaf greenness (SPAD −{min(spad_red):.0f} to −{max(spad_red):.0f}%) while reducing "
    f"leaf area by {min(lai_red_obs):.0f}–{max(lai_red_obs):.0f}%, mostly through smaller leaf area per tiller, whereas WOFOST 8.1 "
    f"kept leaf area and diluted leaf N by {min(sln_red_std):.0f}–{max(sln_red_std):.0f}%. A one-parameter "
    f"LINTUL3-type extension reversing this strategy cut the error of the leaf-area response from {rm['std']:.2f} to "
    f"{rm['ext']:.2f} and blindly reproduced a second N-rate trial on the same variety "
    f"(ratio RMSE {mar_rmse['ext']:.2f} versus {mar_rmse['std']:.2f}). Soil N supply was stable over five years but did not "
    "transfer to farmers' fields. Parameter consistency and leaf-area plasticity are prerequisites "
    "for simulating N responses of tropical rice.")
P(ABSTRACT)
N_ABS = len(ABSTRACT.split())
assert N_ABS <= 246, f"abstrak {N_ABS} kata; batas Elsevier 250, sisakan margin untuk penghitung kata berbeda"
PR([("Keywords: ", "b"), ("crop model; WOFOST; nitrogen nutrition index; leaf area plasticity; indigenous nitrogen supply; "
                          "omission plot; Bayesian calibration", "")])
if BACA:
    for par in doc.paragraphs[-2:-1]:
        pPr = par._p.get_or_add_pPr(); shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), "EEF2F6"); pPr.append(shd)
    set_cols(2)

# ================================================================== 1 Introduction
H("1. Introduction")
P("Rice is the staple food of Indonesia, and the irrigated lowlands of Java supply a large share of national production. "
  "Nitrogen (N) is the nutrient that most often limits rice yield in these systems, while farmer N rates and N-use efficiency "
  "vary widely " + C("cassman1998", "Cassman et al., 2002", "Dobermann et al., 2003a") + ". Yield gaps of intensive rice in Indonesia remain "
  "substantial " + C("agus2019") + ", and site-specific N management based on indigenous N supply has repeatedly "
  "increased N-use efficiency in Asian irrigated rice " + C("pampolino2007") + ". Process-based crop models are the "
  "standard tool for exploring such management options beyond the range of field trials " + C("van Ittersum et al., 2013") + ", "
  "but multi-model comparisons show large structural uncertainty in simulated rice yield " + C("li2015") + ", and "
  "calibration choices alone can change model behaviour substantially " + C("Wallach et al., 2019", "wallach2021") + ".")
PR([("WOFOST is one of the most widely used crop growth models (van Diepen et al., 1989; de Wit et al., 2019). In Asia it "
     "has been used for regional yield estimation with leaf area assimilation " + C("huang2015", "lu2025") + ", seasonal "
     "rice yield forecasting in mainland Southeast Asia " + C("wanthanaporn2024") + " and global sensitivity analysis "
     + C("wang2013", "li2023") + ". WOFOST 8.1 couples crop growth to soil and crop N balances and makes leaf photosynthesis "
     "depend on specific leaf N " + C("berghuijs2024") + ". ", ""),
    ("Applications specifically to tropical transplanted rice nonetheless remain scarce: an OpenAlex search for works "
     "with WOFOST in the title or abstract and at least one author affiliated with a tropical Southeast Asian country "
     "(Brunei, Cambodia, Indonesia, Laos, Malaysia, Myanmar, the Philippines, Singapore, Thailand, Timor-Leste or "
     "Vietnam; OpenAlex API, accessed 26 September 2026) returned four distinct works (five indexed records, including "
     "one preprint–publication pair), three of them on rice " + C("wanthanaporn2024") + " (search filter given in "
     "Table S1)", ""),
    (". In Indonesia, rice modelling has relied mainly on ORYZA " + C("boling2007") + ", which, like LINTUL3 (Shibu et al., "
     "2010), represents N effects on leaf area expansion, whereas WOFOST 7.x did not simulate N at all.", "")])
P("How a model reproduces the N response matters as much as whether it does. N-deficient rice reduces tillering and leaf "
  "expansion and increases specific leaf weight, so that N per unit leaf area changes much less than leaf area "
  + C("peng1993", "zhong2003", "vos2005") + "; the critical N concentration of the crop declines with biomass along a dilution curve "
  + C("sheehy1998", "ataulkarim2013") + " as N is concentrated in the upper, well-lit leaves " + C("lemaire1997", "hikosaka2016")
  + ". Photosynthetic capacity, in turn, scales with leaf N per unit area because most leaf N is invested in the "
  "photosynthetic apparatus " + C("evans1989", "makino2011") + ". A model can therefore reach the right yield by reducing "
  "leaf area (as rice does) or by diluting leaf N at constant leaf area; the two routes diverge in leaf area, canopy "
  "reflectance and N uptake, which are exactly the variables used for remote-sensing assimilation and N diagnosis "
  + C("zha2020", "chen2022") + ".")
P("Two further obstacles hamper evaluation in Indonesia. Experimental data with the detail required for calibration "
  "(dates, leaf area and biomass time series, N treatments) are rarely public, so datasets must be reconstructed from "
  "published tables and figures " + C("drevon2017") + ". And recalibrating a subset of parameters of a complex model can "
  "silently create inconsistencies with parameters left at their defaults, particularly when a newer model version "
  "replaces some parameters by others. Both issues are seldom reported, yet both affect the credibility of model-based N "
  "recommendations.")
P("Here we calibrate and evaluate WOFOST 8.1 for the modern inbred rice variety Inpari-32 in West Java using only "
  "literature-mined data and an open desktop tool (WOFOST Studio) that wraps PCSE. The objectives were (i) to identify and "
  "correct parameter-consistency problems that arise when WOFOST 8.1 is recalibrated for tropical rice; (ii) to test whether "
  "the model reproduces the observed N response of yield, biomass and leaf area, and to diagnose the mechanism behind any "
  "mismatch; (iii) to test a minimal LINTUL3-type extension; and (iv) to evaluate the calibrated N supply by blind "
  "prediction of independent N-omission plots, with explicit quantification of parameter, weather and variety uncertainty.")

# ================================================================== 2 Methods
H("2. Materials and methods")
H("2.1. Modelling framework", 2)
P("Simulations used PCSE 6.0.13 through WOFOST Studio, a PySide6 application developed for this study that provides "
  "model runs, sowing-date batches, Morris/Sobol/eFAST sensitivity analysis, least-squares and MCMC calibration, "
  "ensemble Kalman filtering and climate scenarios (Fig. 1). Potential production was simulated with WOFOST 7.2 "
  "(Wofost72_PP) and N- and water-limited production with WOFOST 8.1 using the classic water and N balances "
  "(Wofost81_NWLP_CWB_CNB). Crop parameters started from the IRRI variety IR72 in the official WOFOST parameter "
  "repository (branch wofost81, stored locally for reproducibility). Table-valued (AFGEN) parameters were calibrated "
  "through multipliers (e.g. AMAXTB@y scales the whole table; SLATB@ya and SLATB@yb scale the table before and after "
  "DVS 0.65). Transplanting shock was emulated following ORYZA2000 (Bouman et al., 2001): leaf-area growth is held for "
  "SHCKL × TSTR and development delayed by SHCKD × TSTR, where TSTR is the thermal time accumulated in the nursery "
  "(SHCKL = 0.25, SHCKD = 0.40). Because the classic water balance assumes freely draining soil, continuously flooded "
  "paddies were emulated by 2 cm irrigation every 2 days; without it the model produced artificial water stress in "
  "dry-season runs (minimum transpiration reduction factor 0.38).")
FIG("Fig1_workflow", "Fig. 1. Workflow of the study: literature-mined datasets (left), two-step model development and "
    "uncertainty analysis in WOFOST Studio (centre), and internal and independent evaluation (right). LTFE, long-term "
    "fertility experiment; DS, dry season; WS, wet season.")

H("2.2. Data", 2)
P("All data were extracted from peer-reviewed publications (Table 1). Values given only in figures were digitised at the "
  "pixel level with axis calibration on four major ticks, a procedure with high reported reliability " + C("drevon2017") + "; the digitising error (±3 px) was combined with the reported "
  "experimental standard deviation to weight observations. Transplanting dates were not reported for any dataset and "
  "were assumed (1 May 2016; 22 November 2017; 1 May 2022; 2 August 2020; 15 May 2023); the sensitivity of all results to ±21 days "
  "was tested. Yields reported at 14% moisture were converted to dry matter (× 0.86). Leaf area per hill was converted "
  "to LAI with the reported planting density.")
TABLE("Table 1. Datasets used for calibration and evaluation.",
      ["Dataset", "Site, season", "Variety", "Treatments", "Variables", "Use"],
      [["Agustiani et al. (2018a, b)", "Subang, Indramayu, Bandung; DS 2016", "Inpari-32", "126 kg N ha⁻¹, near-potential",
        "LAI, AGB, stem at 7/67/112 DAT; grain yield", "Step 1 calibration"],
       ["Sujinah et al. (2020), Exp. II", "KP Sukamandi; WS 2017/18", "Inpari-32 (+5 genotypes)", "23, 115, 207 kg N ha⁻¹",
        "Grain, AGB at maturity (Inpari-32); leaf area & biomass at 14/28 DAT, flowering, maturity (dose means)", "Step 2 calibration"],
       ["Susanti et al. (2023)", "LTFE Sukamandi; DS 2022", "Inpari-33", "+PK (0 N) vs +NPK (140 kg N ha⁻¹)",
        "Grain; leaf area & biomass at 21/35/60 DAT", "Independent validation"],
       ["Hikmah et al. (2021)", "LTFE Sukamandi; Jul–Dec 2020", "Inpari-33", "0 N vs NPK (140 kg N ha⁻¹)",
        "Grain; leaf area at 21/35 DAT and flowering", "Independent validation"],
       ["Marpaung et al. (2024)", "Karangploso (Malang), East Java; DS 2023", "Inpari-32",
        "0 (unfertilised) vs 50, 100, 150 kg N ha⁻¹ (× PGPR)",
        "Grain; leaf area, tillers, biomass at 14/28/42/56 DAT; tissue N", "Independent validation (same variety)"]],
      widths=[3.0, 3.0, 1.8, 2.8, 4.0, 2.0],
      note="DS, dry season; WS, wet season; DAT, days after transplanting; AGB, above-ground biomass; LTFE, long-term fertility experiment (since 1994).")

H("2.3. Weather and soil", 2)
P("Daily weather was taken from Open-Meteo (ERA5-based reanalysis; Hersbach et al., 2020) at each site, with daily rainfall capped at the PCSE input limit of 250 mm (one day at Karangploso); NASA POWER was "
  "used as an alternative source to quantify weather uncertainty " + C("vanwart2013", "bai2010") + ". Soils were parameterised as clayey paddy soils "
  "(field capacity 0.42, wilting point 0.22 m³ m⁻³) with a 5 cm surface storage.")

H("2.4. Step 1: potential production", 2)
P(f"Phenology (TSUM1, TSUM2) was fitted to the reported flowering and maturity dates. Growth parameters (AMAXTB@y, SPAN, "
  f"TDWI, RGRLAI) were fitted jointly to the three 2016 experiments by weighted least squares with multi-start "
  f"optimisation, while the specific leaf area multipliers were fixed at literature-consistent values "
  f"(SLATB@ya = {POT['parameter']['SLATB@ya']}, SLATB@yb = {POT['parameter']['SLATB@yb']}) because free calibration "
  f"drove SLA to its lower bound. Leaf area at maturity measured with a canopy analyser includes senescent leaves and "
  f"was given a large uncertainty because WOFOST simulates green LAI only. WOFOST allocates all post-anthesis "
  "assimilate to the storage organ once FOTB reaches 1 (default at DVS 1.2), whereas rice continues to accumulate stem "
  "mass after flowering (Table 1). We therefore implemented an optional parameter, PART_DELAY, that shifts the DVS breakpoints of "
  "FLTB, FSTB and FOTB for DVS ≥ 1 by the same amount; because these three tables sum to 1 at every DVS in the "
  "unmodified crop file and linear interpolation is affine, shifting them identically preserves this identity at any "
  "DVS without renormalisation. PART_DELAY was calibrated jointly with AMAXTB@y, SPAN, TDWI and RGRLAI against the same "
  "three 2016 experiments, now including stem mass (TWST) at 7, 67 and 112 DAT, and compared by AICc with a refit that "
  "excluded it. We tested whether adopting the PART_DELAY-calibrated Step 1 changes the N-response conclusions by "
  "repeating the Step 2 least-squares calibration and the blind LTFE prediction (not the full staged MCMC) with the new "
  "baseline (Section 3.1).")

H("2.5. Step 2: parameter consistency in WOFOST 8.1", 2)
P("Three problems were identified while moving the calibrated crop to WOFOST 8.1, and corrected in WOFOST Studio.")
P("(i) Juvenile N effect. PCSE reduces juvenile leaf expansion by RFRGRL = 1 − (1 − I)(RGRLAI − RGRLAI_MIN)/RGRLAI, where "
  "I is an index of leaf N concentration. The recalibrated RGRLAI (0.0035) is lower than the default RGRLAI_MIN (0.004), "
  "which turns RFRGRL above 1 so that N stress accelerates leaf growth. RGRLAI_MIN was therefore expressed as a fraction "
  "of RGRLAI (RGRLAI_MIN_FR = 0.5, the ratio of the IR72 defaults).")
P("(ii) Photosynthesis. WOFOST 8.1 computes maximum leaf photosynthesis from AMAX_REF and specific leaf N " + C("evans1989", "hikosaka2016") + " and does not "
  "read AMAXTB, so the AMAXTB multiplier calibrated in Step 1 was silently lost. AMAX_REF and KN, which are required by "
  "PCSE 6.0.13, are also absent from the official wofost81 parameter file. We set AMAX_REF to the maximum of the "
  f"calibrated AMAXTB ({36.07:.1f} kg CO₂ ha⁻¹ h⁻¹) and KN to 0.4.")
P("(iii) Timing of N effects on leaf expansion. N stress acts on sink-limited leaf expansion only when DVS < 0.2 and "
  "LAI < 0.75. At Sukamandi this window closed before the low-N crop became N-limited (Section 3.3), so the standard "
  "model cannot express an early N effect on leaf area.")

H("2.6. Leaf-N extension", 2)
P("Following LINTUL3 (Shibu et al., 2010), an optional extension (WOFOST 8.1 + NLEAF) multiplies the specific leaf area of "
  "new leaves by exp[−N_SLA(1 − NNI)] and, after the juvenile window, the sink-limited leaf expansion rate by "
  "exp[−N_LAI(1 − NNI)], where NNI is the N nutrition index of the vegetative biomass computed as in the WOFOST 8.0 NPK "
  "module (Lemaire et al., 2008). A third LINTUL3 pathway, reduced leaf partitioning (N_PART), was implemented but "
  "rejected by the data (calibrated to zero). Because N_SLA and N_LAI could not be identified separately (standard "
  "errors larger than the estimates), a single coefficient NLEAF = N_SLA = N_LAI was used. With NLEAF = 0 the extension "
  "reproduces WOFOST 8.1 exactly (maximum daily LAI difference 0.0). The NNI used for partitioning must be computed in "
  "the rate step because PCSE removes state variables from the variable kiosk during integration.")

H("2.7. Calibration of N parameters", 2)
P(f"For point estimation, crop parameters from Step 1 were kept fixed; their uncertainty was propagated in the "
  f"Bayesian analysis (Section 2.9). Indigenous soil N supply (NSOILBASE, released at a constant "
  f"NSOILBASE_FR = 0.01 d⁻¹, i.e. evenly over the season) and fertiliser N recovery were calibrated for both model "
  f"versions, plus NLEAF for the extension. Maximum grain N concentration was fixed at 0.0144 kg N kg⁻¹ and initial "
  f"mineral N at zero; urea was split equally at 7, 28 and 42 DAT. The objective used {STD['n_obs']} observations: grain "
  "yield and AGB at maturity of Inpari-32 at the three N rates (weights 1/(CV·obs), CV 8.75% and 16.8%), and eight "
  "relative responses (23/115 and 207/115 ratios of leaf area and biomass at 28 DAT and flowering) derived from the "
  "dose main effects over six genotypes. Because the dose × genotype interaction was significant, ratio errors were "
  "set conservatively to √2 × plot CV. Using ratios removes the bias in the absolute early LAI (Section 4.4) from the "
  "N-response signal. The validation range of NSOILBASE in PCSE (0–100 kg N ha⁻¹) is an input check rather than a "
  "physiological limit and truncated the posterior, so it was widened to 0–400 kg N ha⁻¹. Because observation errors "
  "were fixed, −2 ln L equals the weighted sum of squares χ² plus a constant, and models were compared with "
  "AICc = χ² + 2k + 2k(k + 1)/(n − k − 1) (Burnham and Anderson, 2002).")

H("2.8. Evaluation", 2)
P("Internal evaluation used leave-one-dose-out (LODO) cross-validation: each N rate was predicted after re-calibrating "
  "on the other two. Independent evaluation used the LTFE seasons (Table 1) in two stages: (A) blind prediction with the "
  "calibrated parameters, and (B) estimation of NSOILBASE from the 0-N yield alone, following the omission-plot "
  "principle (Dobermann et al., 2003b), followed by prediction of the 140-N yield and of the 0-N/140-N ratios of LAI and "
  "biomass. Inpari-33 phenology (107 days after sowing versus 120 for Inpari-32) was represented by scaling TSUM1 and "
  "TSUM2 so that simulated duration matched the variety description. Transfer to the farmers' fields of the 2016 "
  "experiments (126 kg N ha⁻¹) was also tested. A second independent dataset became available for Inpari-32 itself: "
  "an N-rate trial (0, 50, 100, 150 kg N ha⁻¹) at Karangploso, East Java (≈500 m elevation), DS 2023 "
  + C("marpaung2024") + ", with leaf area, tillers and biomass at 14–56 DAT read directly from the published tables "
  "(no digitising). The same stage-B protocol was applied without any phenological adjustment: NSOILBASE was estimated "
  "from the 0-N yield alone and the yield response and the 0-N/100-N ratios of LAI and biomass were then predicted "
  "blind. Two confounders are noted: the control received no P, K or PGPR, and all fertilised plots received PGPR "
  "(differences among PGPR concentrations were not significant for almost all variables), so part of the yield response "
  "to the first 50 kg N ha⁻¹ includes P, K and PGPR effects; the unreported transplanting date and fertiliser "
  "timing were assumed and varied (±14 days; alternative splits).")

H("2.9. Uncertainty and sensitivity", 2)
P("Parameter uncertainty was quantified by staged Bayesian inference with the affine-invariant ensemble sampler "
  + C("goodman2010") + " implemented in emcee (Foreman-Mackey et al., 2013), as in Bayesian calibration of rice models "
  + C("iizumi2009") + ". Stage 1 sampled AMAXTB@y, SPAN, TDWI and RGRLAI against the 2016 data with uniform priors "
  "(24 walkers × 1000 steps). The stage-1 posterior of SPAN and AMAXTB@y, the two potential-production parameters with the "
  "largest Sobol indices, was approximated by a bivariate normal distribution and used as the prior in stage 2, which "
  "sampled them jointly with the N parameters (24 walkers; 800 steps for the standard model); uncertainty from Step 1 was thereby "
  "propagated to the N parameters and predictions. Because the extension posterior contains a ridge along which NLEAF, "
  "NSOILBASE and N recovery trade off (Section 4.2), the default stretch move mixed slowly for this stage; it was "
  "therefore sampled with differential-evolution moves (80% DEMove, 20% snooker move; " + C("terbraak2006", "terbraak2008") + "), initialised overdispersed around the posterior of a preliminary 800-step run, and extended "
  "in blocks of 100 steps until split-R̂ ≤ 1.05 and the chain exceeded 50τ (reached at 1200 steps). Convergence was assessed with the integrated autocorrelation time τ (a chain length "
  "above 50τ is recommended for emcee), the effective sample size and split-R̂ computed across walkers "
  + C("gelman1992") + ", with a burn-in of max(100, 5τ). Sixty-four posterior draws were propagated to the LTFE, and "
  "predictive skill was scored with the continuous ranked probability score (CRPS) and 95% interval coverage "
  + C("gneiting2007") + ". Robustness to the observation model was tested by recalibrating with the ratio errors halved, "
  "doubled, or without ratio data. The posterior of the extension was additionally propagated to the Karangploso trial "
  "(64 draws, NSOILBASE re-estimated from the 0-N yield per draw) and then updated with its three LAI ratios by "
  "importance sampling (sequential Bayesian updating), which narrows the NLEAF interval without re-running the chain. Global sensitivity of grain yield "
  "and maximum LAI to 11 parameters was quantified with Sobol indices (Sobol', 2001; Saltelli, 2002) as implemented in "
  "SALib (Herman and Usher, 2017; N = 128, bootstrap confidence intervals) at 23 and 207 kg N ha⁻¹. Weather uncertainty "
  "was assessed by repeating key simulations with NASA POWER, and variety uncertainty by eight variants of phenology "
  "(±10%, unscaled Inpari-32), AMAX (±10%) and SLA (±10%).")

# ---- blok 2: metode diagnostik mekanisme (2.10) - disisipkan setelah 2.9 ----
H("2.10. Mechanistic diagnostics", 2)
P("To identify how the N response is generated, observed and simulated 0-N/140-N contrasts of the LTFE were decomposed "
  "along four axes. (i) Leaf area was split into tiller number and leaf area per tiller, ln(LAI₀/LAI₁₄₀) = "
  "ln(T₀/T₁₄₀) + ln(A₀/A₁₄₀), using the reported tiller counts. (ii) The leaf-N strategy was characterised by the ratio of "
  "leaf greenness (SPAD, a proxy for leaf N per unit area; " + PUS["peng1993"]["cite"] + ") in observations and by the "
  "ratio of specific leaf N (SLN = leaf N / LAI) in simulations. (iii) Light interception was computed as 1 − exp(−k·LAI) "
  "(Beer's law; " + PUS["monsi2005"]["cite"] + ") with k = 0.6 from the KDIFTB of the crop file, and compared with the yield "
  "ratio to separate interception from radiation-use and sink effects. (iv) Biomass per unit leaf area was used as an "
  "integrated proxy of the inverse of specific leaf area and of stem-to-leaf allocation.")

# ================================================================== 3 Results
H("3. Results")
H("3.1. Potential production", 2)
m = lambda s, v, k: met[(s, v)][k]
P(f"The calibrated potential model (TSUM1 {f0(POT['parameter']['TSUM1'])} and TSUM2 {f0(POT['parameter']['TSUM2'])} °C d, "
  f"SPAN {f1(POT['parameter']['SPAN'])} d, TDWI {f0(POT['parameter']['TDWI'])} kg ha⁻¹, AMAXTB multiplier "
  f"{f2(POT['parameter']['AMAXTB@y'])}) reproduced LAI at flowering with nRMSE of "
  f"{m('subang', 'LAI', 'nRMSE_%'):.0f}–{m('bandung', 'LAI', 'nRMSE_%'):.0f}% and AGB with nRMSE of "
  f"{m('bandung', 'TAGP', 'nRMSE_%'):.0f}–{m('subang', 'TAGP', 'nRMSE_%'):.0f}% (Fig. 2). Grain yield was within "
  f"{m('subang', 'TWSO', 'nRMSE_%'):.1f}% at Subang and {m('indramayu', 'TWSO', 'nRMSE_%'):.1f}% at Indramayu, but "
  f"overestimated by {m('bandung', 'TWSO', 'nRMSE_%'):.0f}% at the highland site Bandung, where the original study "
  "reported water stress during grain filling that a potential-production run cannot represent. Late-season LAI was "
  "underestimated because the measurements included senescent leaves. Shifting the assumed transplanting date by up "
  "to ±30 days changed simulated flowering by 1–2 days after transplanting and yield by up to 10%. Compared with ORYZA "
  "v3 calibrated on the same experiments (Agustiani et al., 2018a), WOFOST had a lower RMSE for AGB "
  f"({ORY['semua']['RMSE_AGB_t']:.1f} vs 1.6 t ha⁻¹) and green LAI ({ORY['tanpa LAI masak']['RMSE_LAI']:.1f} vs 0.5) and the "
  f"same mean normalised RMSE ({ORY['tanpa LAI masak']['RMSEn_rata2_pct']:.0f}% vs 23%), but a larger stem RMSE "
  f"({ORY['semua']['RMSE_batang_t']:.1f} vs 0.7 t ha⁻¹; Table S2). Observed stem mass kept increasing after flowering "
  "(from 4.1 to 7.5 t ha⁻¹ at Subang), whereas WOFOST allocates all post-anthesis assimilates to the panicles, so that "
  "simulated stem mass levelled off at 71–75 DAT (Section 4.2). Adding PART_DELAY and refitting AMAXTB@y, SPAN, TDWI "
  f"and RGRLAI jointly against LAI, AGB, stem mass and grain yield (28 observations) reduced AICc by "
  f"{KP['AICc_A'] - KP['AICc_B']:.0f} points ({KP['AICc_A']:.0f} → {KP['AICc_B']:.0f}) relative to the same refit without "
  f"PART_DELAY, with PART_DELAY = {KP['parameter_B_dengan_PART_DELAY']['PART_DELAY']:.2f} DVS units. The mean normalised "
  f"RMSE fell to {ORY['dengan_PART_DELAY']['RMSEn_pct']:.0f}% (below the ORYZA benchmark of 23%) and the stem RMSE to "
  f"{ORY['dengan_PART_DELAY']['RMSE_batang_t']:.2f} t ha⁻¹, closing most of the gap with ORYZA "
  "(Table S2); stem mass at Bandung, previously underestimated by 25%, matched observations almost exactly. Grain yield "
  "fit worsened slightly at Subang and Indramayu (from −2% to about −7 to −9%) because more assimilate remains in "
  "the stem, while the Bandung yield, already overestimated because water stress during grain filling is not "
  "represented, worsened further (Table S5). This alternative Step 1 requires substantially different values of AMAXTB@y "
  f"(0.90 → {KP['parameter_B_dengan_PART_DELAY']['AMAXTB@y']:.2f}) and SPAN "
  f"({f1(POT['parameter']['SPAN'])} → {KP['parameter_B_dengan_PART_DELAY']['SPAN']:.1f} d), so it was not propagated "
  "through the full N-limited pipeline reported in Sections 3.2–3.5, which uses the original Step 1 throughout for "
  "internal consistency. A lightweight check, however, is reassuring: repeating the Step 2 least-squares calibration "
  "and the blind LTFE prediction with the PART_DELAY baseline gave a similar indigenous N supply "
  f"({KP.get('nsoilbase_check', 116):.0f} kg N ha⁻¹) and 0-N prediction errors of similar magnitude and sign "
  "(+4.7% in 2022, −4.6% in 2020) to the main results (Table 4), and the standard model still showed almost no LAI "
  "response to N (ratios 1.00, 1.00, 0.92 at 21, 35 and 60 DAT versus 0.95, 0.66 and 0.45 observed). The paper's "
  "conclusions about indigenous N supply and the need for the NLEAF extension therefore do not depend on which Step-1 "
  "parameterisation is used, and adopting PART_DELAY as the default Step 1 is a direct, low-risk extension of this work "
  "(Section 4.2).")
FIG("Fig2_potential_calibration", "Fig. 2. Calibration of potential production (WOFOST 7.2 with transplanting shock) for "
    "Inpari-32 at three sites in West Java, dry season 2016: (a–c) leaf area index, (d–f) above-ground biomass, (g–i) grain "
    "dry matter. Symbols: observations digitised from Agustiani et al. (2018a) with combined digitising and experimental "
    "uncertainty.")

H("3.2. Nitrogen response and model comparison", 2)
P(f"The standard WOFOST 8.1 calibrated to NSOILBASE = {f1(ps['NSOILBASE'])} kg N ha⁻¹ and N recovery = "
  f"{f2(ps['N_recovery'])} reproduced grain yield at all three N rates (Fig. 3a; Table 3), with a LODO RMSE of "
  f"{f0(STD['rmse_lodo']['TWSO'])} kg ha⁻¹ ({100 * STD['rmse_lodo']['TWSO'] / 5716:.1f}%). AGB at maturity was "
  f"underestimated at 115 and 207 kg N ha⁻¹ (Fig. 3b), but observed harvest indices at these rates (0.38 and 0.42) are "
  "low compared with 0.45–0.56 for Inpari-32 in the other datasets, and the residuals are within one standard deviation "
  f"of the measurements. The main failure of the standard model was leaf area: the flowering LAI at 23 kg N ha⁻¹ relative "
  f"to 115 kg N ha⁻¹ was {tab_s[23]['rLAIFL_obs']:.2f} observed and {tab_s[23]['rLAIFL_sim']:.2f} simulated (Fig. 3c). "
  f"The NLEAF extension (NLEAF = {f2(pe['NLEAF'])}) reproduced this ratio ({tab_e[23]['rLAIFL_sim']:.2f}) and the "
  f"flowering biomass ratio more closely and had a lower LODO RMSE for grain yield ({f0(EXT['rmse_lodo']['TWSO'])} kg ha⁻¹). "
  f"Cross-validation exposed an identifiability limit: when the 23 kg N ha⁻¹ rate was withheld, the two high rates could "
  f"not separate indigenous supply from fertiliser recovery (NSOILBASE {LODO_S[23]['p_NSOILBASE']:.0f} kg N ha⁻¹, recovery "
  f"{LODO_S[23]['p_N_recovery']:.2f}), and the standard model over-predicted the withheld yield by "
  f"{100 * (LODO_S[23]['TWSO_pred'] / LODO_S[23]['TWSO_obs'] - 1):.0f}%, whereas the extension, additionally constrained by "
  f"the leaf-area response, predicted it within {abs(100 * (LODO_E[23]['TWSO_pred'] / LODO_E[23]['TWSO_obs'] - 1)):.0f}%. "
  f"The two versions had similar support (AICc {STD['AICc']:.2f} vs {EXT['AICc']:.2f}). Neither reproduced "
  f"the 28-DAT leaf area ratio ({tab_s[23]['rLAI28_obs']:.2f} observed; {tab_s[23]['rLAI28_sim']:.2f} and "
  f"{tab_e[23]['rLAI28_sim']:.2f} simulated).")
FIG("Fig3_N_response", "Fig. 3. Response of Inpari-32 to N rate at Sukamandi, wet season 2017/18: (a) grain yield, "
    "(b) above-ground biomass at maturity, (c) LAI at flowering relative to 115 kg N ha⁻¹ (observations are dose main "
    "effects across six genotypes). Error bars: ±1 SD (a, b) and the conservative ratio error (c).")
TABLE("Table 2. Calibrated parameters. Posterior medians and 95% credible intervals from MCMC are given for the N parameters.",
      ["Parameter", "Unit", "Value", "Basis"],
      [["TSUM1 / TSUM2", "°C d", f"{f0(POT['parameter']['TSUM1'])} / {f0(POT['parameter']['TSUM2'])}", "Step 1 (DS 2016)"],
       ["SLATB@ya / SLATB@yb", "–", f"{POT['parameter']['SLATB@ya']} / {POT['parameter']['SLATB@yb']}", "Literature-constrained"],
       ["AMAXTB@y (→ AMAX_REF)", "– (kg CO₂ ha⁻¹ h⁻¹)", f"{f2(POT['parameter']['AMAXTB@y'])} (36.1); {ci('tahap1', 'AMAXTB@y', f2)}", "Step 1 (stage-1 posterior)"],
       ["SPAN", "d", f"{f1(POT['parameter']['SPAN'])}; {ci('tahap1', 'SPAN')}", "Step 1 (stage-1 posterior)"],
       ["TDWI", "kg ha⁻¹", f"{f0(POT['parameter']['TDWI'])}; {ci('tahap1', 'TDWI', f0)}", "Step 1 (stage-1 posterior)"],
       ["RGRLAI (RGRLAI_MIN_FR)", "ha ha⁻¹ d⁻¹ (–)", f"{POT['parameter']['RGRLAI']:.4f} (0.5)", "Step 1 (IR72 ratio)"],
       ["NSOILBASE, WOFOST 8.1", "kg N ha⁻¹", f"{f1(ps['NSOILBASE'])}; {ci('std', 'NSOILBASE')}", "Step 2"],
       ["N recovery, WOFOST 8.1", "–", f"{f2(ps['N_recovery'])}; {ci('std', 'N_recovery', f2)}", "Step 2"],
       ["NSOILBASE, + NLEAF", "kg N ha⁻¹", f"{f1(pe['NSOILBASE'])}; {ci('ext', 'NSOILBASE')}", "Step 2"],
       ["N recovery, + NLEAF", "–", f"{f2(pe['N_recovery'])}; {ci('ext', 'N_recovery', f2)}", "Step 2"],
       ["NLEAF (= N_SLA = N_LAI)", "–", f"{f2(pe['NLEAF'])}; {ci('ext', 'NLEAF', f2)}", "Step 2"],
       ["NMAXSO; NSOILBASE_FR; KN", "kg kg⁻¹; d⁻¹; –", "0.0144; 0.01; 0.4", "Fixed"]],
      widths=[4.5, 3.0, 5.0, 3.5])
TABLE("Table 3. Calibration fit and leave-one-dose-out (LODO) cross-validation at Sukamandi, WS 2017/18.",
      ["Quantity", "Observed", "WOFOST 8.1", "WOFOST 8.1 + NLEAF"],
      [[f"Grain yield, {d} kg N ha⁻¹ (kg ha⁻¹)", tab_s[d]["TWSO_obs"], tab_s[d]["TWSO_sim"], tab_e[d]["TWSO_sim"]] for d in (23, 115, 207)]
      + [[f"AGB, {d} kg N ha⁻¹ (kg ha⁻¹)", tab_s[d]["TAGP_obs"], tab_s[d]["TAGP_sim"], tab_e[d]["TAGP_sim"]] for d in (23, 115, 207)]
      + [["LAI ratio 23/115 N, 28 DAT", tab_s[23]["rLAI28_obs"], tab_s[23]["rLAI28_sim"], tab_e[23]["rLAI28_sim"]],
         ["LAI ratio 23/115 N, flowering", tab_s[23]["rLAIFL_obs"], tab_s[23]["rLAIFL_sim"], tab_e[23]["rLAIFL_sim"]],
         ["Weighted SSE (n = 14)", "–", f2(STD["SSE"]), f2(EXT["SSE"])],
         ["AICc", "–", f2(STD["AICc"]), f2(EXT["AICc"])],
         ["LODO RMSE grain / AGB (kg ha⁻¹)", "–", f"{f0(STD['rmse_lodo']['TWSO'])} / {f0(STD['rmse_lodo']['TAGP'])}",
          f"{f0(EXT['rmse_lodo']['TWSO'])} / {f0(EXT['rmse_lodo']['TAGP'])}"]],
      widths=[6.0, 2.5, 3.0, 3.5])

H("3.3. Why leaf area did not respond to N", 2)
P(f"The simulated NNI of the 23 kg N ha⁻¹ crop stayed at 1 until about 14 DAT and then declined "
  f"({nni[(23, 21)]:.2f} at 21 DAT, {nni[(23, 28)]:.2f} at 28 DAT, {nni[(23, 35)]:.2f} at 35 DAT; "
  "Fig. 4a), whereas the crops at 115 and 207 kg N ha⁻¹ remained unstressed until after flowering. At that time leaf "
  "expansion in WOFOST 8.1 was still sink-limited (exponential phase up to LAIEXP = 6), but outside the juvenile window "
  "in which N stress can act. As a result, simulated LAI was nearly identical across N rates until 50 DAT (Fig. 4b). "
  "With the NLEAF extension, LAI of the low-N crop diverged from about 35 DAT and peaked 1.7 units lower (Fig. 4c).")
FIG("Fig4_NNI_LAI_mechanism", "Fig. 4. (a) Simulated N nutrition index (standard WOFOST 8.1) at three N rates; the shaded "
    "area marks the juvenile window (DVS < 0.2, LAI < 0.75) in which the standard model lets N stress reduce leaf "
    "expansion. (b, c) Simulated LAI with the standard model and with the NLEAF extension.")

H("3.4. Independent validation with omission plots", 2)
P(f"Without any re-calibration, the standard model predicted the 0-N yields of the LTFE at "
  f"{f0(A['std']['S2022']['Y0'])} and {f0(A['std']['S2020']['Y0'])} kg ha⁻¹, against {f0(o22['Y0'])} and "
  f"{f0(o20['Y0'])} kg ha⁻¹ observed ({err0['std']['S2022']:+.1f}% and {err0['std']['S2020']:+.1f}%; Fig. 5a; Table 4). "
  f"NSOILBASE estimated from the 0-N yield of each season ({f1(nsbB['S2022'])} and {f1(nsbB['S2020'])} kg N ha⁻¹) was "
  f"within 2.3% of the value calibrated five years earlier on a different experiment (Fig. 5b). The 140-N yield was "
  f"underestimated by {abs(err140['std']['S2022']):.0f}% in 2022, consistent with the higher yield potential of Inpari-33, "
  f"and overestimated by {err140['std']['S2020']:.0f}% in 2020, when the reported NPK yield was lower than that of the "
  "−P plot and the soil was described as degraded. The standard model again failed to reproduce the reduction of leaf area "
  "under N deficiency (Fig. 5c): observed 0-N/140-N LAI ratios fell from "
  f"{o22['rLAI21']:.2f} to {o22['rLAI60']:.2f} (2022) and from {o20['rLAI21']:.2f} to {o20['rLAIFL']:.2f} (2020), while "
  f"the model gave 0.88–1.00. The NLEAF extension, with NLEAF calibrated on Sujinah et al. (2020) only, reduced the RMSE "
  f"of the six ratios from {rm['std']:.2f} to {rm['ext']:.2f}. Of the six LAI ratios, "
  f"{sum(v['dalam_95'] for k, v in POST['ext']['skor'].items() if 'rLAI' in k)} fell within the 95% predictive intervals of "
  f"the extension and {sum(v['dalam_95'] for k, v in POST['std']['skor'].items() if 'rLAI' in k)} within those of the "
  "standard model.")
FIG("Fig5_independent_validation", "Fig. 5. Blind prediction of the LTFE at Sukamandi (Inpari-33, 0 vs 140 kg N ha⁻¹). "
    "(a) 0-N grain yield (posterior median and 95% predictive interval). (b) Indigenous N supply calibrated on the "
    "WS 2017/18 N-rate experiment (with 95% credible interval) and estimated from each omission season. (c) Ratio of LAI "
    "in the 0-N plot to the 140-N plot; DAT, days after transplanting; flow., flowering.")
TABLE("Table 4. Independent evaluation against LTFE omission plots (blind prediction, no re-calibration).",
      ["Quantity", "DS 2022 obs.", "8.1", "8.1+NLEAF", "2020 obs.", "8.1", "8.1+NLEAF"],
      [["0-N yield (kg ha⁻¹)", f0(o22["Y0"]), f0(A["std"]["S2022"]["Y0"]), f0(A["ext"]["S2022"]["Y0"]), f0(o20["Y0"]), f0(A["std"]["S2020"]["Y0"]), f0(A["ext"]["S2020"]["Y0"])],
       ["140-N yield (kg ha⁻¹)", f0(o22["Y140"]), f0(A["std"]["S2022"]["Y140"]), f0(A["ext"]["S2022"]["Y140"]), f0(o20["Y140"]), f0(A["std"]["S2020"]["Y140"]), f0(A["ext"]["S2020"]["Y140"])],
       ["Yield ratio 0N/140N", f2(o22["rY"]), f2(A["std"]["S2022"]["rY"]), f2(A["ext"]["S2022"]["rY"]), f2(o20["rY"]), f2(A["std"]["S2020"]["rY"]), f2(A["ext"]["S2020"]["rY"])],
       ["LAI ratio, 21 DAT", f2(o22["rLAI21"]), f2(A["std"]["S2022"]["rLAI21"]), f2(A["ext"]["S2022"]["rLAI21"]), f2(o20["rLAI21"]), f2(A["std"]["S2020"]["rLAI21"]), f2(A["ext"]["S2020"]["rLAI21"])],
       ["LAI ratio, 35 DAT", f2(o22["rLAI35"]), f2(A["std"]["S2022"]["rLAI35"]), f2(A["ext"]["S2022"]["rLAI35"]), f2(o20["rLAI35"]), f2(A["std"]["S2020"]["rLAI35"]), f2(A["ext"]["S2020"]["rLAI35"])],
       ["LAI ratio, 60 DAT / flowering", f2(o22["rLAI60"]), f2(A["std"]["S2022"]["rLAI60"]), f2(A["ext"]["S2022"]["rLAI60"]), f2(o20["rLAIFL"]), f2(A["std"]["S2020"]["rLAIFL"]), f2(A["ext"]["S2020"]["rLAIFL"])],
       ["Biomass ratio, 35 / 60 DAT", f"{f2(o22['rDM35'])} / {f2(o22['rDM60'])}", f"{f2(A['std']['S2022']['rDM35'])} / {f2(A['std']['S2022']['rDM60'])}",
        f"{f2(A['ext']['S2022']['rDM35'])} / {f2(A['ext']['S2022']['rDM60'])}", "–", "–", "–"]],
      widths=[4.2, 2.0, 1.8, 2.0, 2.0, 1.8, 2.0], fs=8)
P(f"The Karangploso N-rate trial on Inpari-32 itself confirmed this picture on an independent site, season and "
  f"soil (Table 5). With TSUM unchanged (same variety), simulated maturity was {MAR['ext']['DOM_0N']:.0f} DAT against "
  "the reported 120 DAT. NSOILBASE estimated from the unfertilised plot was "
  f"{MAR['std']['NSOILBASE_fit']:.0f} (standard) and {MAR['ext']['NSOILBASE_fit']:.0f} kg N ha⁻¹ (extension), "
  f"below the Sukamandi values ({f1(ps['NSOILBASE'])}–{f1(pe['NSOILBASE'])} kg N ha⁻¹), as expected for a "
  "different soil. The observed 0-N/100-N LAI ratio fell to "
  f"{_mo['rLAI']['42']:.2f} at 42 DAT, whereas the standard model again predicted almost no leaf-area response "
  f"({MAR['std']['rLAI']['42']:.2f}–{MAR['std']['rLAI']['28']:.2f}); the extension, blind, gave "
  f"{MAR['ext']['rLAI']['56']:.2f}–{MAR['ext']['rLAI']['28']:.2f} (RMSE {mar_rmse['ext']:.2f} versus "
  f"{mar_rmse['std']:.2f}; posterior-mean CRPS {MAR['ext']['prediksi_posterior']['crps_rasio_LAI_rata2']:.3f} versus "
  f"{MAR['std']['prediksi_posterior']['crps_rasio_LAI_rata2']:.3f}). Both models under-predicted the yield response to "
  f"the first 50 kg N ha⁻¹ ({MAR['std']['rY']['50']:.2f} against {_mo['rY']['50']:.2f} observed), which is "
  "expected because the unfertilised control also lacked P, K and PGPR (Section 2.8), so the observed response is not "
  "an N response alone. Two independent observations support the conserved-leaf-N strategy directly: tissue N of the "
  f"unfertilised plants was {mar_nj0:.2f}% against {mar_njF:.2f}% in fertilised plants (a {100 * (1 - mar_nj0 / mar_njF):.0f}% "
  f"reduction, while leaf area at 56 DAT fell by {100 * (1 - _mo['rLAI']['56']):.0f}%), and the leaf-area reduction was "
  f"almost entirely a tiller-number effect (tiller ratio {mar_rtil:.2f}; leaf area per tiller ratio {mar_rlpt:.2f}), "
  "the extreme of the plasticity hierarchy seen in the LTFE (Section 3.6).")
TABLE("Table 5. Blind prediction of the second independent dataset: N-rate trial on Inpari-32, Karangploso, DS 2023 "
      "(Marpaung et al., 2024). NSOILBASE fitted on the 0-N yield only; all ratios predicted blind (dose means over "
      "PGPR concentrations).",
      ["Quantity", "Observed", "8.1", "8.1+NLEAF"],
      [["Yield ratio 50N/0N", f2(_mo["rY"]["50"]), f2(MAR["std"]["rY"]["50"]), f2(MAR["ext"]["rY"]["50"])],
       ["Yield ratio 100N/0N", f2(_mo["rY"]["100"]), f2(MAR["std"]["rY"]["100"]), f2(MAR["ext"]["rY"]["100"])],
       ["Yield ratio 150N/0N", f2(_mo["rY"]["150"]), f2(MAR["std"]["rY"]["150"]), f2(MAR["ext"]["rY"]["150"])],
       ["LAI ratio 0N/100N, 28 DAT", f2(_mo["rLAI"]["28"]), f2(MAR["std"]["rLAI"]["28"]), f2(MAR["ext"]["rLAI"]["28"])],
       ["LAI ratio 0N/100N, 42 DAT", f2(_mo["rLAI"]["42"]), f2(MAR["std"]["rLAI"]["42"]), f2(MAR["ext"]["rLAI"]["42"])],
       ["LAI ratio 0N/100N, 56 DAT", f2(_mo["rLAI"]["56"]), f2(MAR["std"]["rLAI"]["56"]), f2(MAR["ext"]["rLAI"]["56"])],
       ["Biomass ratio 0N/100N, 28/42/56 DAT", f"{f2(_mo['rDM']['28'])} / {f2(_mo['rDM']['42'])} / {f2(_mo['rDM']['56'])}",
        f"{f2(MAR['std']['rDM']['28'])} / {f2(MAR['std']['rDM']['42'])} / {f2(MAR['std']['rDM']['56'])}",
        f"{f2(MAR['ext']['rDM']['28'])} / {f2(MAR['ext']['rDM']['42'])} / {f2(MAR['ext']['rDM']['56'])}"],
       ["NSOILBASE from 0-N plot (kg N ha⁻¹)", "–", f1(MAR["std"]["NSOILBASE_fit"]), f1(MAR["ext"]["NSOILBASE_fit"])],
       ["Maturity (DAT; reported 120)", "120", f0(MAR["std"]["DOM_0N"]), f0(MAR["ext"]["DOM_0N"])]],
      widths=[4.6, 3.2, 2.6, 2.8], fs=8,
      note="Confounders: the control received no P, K or PGPR and all fertilised plots received PGPR, so the observed "
           "yield response includes non-N effects; LAI from leaf area per hill (16 hills m⁻²); dry matter from "
           "grain at 14% moisture × 0.86. Results were robust to the assumed transplanting date (±14 d) and "
           "fertiliser split (Section 2.8).")
P(f"At the three farmers' fields of 2016, the Sukamandi N supply led to yield underestimates of "
  f"{abs(TR['subang']['err_126N_pct']):.0f}% (Subang) and {abs(TR['indramayu']['err_126N_pct']):.0f}% (Indramayu), "
  f"whereas N-saturated runs were within {abs(TR['subang']['err_jenuh_pct']):.1f}% and "
  f"{abs(TR['indramayu']['err_jenuh_pct']):.1f}%. All four locations were classified as low in soil N in the source "
  "publications, so soil tests did not explain the difference.")

H("3.5. Uncertainty and sensitivity", 2)
P(f"All stages converged (Table S4). Stage 1 (production parameters, 1000 steps) reached "
  f"split-R̂ ≤ {max(DG['tahap1']['rhat'].values()):.2f} and a chain length of {DG['tahap1']['langkah_per_tau']:.0f}τ, and stage 2 for the standard model "
  f"(NSOILBASE and N recovery jointly with SPAN and AMAXTB@y; 800 steps) split-R̂ ≤ {max(DG['std']['rhat'].values()):.2f} "
  f"and {DG['std']['langkah_per_tau']:.0f}τ. For the NLEAF extension a preliminary 800-step run with the default stretch move had not "
  "converged (split-R̂ up to 1.20), because NLEAF, NSOILBASE and N recovery trade off along a ridge of similar "
  "likelihood (Section 4.2) that the stretch move explored slowly; with differential-evolution moves (Section 2.9) "
  f"the chains converged cleanly (split-R̂ ≤ {max(DG['ext']['rhat'].values()):.2f}, "
  f"{DG['ext']['langkah_per_tau']:.0f}τ, minimum effective sample size {min(DG['ext']['ess'].values()):.0f}). "
  f"Stage 1 constrained SPAN to {ci('tahap1', 'SPAN')} d and AMAXTB@y to {ci('tahap1', 'AMAXTB@y', f2)}. "
  f"With the bound removed, NSOILBASE had a 95% interval of {ci('std', 'NSOILBASE')} kg N ha⁻¹ and N recovery of "
  f"{ci('std', 'N_recovery', f2)} in the standard model, and the two were negatively correlated (r = {rhoNS:.2f}); NLEAF "
  f"was {ci('ext', 'NLEAF', f2)} (Table 2); sequential updating with the three Karangploso LAI ratios narrowed it to "
  f"{MARU['NLEAF_sesudah'][1]:.2f} [{MARU['NLEAF_sesudah'][0]:.2f}, {MARU['NLEAF_sesudah'][2]:.2f}] "
  f"(importance sampling, effective sample size {MARU['ESS']:.0f}). For the independent LTFE data, the staged posterior of the extension covered "
  f"{100 * POST['ext']['cakupan_95']:.0f}% of the observations within its 95% intervals (standard model "
  f"{100 * POST['std']['cakupan_95']:.0f}%), and the mean CRPS of the LAI ratios was {POST['ext']['crps_rasio_LAI_rata2']:.3f} "
  f"versus {POST['std']['crps_rasio_LAI_rata2']:.3f}. Halving or doubling the ratio errors, or omitting the ratio data, "
  f"changed the 0-N yield predictions by at most "
  f"{max(abs(r['err_Y0_2022'] - ROBD[('dasar (sigma x1)', r['model'])]['err_Y0_2022']) for r in ROB):.1f} percentage points, "
  f"and the extension kept the lower LAI-ratio error in every variant (Table S3). At 23 kg N ha⁻¹, grain yield "
  f"was dominated by SPAN (S_T = {sob['N23_TWSO']['SPAN']['ST']:.2f}) and the maximum grain N concentration NMAXSO "
  f"({sob['N23_TWSO']['NMAXSO']['ST']:.2f}), and maximum LAI by N_LAI ({sob['N23_LAIMAX']['NLAI']['ST']:.2f}), TSUM1 "
  f"({sob['N23_LAIMAX']['TSUM1']['ST']:.2f}) and N_SLA ({sob['N23_LAIMAX']['NSLA']['ST']:.2f}) (Fig. 6). At 207 kg N ha⁻¹ "
  f"the extension parameters had no effect, as intended, and the AMAXTB multiplier now influenced yield "
  f"({sob['N207_TWSO']['AMAXTB@y']['ST']:.2f}), confirming correction (ii).")
FIG("Fig6_Sobol", "Fig. 6. Total-order Sobol indices (N = 128; bars: bootstrap 95% confidence intervals) for (a) grain "
    "yield and (b) maximum LAI of WOFOST 8.1 + NLEAF at 23 and 207 kg N ha⁻¹, Sukamandi WS 2017/18.")
P(f"Replacing Open-Meteo by NASA POWER changed the calibration-season yields by 1–5% and the 2022 0-N prediction from "
  f"{wl[('openmeteo', 'S2022')]['err_Y0_pct']:+.1f}% to {wl[('nasapower', 'S2022')]['err_Y0_pct']:+.1f}% (Fig. S1). The "
  f"2020 season was sensitive (error {wl[('nasapower', 'S2020')]['err_Y0_pct']:+.1f}% with NASA POWER), because the two "
  f"sources differed by {wst['LTFE 2020']['OM_TMAX'] - wst['LTFE 2020']['NP_TMAX']:.1f} °C in mean maximum temperature. "
  f"Across the eight variety variants, 0-N yield errors stayed between {min(vr[(k, s)]['err_Y0_min'] for k in ('std', 'ext') for s in ('S2022', 'S2020')):.0f}% "
  f"and {max(vr[(k, s)]['err_Y0_max'] for k in ('std', 'ext') for s in ('S2022', 'S2020')):+.0f}%, and the extension "
  f"always gave the lower LAI-ratio error (RMSE {min(vr[('ext', s)]['rmse_rLAI_min'] for s in ('S2022', 'S2020')):.2f}–"
  f"{max(vr[('ext', s)]['rmse_rLAI_max'] for s in ('S2022', 'S2020')):.2f} vs "
  f"{min(vr[('std', s)]['rmse_rLAI_min'] for s in ('S2022', 'S2020')):.2f}–{max(vr[('std', s)]['rmse_rLAI_max'] for s in ('S2022', 'S2020')):.2f}; Fig. S2).")

# ---- blok 3: hasil 3.6 diagnostik mekanisme + Tabel 5 - disisipkan sebelum Diskusi ----
H("3.6. Mechanistic diagnosis of the leaf-area response", 2)
d22, d20 = dek[("S2022", "60")], dek[("S2020", "FL")]
P(f"Tiller number explained only {100 * d22['porsi_anakan']:.0f}% (DS 2022, 60 DAT) and {100 * d20['porsi_anakan']:.0f}% "
  f"(2020, flowering) of the log-reduction of LAI in the 0-N plots; the remainder came from a smaller leaf area per tiller "
  f"(ratios {d22['rasio_luas_per_anakan']:.2f} and {d20['rasio_luas_per_anakan']:.2f}), i.e. fewer, shorter or narrower "
  f"and thicker leaves (Table 6). Early in the season (2020, 35 DAT) the tiller contribution was larger "
  f"({100 * dek[('S2020', '35')]['porsi_anakan']:.0f}%). Leaf greenness was reduced by only {spad_red[0]:.0f}% at 35 DAT and "
  f"{spad_red[1]:.0f}% at flowering while LAI was reduced by {lai_red_obs[2]:.0f}% and {lai_red_obs[3]:.0f}%, and the biomass per "
  f"unit leaf area of the 0-N crop was {bpl[('S2022', '35')]:.2f} and {bpl[('S2022', '60')]:.2f} times that of the 140-N crop "
  "(DS 2022, 35 and 60 DAT). The observed crop therefore conserved N per unit leaf area and adjusted leaf area.")
P(f"The standard model did the opposite: it kept LAI nearly unchanged (ratios {strat[('S2022', 'std', '60')]['sim_rasio_LAI']:.2f} "
  f"and {strat[('S2020', 'std', 'FL')]['sim_rasio_LAI']:.2f}) and diluted specific leaf N by {min(sln_red_std):.0f}–"
  f"{max(sln_red_std):.0f}%, which lowered leaf photosynthetic capacity through the AMAX(SLN) relationship; biomass per "
  f"unit leaf area did not change (ratio {strat[('S2022', 'std', '60')]['sim_rasio_WLV_per_LAI']:.2f}). With the NLEAF "
  f"extension, SLN ratios rose to {min(sln_ratio_ext):.2f}–{max(sln_ratio_ext):.2f} and leaf mass per leaf area increased "
  f"({strat[('S2022', 'ext', '60')]['sim_rasio_WLV_per_LAI']:.2f} and {strat[('S2020', 'ext', 'FL')]['sim_rasio_WLV_per_LAI']:.2f}), "
  "moving the simulated strategy towards the observed one. The reduction of LAI lowered the intercepted fraction of "
  f"radiation from {inter['S2022']['f_int140']:.2f} to {inter['S2022']['f_int0']:.2f} in DS 2022 (ratio "
  f"{inter['S2022']['rasio_intersepsi']:.2f}), which explains only part of the yield ratio ({inter['S2022']['rasio_hasil']:.2f}); "
  f"the residual factor ({inter['S2022']['rasio_hasil_per_intersepsi']:.2f}) reflects lower radiation-use efficiency and sink "
  f"size. In 2020 the yield ratio ({inter['S2020']['rasio_hasil']:.2f}) exceeded the interception ratio "
  f"({inter['S2020']['rasio_intersepsi']:.2f}), consistent with the under-performing NPK plot of that season.")
TABLE("Table 6. Mechanistic diagnosis of the 0-N/140-N contrast in the LTFE (observed vs simulated ratios).",
      ["Quantity", "DS 2022, 60 DAT obs.", "8.1", "8.1+NLEAF", "2020, flowering obs.", "8.1", "8.1+NLEAF"],
      [["LAI ratio", f2(d22["rasio_LAI"]), f2(strat[("S2022", "std", "60")]["sim_rasio_LAI"]), f2(strat[("S2022", "ext", "60")]["sim_rasio_LAI"]),
        f2(d20["rasio_LAI"]), f2(strat[("S2020", "std", "FL")]["sim_rasio_LAI"]), f2(strat[("S2020", "ext", "FL")]["sim_rasio_LAI"])],
       ["Tiller-number ratio", f2(d22["rasio_anakan"]), "–", "–", f2(d20["rasio_anakan"]), "–", "–"],
       ["Leaf area per tiller ratio", f2(d22["rasio_luas_per_anakan"]), "–", "–", f2(d20["rasio_luas_per_anakan"]), "–", "–"],
       ["Share of ln LAI ratio due to tillers", f"{100 * d22['porsi_anakan']:.0f}%", "–", "–", f"{100 * d20['porsi_anakan']:.0f}%", "–", "–"],
       ["Leaf N per area ratio (SPAD obs.; SLN sim.)", "n.a.", f2(strat[("S2022", "std", "60")]["sim_rasio_SLN"]), f2(strat[("S2022", "ext", "60")]["sim_rasio_SLN"]),
        f2(strat[("S2020", "std", "FL")]["obs_rasio_SPAD"]), f2(strat[("S2020", "std", "FL")]["sim_rasio_SLN"]), f2(strat[("S2020", "ext", "FL")]["sim_rasio_SLN"])],
       ["Biomass (leaf mass) per leaf area ratio", f2(bpl[("S2022", "60")]), f2(strat[("S2022", "std", "60")]["sim_rasio_WLV_per_LAI"]),
        f2(strat[("S2022", "ext", "60")]["sim_rasio_WLV_per_LAI"]), "n.a.", f2(strat[("S2020", "std", "FL")]["sim_rasio_WLV_per_LAI"]),
        f2(strat[("S2020", "ext", "FL")]["sim_rasio_WLV_per_LAI"])],
       ["Interception ratio (k = 0.6) / yield ratio", f"{inter['S2022']['rasio_intersepsi']:.2f} / {inter['S2022']['rasio_hasil']:.2f}", "–", "–",
        f"{inter['S2020']['rasio_intersepsi']:.2f} / {inter['S2020']['rasio_hasil']:.2f}", "–", "–"]],
      widths=[4.6, 2.2, 1.4, 1.8, 2.3, 1.4, 1.8], fs=8,
      note="Observed tiller counts, leaf area and SPAD from Susanti et al. (2023, Tables 2–3) and Hikmah et al. (2021, Table 3). "
           "Observed biomass per leaf area uses above-ground dry matter; simulated values use leaf dry mass (WLV/LAI). n.a., not reported.")

# ================================================================== 4 Discussion
# ---- blok 4: Diskusi mekanistik + Kesimpulan (menggantikan Diskusi & Kesimpulan lama) ----
H("4. Discussion")
H("4.1. What the inconsistent parameters represent physiologically", 2)
P("The three consistency problems are interactions between recalibrated and default parameters rather than errors in the "
  "equations, but each changes a physiological process. RGRLAI is the temperature-driven relative expansion rate of the "
  "canopy during the sink-limited phase, set by leaf appearance and elongation before canopy closure; RGRLAI_MIN is the "
  "floor of that rate under severe N deficiency. The formula that interpolates between them presumes RGRLAI_MIN < RGRLAI. "
  "For transplanted rice the calibrated RGRLAI (0.0035) is less than half the IR72 default because the canopy restarts "
  "from a few damaged seedlings after transplanting and must first re-establish roots " + C("Bouman et al., 2001")
  + "; keeping the default absolute floor then inverts the ordering and N deficiency accelerates expansion. Expressing "
  "the floor as a fraction of RGRLAI preserves its physiological meaning for any variety or establishment method.")
P("In WOFOST 8.1, maximum leaf photosynthesis increases linearly with specific leaf N up to AMAX_REF, reflecting the "
  "investment of leaf N in Rubisco and electron transport " + C("evans1989", "makino2011") + ", and leaf N declines "
  "exponentially through the canopy " + C("hikosaka2016") + ". The potential-production calibration had lowered the "
  "photosynthetic plateau by 10%, but because WOFOST 8.1 reads AMAX_REF instead of AMAXTB this information was lost and "
  "the N-supply parameters absorbed the error. This is a textbook case of parameter compensation, or equifinality "
  + C("beven2001", "wallach2021") + ": the yield fit is preserved but the parameters lose their physical meaning and "
  f"become non-transferable. After AMAX_REF was tied to the calibrated AMAXTB, N-saturated simulations at the farmers' "
  f"fields fell within {abs(TR['subang']['err_jenuh_pct']):.1f}–{abs(TR['indramayu']['err_jenuh_pct']):.1f}% of observed "
  "yields, compared with +4 to +5% before, showing that the correction restored the separation between photosynthetic "
  "capacity and N supply. Similarly, the classic water balance treats a puddled paddy as a freely draining soil; in "
  "reality the plough pan restricts percolation and maintains ponding, so that dry-season runs without flooding "
  "emulation confound N stress with an artificial water stress that reduces both leaf expansion and radiation-use "
  "efficiency.")

H("4.2. Two canopy strategies: why yield alone cannot validate the N module", 2)
P("The central mechanistic finding is that the standard model and the crop reach similar yields through opposite canopy "
  "strategies. N-deficient rice conserved leaf N per unit area (SPAD reduced by "
  f"{min(spad_red):.0f}–{max(spad_red):.0f}%) and reduced leaf area by {min(lai_red_obs):.0f}–{max(lai_red_obs):.0f}%. "
  "This is consistent with the regulation of leaf N per area in rice: specific leaf weight increases when N is short "
  + C("peng1993") + ", N is preferentially retained in the upper, well-lit leaves where it yields the highest carbon return "
  + C("lemaire1997", "hikosaka2016") + ", and the critical N concentration of the crop declines with biomass along a "
  "dilution curve that is largely a consequence of reduced leaf area per unit biomass " + C("sheehy1998", "ataulkarim2013", "song2020")
  + ". Leaf area is the plastic variable, because both tiller outgrowth and leaf elongation require a threshold leaf N "
  + C("zhong2003", "vos2005", "Gastal and Lemaire, 2002") + ". Our decomposition shows that about "
  f"{100 * min(til_share):.0f}–{100 * max(til_share):.0f}% of the late-season LAI reduction came from fewer tillers and the "
  "rest from smaller leaves, and that the 0-N crop carried "
  f"{bpl[('S2022', '60')]:.2f} times more biomass per unit leaf area. WOFOST 8.1, in contrast, fixes specific leaf area as a "
  "function of development stage and lets N deficiency act on photosynthesis per unit leaf area; the model therefore "
  f"keeps expanding leaves with diluted N (SLN reduced by {min(sln_red_std):.0f}–{max(sln_red_std):.0f}%), a strategy that "
  "rice avoids because photosynthesis per unit N falls steeply at low SLN " + C("evans1989", "makino2011") + ". Canopy "
  "radiation-use efficiency is highest when leaf N follows the light profile, and the benefit of that distribution itself "
  "depends on leaf area (" + PUS["bonelli2020"]["cite"] + "; " + PUS["wang2024"]["cite"] + ", both in maize), so leaf area and N per "
  "unit leaf area are co-regulated rather than independent.")
P("Both strategies reduce canopy photosynthesis, one through interception and one through leaf-level capacity, so the "
  "yield response alone cannot discriminate between them; this is why the two model versions had similar AICc and "
  "cross-validated yield errors. They diverge, however, in every canopy variable: leaf area, light interception, canopy "
  "N distribution and spectral reflectance. The distinction is therefore essential when WOFOST is combined with "
  "remotely sensed LAI " + C("huang2015", "novelli2019", "lu2025") + ": the standard model would interpret a low observed LAI of an "
  "N-deficient field as a growth deficit of unknown cause and correct it by adjusting state variables that are "
  "physiologically unrelated to N. The one-parameter extension corrects the strategy rather than the outcome: it lowers "
  "specific leaf area and exponential-phase expansion in proportion to (1 − NNI), raising the simulated SLN ratio to "
  f"{min(sln_ratio_ext):.2f}–{max(sln_ratio_ext):.2f}, and it improved the leaf-area response in data never used for "
  "calibration, which AICc on the calibration set could not reveal.")
P("The residual yield effect not explained by interception (factor "
  f"{inter['S2022']['rasio_hasil_per_intersepsi']:.2f} in DS 2022) points to sink limitation. N deficiency around panicle "
  "initiation reduces spikelet differentiation and the number of productive panicles; the 0-N plots had 44% fewer "
  "panicles per hill (Susanti et al., 2023). Grain number is a major determinant of the yield advantage of high-yielding "
  "tropical rice " + C("ying1998", "fukushima2019") + ", yet WOFOST partitions assimilates to grain by development stage only and has no "
  "N-dependent sink size. The same structural feature explains why observed harvest indices dropped at 115–207 kg N ha⁻¹ "
  "(0.38–0.42), when surplus N stimulates vegetative and unproductive tiller growth, whereas simulated harvest indices "
  f"remained at {min(tab_s[d]['TWSO_sim'] / tab_s[d]['TAGP_sim'] for d in (115, 207)):.2f}–"
  f"{max(tab_s[d]['TWSO_sim'] / tab_s[d]['TAGP_sim'] for d in (115, 207)):.2f}. The benchmark against ORYZA points to the "
  "same structural element: in the 2016 data stem mass rose by 1–3 t ha⁻¹ after flowering, consistent with continued "
  "sheath and culm growth and temporary storage of non-structural carbohydrates, whereas WOFOST sends all post-anthesis "
  "assimilates to the panicles. We tested whether this can be corrected (Section 3.1): shifting the DVS at which "
  "FOTB reaches 1 by a single calibrated parameter (PART_DELAY) essentially eliminated the stem-mass bias at Bandung "
  "and roughly halved it at the other two sites, and improved the overall normalised RMSE below the ORYZA benchmark. "
  "The corresponding cost is that grain yield, well reproduced by the original Step 1, is 7–9% lower with the delayed "
  "partitioning, because assimilate that used to go to the panicle now goes to the stem. WOFOST cannot resolve this "
  "trade-off the way rice does, by keeping stem carbohydrate as a reserve and remobilising part of it to the grain "
  "during filling " + C("mae1997") + "; it can only choose, at each development stage, how much of the current day's "
  "assimilate to send to each organ. A stem-reserve and remobilisation pool, as implemented in ORYZA2000 and LINTUL3, "
  "would let stem mass and grain yield both match observations, whereas a single partitioning-delay parameter must "
  "trade one against the other; the WOFOST Studio implementation is nonetheless available as PART_DELAY for other "
  "datasets where this trade-off is more favourable, and the full 2016 results with and without it are given in Table S5.")

H("4.3. Why the early N response is still missing", 2)
P(f"In the calibration experiment, the simulated NNI of the 23 kg N ha⁻¹ crop stayed at 1 until about 14 DAT and fell "
  f"to {nni[(23, 28)]:.2f} only at 28 DAT, whereas the observed leaf area was already reduced by "
  f"{100 * (1 - tab_s[23]['rLAI28_obs']):.0f}% at that time. The cause lies on the supply side. The classic N balance releases "
  "indigenous N at a constant daily fraction and adds fertiliser N with a single recovery fraction, so the young crop, "
  "whose demand is small, is fully supplied. In a puddled soil, early N availability is lower for three reasons: ammonium "
  "is immobilised by microbes decomposing incorporated residues, basal and early urea is exposed to ammonia volatilisation "
  "and nitrification–denitrification losses before a root system exists to capture it " + C("buresh2008") + ", and the "
  "root system damaged at transplanting has a limited uptake capacity. Recovery efficiencies of early splits in irrigated "
  "rice are accordingly much lower than those of splits applied at panicle initiation " + C("cassman1998", "peng2006")
  + ". Our single recovery (0.52) is an average over splits and therefore overestimates early supply. Split-specific "
  "recovery, or a mechanistic soil N module such as SNOMIN in PCSE, is the logical next step, but requires soil C and N "
  "data that were not available here.")

H("4.4. Indigenous N supply: stable in time, local in space", 2)
P("Indigenous N supply in flooded rice is the sum of net mineralisation of soil organic N under anaerobic conditions, "
  "biological N fixation by free-living and phototrophic organisms in the floodwater " + C("roger1992") + ", and N in "
  "irrigation water, rain and recycled residues " + C("cassman1998") + ". At a research station these inputs are governed "
  "by a constant water regime, puddling and residue practice, which explains why NSOILBASE calibrated on the 2017/18 "
  "experiment agreed with the values derived independently from the 2020 and 2022 omission plots, and why decades-old "
  "0-N plots still produced 3.3–3.4 t ha⁻¹ of grain dry matter. Across fields, however, the same inputs vary with organic matter quality, legacy "
  "N from past fertilisation " + C("huang2021") + ", drainage and water source; differences in mineralisation potential "
  "between paddy soils alone change rice N supply and the fate of fertiliser N " + C("liu2026") + ". Soil-test classes such as total N capture these differences "
  "poorly (Dobermann et al., 2003a); soil organic carbon predicted indigenous N supply in one temperate region "
  + C("espe2015") + ", but such relations are regional. The failed transfer to farmers' fields that share the station's "
  "\"low N\" soil class is therefore expected and supports the omission-plot approach of site-specific N management "
  + C("Dobermann et al., 2003b", "pampolino2007") + ". Within a site, indigenous supply and fertiliser recovery are "
  f"separable only across a range of N rates: at 23 kg N ha⁻¹ fertiliser adds about {23 * ps['N_recovery']:.0f} kg of "
  f"available N against about {ps['NSOILBASE']:.0f} kg from the soil, so the low rate informs NSOILBASE while the high "
  "rates inform recovery. Without the low rate, any combination giving the same total supply at 115–207 kg N ha⁻¹ fits "
  "equally well " + C("beven2001") + ", which is exactly what the cross-validation showed. The leaf-area response restores "
  "identifiability because it depends on when N deficiency starts, which is governed mainly by indigenous supply; "
  "omission plots and early canopy measurements are therefore complementary rather than redundant.")

P(f"The Karangploso trial adds a spatial data point: the indigenous supply inferred there "
  f"({MAR['std']['NSOILBASE_fit']:.0f}–{MAR['ext']['NSOILBASE_fit']:.0f} kg N ha⁻¹) differs from the "
  "Sukamandi value by 10–20%, consistent with the view that NSOILBASE is a stable property of a field rather than "
  "of a region, and must be re-estimated locally — which a single omission plot suffices to do.")
H("4.5. Sensitivity reflects the N economy of grain filling", 2)
P("At low N, grain yield was most sensitive to leaf life span (SPAN) and to the maximum grain N concentration (NMAXSO). "
  "Both act through the same mechanism: grain filling requires N that, once soil supply is exhausted, must be remobilised "
  "from leaves, which accelerates leaf senescence and shortens the period of canopy photosynthesis – the "
  "\"self-destruction\" of the canopy described by " + PUS["sinclair1975"]["cite"].replace(",", " (") + ") and documented "
  "for rice leaf N remobilisation " + C("mae1997") + ". A higher NMAXSO draws more N from the leaves, whereas a longer SPAN "
  "keeps them photosynthetically active; the two parameters therefore trade off and, at high N, SPAN dominates. Because "
  "NMAXSO was fixed from the literature, measuring grain N concentration at maturity would reduce a major uncertainty. "
  "That the extension parameters affected leaf area only at low N confirms that they act as intended, as stress "
  "responses rather than as additional potential-growth parameters.")

H("4.6. Weather source as a mechanistic uncertainty", 2)
P("Gridded weather products differ from station records, and these differences propagate to simulated yields "
  + C("vanwart2013", "bai2010") + ". Here the two products agreed within 1–5% for most seasons but differed by "
  f"{wst['LTFE 2020']['OM_TMAX'] - wst['LTFE 2020']['NP_TMAX']:.1f} °C in mean maximum temperature for the 2020 dry season. "
  "Temperature affects the simulated crop through three processes: thermal-time accumulation (duration), maintenance "
  "respiration (via Q10) and the temperature reduction of leaf photosynthesis. Scaling TSUM to the known duration removes "
  "the first but not the other two, which explains why the 2020 prediction remained sensitive. On-site weather is "
  "therefore the most cost-effective improvement for any future field evaluation.")

H("4.7. Limitations", 2)
P(f"Although the MCMC chains converged for all stages (split-R̂ ≤ {max(DG['ext']['rhat'].values()):.2f} for the extension; "
  f"Section 3.5, Table S4), the posterior of NLEAF remains wide ({ci('ext', 'NLEAF', f2)}) because NLEAF, NSOILBASE "
  "and N recovery trade off along a ridge of similar likelihood; updating with the Karangploso LAI ratios narrowed it "
  f"to {MARU['NLEAF_sesudah'][1]:.2f} [{MARU['NLEAF_sesudah'][0]:.2f}, {MARU['NLEAF_sesudah'][2]:.2f}] (Section 3.5), and "
  "a larger N-rate dataset, or an independent measurement of the indigenous N supply, would narrow it further. The point estimate and the qualitative conclusion, that the "
  "extension improves the independent leaf-area response, do not depend on this width: they are also supported by the "
  "leave-one-dose-out cross-validation, the blind LTFE prediction and the observation-model robustness check (Table S3). All data are secondary, several were digitised from figures, and no transplanting date was reported; the effects of "
  "these assumptions were quantified but cannot be eliminated. The LTFE validation used Inpari-33 rather than "
  "Inpari-32, although results were robust to eight variety assumptions, and the second validation used Inpari-32 "
  "itself; its control, however, lacked P, K and PGPR, so only its leaf-area and biomass ratios, not its yield "
  "response, are a clean test of the N module. SPAD was available only for 2020 and is a proxy "
  "rather than a measurement of leaf N per area. The NLEAF extension was supported by independent data but rests on three "
  "datasets from one station and should be tested across sites and varieties. Post-anthesis partitioning tables were not "
  "calibrated, which limits stem and harvest-index predictions, and phenology parameters were fixed in the Bayesian "
  "analysis because they were tightly constrained by the reported flowering dates. A dedicated field season with weekly green "
  "LAI and SPAD from 7 to 56 DAT, 0/60/120 kg N ha⁻¹ including an omission plot, grain N at maturity, recorded sowing "
  "and transplanting dates and on-site weather would address most of these limitations.")

H("5. Conclusions")
P("With parameter consistency enforced, WOFOST 8.1 reproduced the N response of grain yield of Indonesian transplanted "
  f"rice and predicted independent omission-plot yields within {max(abs(err0['std']['S2022']), abs(err0['std']['S2020'])):.1f}% "
  "without re-calibration, and indigenous N supply was stable over five years at the calibration station. The standard "
  "model, however, achieves the yield response through the wrong canopy strategy: it dilutes leaf N at constant leaf "
  "area, whereas rice conserves leaf N per area and adjusts leaf area, mainly through leaf size and partly through "
  "tillering. A one-parameter LINTUL3-type extension corrects this strategy and improves the leaf-area response in "
  "independent data. Applications that use canopy variables – remote-sensing assimilation, N diagnosis or canopy "
  "photosynthesis studies – should use such an extension, and indigenous N supply should be measured locally rather than "
  "transferred. All code and data are provided so that these checks can be repeated for other varieties and regions.")

H("Software and data availability")
P("WOFOST Studio (Python 3.12, PCSE 6.0.13, PySide6), the extension module, all datasets extracted from the literature "
  "(with source, table/figure and digitising method for every value), analysis scripts and figure scripts are "
  "available at https://github.com/iwan99gun/wofost-studio-inpari32-n under the MIT licence, and are permanently "
  "archived at Zenodo (version 1.0.0): https://doi.org/10.5281/zenodo.22969839.")
H("CRediT authorship contribution statement")
P("Zainal Arifin: Investigation (literature search and reference compilation), Writing – original draft, Writing – review & editing. "
  "Iwan Gunawan: Software (development of WOFOST Studio and the nitrogen extension), Investigation (literature search and reference compilation), "
  "Writing – original draft, Writing – review & editing.")
H("Declaration of competing interest")
P("The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.")
H("Acknowledgements")
P("The authors thank the laboratory of the Department of Agribusiness, Vocational School, Universitas Sebelas Maret, and the laboratory of the Department of Mechanical Engineering, Universitas Khairun, for their support throughout the completion of this work.")

H("Declaration of generative AI and AI-assisted technologies")
P("During the preparation of this work the authors used generative AI tools to assist in developing the WOFOST Studio "
  "software and analysis scripts, and in drafting and editing the manuscript text. All model formulations, calibration "
  "choices and interpretations were directed and verified by the authors, and every numerical result reported here is "
  "generated by the openly archived scripts. After using this tool, the authors reviewed and edited the content as "
  "needed and take full responsibility for the content of the publication.")

# ================================================================== pustaka
H("References")
REFS = [
    ("Agustiani, N., Deng, N., Edreira, J.I.R., Girsang, S.S., Syafruddin, Sitaresmi, T., Pasuquin, J.M.C., Agus, F., Grassini, P., 2018a. "
     "Simulating rice and maize yield potential in the humid tropical environment of Indonesia. Eur. J. Agron. 101, 10–19. "
     "https://doi.org/10.1016/j.eja.2018.08.002", False),
    ("Agustiani, N., Sujinah, Hikmah, Z.M., 2018b. Kesesuaian cara tanam menurut elevasi pada ekosistem padi sawah irigasi "
     "[Conformity of planting method according to elevation in irrigated rice field]. Penelitian Pertanian Tanaman Pangan 2(3), 145–153. "
     "https://doi.org/10.21082/jpptp.v2n3.2018.p145-153", False),
    ("Berghuijs, H.N.C., Silva, J.V., Reidsma, P., de Wit, A.J.W., 2024. Expanding the WOFOST crop model to explore options for "
     "sustainable nitrogen management: a study for winter wheat in the Netherlands. Eur. J. Agron. 154, 127099.", True),
    ("Bouman, B.A.M., Kropff, M.J., Tuong, T.P., Wopereis, M.C.S., ten Berge, H.F.M., van Laar, H.H., 2001. ORYZA2000: Modeling "
     "Lowland Rice. International Rice Research Institute, Los Baños.", False),
    ("Burnham, K.P., Anderson, D.R., 2002. Model Selection and Multimodel Inference, 2nd ed. Springer, New York.", False),
    ("Cassman, K.G., Dobermann, A., Walters, D.T., 2002. Agroecosystems, nitrogen-use efficiency, and nitrogen management. "
     "Ambio 31, 132–140.", False),
    ("de Wit, A., Boogaard, H., Fumagalli, D., Janssen, S., Knapen, R., van Kraalingen, D., Supit, I., van der Wijngaart, R., "
     "van Diepen, K., 2019. 25 years of the WOFOST cropping systems model. Agric. Syst. 168, 154–167. "
     "https://doi.org/10.1016/j.agsy.2018.06.018", False),
    ("Dobermann, A., Witt, C., Abdulrachman, S., Gines, H.C., Nagarajan, R., Son, T.T., Tan, P.S., Wang, G.H., Chien, N.V., "
     "Thoa, V.T.K., Phung, C.V., Stalin, P., Muthukrishnan, P., Ravi, V., Babu, M., Simbahan, G.C., Adviento, M.A.A., 2003a. "
     "Soil fertility and indigenous nutrient supply in irrigated rice domains of Asia. Agron. J. 95, 913–923. "
     "https://doi.org/10.2134/agronj2003.9130", False),
    ("Dobermann, A., Witt, C., Abdulrachman, S., Gines, H.C., Nagarajan, R., Son, T.T., Tan, P.S., Wang, G.H., Chien, N.V., "
     "Thoa, V.T.K., Phung, C.V., Stalin, P., Muthukrishnan, P., Ravi, V., Babu, M., Simbahan, G.C., Adviento, M.A.A., "
     "Bartolome, V., 2003b. Estimating indigenous nutrient supplies for site-specific nutrient management in irrigated rice. "
     "Agron. J. 95, 924–935. https://doi.org/10.2134/agronj2003.9240", False),
    ("Foreman-Mackey, D., Hogg, D.W., Lang, D., Goodman, J., 2013. emcee: the MCMC hammer. Publ. Astron. Soc. Pac. 125, 306–312.", False),
    ("Gastal, F., Lemaire, G., 2002. N uptake and distribution in crops: an agronomical and ecophysiological perspective. "
     "J. Exp. Bot. 53, 789–799.", False),
    ("Herman, J., Usher, W., 2017. SALib: an open-source Python library for sensitivity analysis. J. Open Source Softw. 2(9), 97.", False),
    ("Hersbach, H., et al., 2020. The ERA5 global reanalysis. Q. J. R. Meteorol. Soc. 146, 1999–2049.", False),
    ("Hikmah, Z.M., Sulistyono, E., Susanti, Z., 2021. Pertumbuhan, hasil dan efisiensi pemakaian air padi Inpari 33 pada "
     "perlakuan pupuk anorganik dan organik [Growth, yield and water use efficiency of Inpari 33 rice to inorganic and organic "
     "fertilizer treatments]. J. Agron. Indonesia 49(3), 242–250. https://doi.org/10.24831/jai.v49i3.38323", False),
    ("Lemaire, G., Jeuffroy, M.-H., Gastal, F., 2008. Diagnosis tool for plant and crop N status in vegetative stage: theory "
     "and practices for crop N management. Eur. J. Agron. 28, 614–624.", False),
    ("Saltelli, A., 2002. Making best use of model evaluations to compute sensitivity indices. Comput. Phys. Commun. 145, 280–297.", False),
    ("Shibu, M.E., Leffelaar, P.A., van Keulen, H., Aggarwal, P.K., 2010. LINTUL3, a simulation model for nitrogen-limited "
     "situations: application to rice. Eur. J. Agron. 32, 255–271. https://doi.org/10.1016/j.eja.2010.01.003", False),
    ("Sobol', I.M., 2001. Global sensitivity indices for nonlinear mathematical models and their Monte Carlo estimates. "
     "Math. Comput. Simul. 55, 271–280.", False),
    ("Sujinah, Hairmansis, A., Sasmita, P., Nugraha, Y., 2020. Hubungan fenologi pertumbuhan tanaman padi dengan hasil gabah, "
     "umur panen, biomasa, dan pengaruh pemupukan [Relationship between rice growth phenology with biomass, maturity, grain "
     "yield, and the effect of fertilization]. Penelitian Pertanian Tanaman Pangan 4(2), 63–71. "
     "https://doi.org/10.21082/jpptp.v4n2.2020.p63-71", False),
    ("Susanti, Z., Hikmah, Z.M., Sastro, Y., Sasmita, P., Sembiring, H., 2023. The combined application of organic and "
     "inorganic fertilizers to improve fertility of degraded soil and sustainable yield in intensive irrigated rice systems. "
     "IOP Conf. Ser.: Earth Environ. Sci. 1165, 012026. https://doi.org/10.1088/1755-1315/1165/1/012026", False),
    ("van Diepen, C.A., Wolf, J., van Keulen, H., Rappoldt, C., 1989. WOFOST: a simulation model of crop production. "
     "Soil Use Manage. 5, 16–24.", False),
    ("van Ittersum, M.K., Cassman, K.G., Grassini, P., Wolf, J., Tittonell, P., Hochman, Z., 2013. Yield gap analysis with "
     "local to global relevance—a review. Field Crops Res. 143, 4–17.", False),
    ("Wallach, D., Makowski, D., Jones, J.W., Brun, F., 2019. Working with Dynamic Crop Models, 3rd ed. Academic Press, London.", False),
]
REFS = [(t, v) for t, v in REFS if not t.startswith("Berghuijs")]
REFS += [(PUS[k]["ref"], False) for k in PUS]
REFS.sort(key=lambda x: x[0].lower().replace("'", ""))
N_REFS = len(REFS)
for txt, v in REFS:
    p = P(txt, verify=v, size=8 if BACA else None); p.paragraph_format.line_spacing = 1.0 if BACA else 1.15
    p.paragraph_format.left_indent = Cm(0.6); p.paragraph_format.first_line_indent = Cm(-0.6)

# ================================================================== lampiran
if BACA:
    set_cols(1, new_page=True)
else:
    doc.add_page_break()
H("Supplementary material")
FIG("FigS1_weather_source", "Fig. S1. Weather-source uncertainty: (a) mean maximum temperature and (b) radiation over "
    "each growing period from Open-Meteo (ERA5) and NASA POWER; (c) resulting yield error for the calibration season "
    "and the blind 0-N predictions.")
FIG("FigS2_variety_assumption", "Fig. S2. Robustness of the independent validation to eight variety assumptions for "
    "Inpari-33: (a) error of the 0-N yield, (b) RMSE of the 0-N/140-N LAI ratios. Filled symbols DS 2022, open symbols 2020.")
TABLE("Table S1. Changes made to the default PCSE 6.0.13 / WOFOST 8.1 set-up in WOFOST Studio.",
      ["Issue", "Default behaviour", "Change", "Effect when disabled"],
      [["RGRLAI_MIN vs RGRLAI", "Absolute RGRLAI_MIN (0.004)", "RGRLAI_MIN = 0.5 × RGRLAI", "N stress accelerates juvenile leaf growth"],
       ["AMAX_REF, KN", "Missing in wofost81 parameter file", "AMAX_REF = max(calibrated AMAXTB); KN = 0.4", "Run fails, or calibrated AMAX ignored"],
       ["N effect on leaf expansion", "Only DVS < 0.2 and LAI < 0.75", "Optional NLEAF extension (Section 2.6)", "No canopy N response after ~20 DAT"],
       ["Flooded paddy", "Free-draining classic water balance", "2 cm irrigation every 2 days", "Artificial dry-season water stress"],
       ["Same-day events", "PCSE error for two events on one day", "Events merged (amounts summed)", "Run fails"],
       ["Post-anthesis partitioning", "FOTB = 1 fixed at DVS 1.2 (no stem-reserve remobilisation)",
        "Optional PART_DELAY shifts FLTB/FSTB/FOTB breakpoints for DVS ≥ 1 jointly (mass-conserving)",
        "Systematic stem-mass underestimation after flowering (Table S5)"]],
      widths=[3.2, 4.0, 4.6, 4.2],
      note="Literature-count search underlying Section 1: OpenAlex API, filter=title_and_abstract.search:WOFOST,"
           "institutions.country_code:BN|KH|ID|LA|MY|MM|PH|SG|TH|TL|VN (https://api.openalex.org/works), accessed 26 September 2026.")
TABLE("Table S2. Benchmark of the Step-1 calibration against ORYZA v3 calibrated on the same experiments by Agustiani et al. (2018a).",
      ["Statistic", "WOFOST 7.2 (this study)", "WOFOST 7.2 + PART_DELAY", "ORYZA v3 (Agustiani et al., 2018a)", "Mean experimental SD"],
      [["RMSE AGB (t ha⁻¹)", f"{ORY['semua']['RMSE_AGB_t']:.2f}", f"{ORY['dengan_PART_DELAY']['RMSE_AGB_t']:.2f}", "1.6", "1.1"],
       ["RMSE stem (t ha⁻¹)", f"{ORY['semua']['RMSE_batang_t']:.2f}", f"{ORY['dengan_PART_DELAY']['RMSE_batang_t']:.2f}", "0.7", "0.6"],
       ["RMSE LAI, green LAI only / all", f"{ORY['tanpa LAI masak']['RMSE_LAI']:.2f} / {ORY['semua']['RMSE_LAI']:.2f}",
        f"{ORY['dengan_PART_DELAY']['RMSE_LAI']:.2f}", "0.5", "0.2"],
       ["Mean normalised RMSE (%)", f"{ORY['tanpa LAI masak']['RMSEn_rata2_pct']:.0f}", f"{ORY['dengan_PART_DELAY']['RMSEn_pct']:.0f}", "23", "–"],
       ["r² AGB / stem / LAI", f"{ORY['semua']['r2']['TAGP']:.2f} / {ORY['semua']['r2']['TWST']:.2f} / {ORY['tanpa LAI masak']['r2']['LAI']:.2f}",
        f"{ORY['dengan_PART_DELAY']['r2']['TAGP']:.2f} / {ORY['dengan_PART_DELAY']['r2']['TWST']:.2f} / {ORY['dengan_PART_DELAY']['r2']['LAI']:.2f}",
        "> 0.93", "–"]],
      widths=[4.0, 3.4, 3.4, 3.6, 2.6],
      note="ORYZA statistics as reported (one observation excluded). WOFOST: 3 sites × 7, 67 and 112 DAT; 'green LAI only' excludes the maturity LAI, which included senescent leaves. "
           "PART_DELAY calibrated jointly with AMAXTB@y, SPAN, TDWI and RGRLAI (Table S5); not propagated to the main N-limited pipeline (Section 3.1).")
TABLE("Table S5. Joint recalibration of Step 1 with the post-anthesis partitioning delay (PART_DELAY).",
      ["Parameter / statistic", "Without PART_DELAY (refit, k = 4)", "With PART_DELAY (k = 5)"],
      [["AMAXTB@y", f"{KP['parameter_A_tanpa_PART_DELAY']['AMAXTB@y']:.3f}", f"{KP['parameter_B_dengan_PART_DELAY']['AMAXTB@y']:.3f}"],
       ["SPAN (d)", f"{KP['parameter_A_tanpa_PART_DELAY']['SPAN']:.1f}", f"{KP['parameter_B_dengan_PART_DELAY']['SPAN']:.1f}"],
       ["TDWI (kg ha⁻¹)", f"{KP['parameter_A_tanpa_PART_DELAY']['TDWI']:.0f}", f"{KP['parameter_B_dengan_PART_DELAY']['TDWI']:.0f}"],
       ["RGRLAI (ha ha⁻¹ d⁻¹)", f"{KP['parameter_A_tanpa_PART_DELAY']['RGRLAI']:.4f}", f"{KP['parameter_B_dengan_PART_DELAY']['RGRLAI']:.4f}"],
       ["PART_DELAY (DVS)", "0 (fixed)", f"{KP['parameter_B_dengan_PART_DELAY']['PART_DELAY']:.2f}"],
       ["SSE (28 obs., LAI+AGB+stem+grain, 3 sites)", f"{KP['SSE_A']:.1f}", f"{KP['SSE_B']:.1f}"],
       ["AICc", f"{KP['AICc_A']:.1f}", f"{KP['AICc_B']:.1f}"]] +
      [[f"{r['lokasi'].capitalize()}: {v} obs / sim (error %)",
        f"{r[f'{v}_obs']} / {r[f'{v}_A_tanpaPD']} ({r[f'{v}_errA_%']:+.1f}%)",
        f"{r[f'{v}_obs']} / {r[f'{v}_B_PART_DELAY']} ({r[f'{v}_errB_%']:+.1f}%)"]
       for r in KP["detail_per_lokasi"] for v in ("TWST", "TWSO")],
      widths=[6.0, 5.5, 5.5], fs=7.5,
      note="TSUM1, TSUM2 and SLATB fixed at their Step-1 values (Table 2) in both refits. Detail rows give stem (TWST) and grain (TWSO) "
           "dry matter at maturity (kg ha⁻¹) per site.")
TABLE("Table S3. Robustness of calibration and independent prediction to the observation model for the ratio data.",
      ["Variant", "Model", "NSOILBASE", "Recovery", "NLEAF", "0-N error 2022 (%)", "0-N error 2020 (%)", "RMSE LAI ratio"],
      [[r["varian"].replace("dasar (sigma x1)", "baseline (σ × 1)").replace("sigma", "σ").replace("tanpa data rasio", "no ratio data"),
        {"std": "8.1", "ext": "8.1+NLEAF"}[r["model"]], f"{r['NSOILBASE']:.0f}", f"{r['N_recovery']:.2f}",
        (f"{r['NLEAF']:.2f}" if "NLEAF" in r else "–"), f"{r['err_Y0_2022']:+.1f}", f"{r['err_Y0_2020']:+.1f}", f"{r['rmse_rasio_LAI']:.2f}"] for r in ROB],
      widths=[3.0, 1.8, 1.8, 1.6, 1.4, 2.2, 2.2, 2.0], fs=8)
TABLE("Table S4. MCMC convergence diagnostics per stage (emcee ensemble sampler).",
      ["Stage", "Walkers × steps", "Burn-in", "Max split-R̂", "Min chain length (τ)", "Min ESS", "Acceptance"],
      [["1: production parameters", f"{POST['tahap1']['n_walker']} × {POST['tahap1']['n_step']}", str(DG['tahap1']['burn']),
        f"{max(DG['tahap1']['rhat'].values()):.2f}", f"{DG['tahap1']['langkah_per_tau']:.0f}", f"{min(DG['tahap1']['ess'].values()):.0f}",
        f"{DG['tahap1']['penerimaan']:.2f}"],
       ["2: WOFOST 8.1 (std)", f"{POST['std']['n_walker']} × {POST['std']['n_step']}", str(DG['std']['burn']),
        f"{max(DG['std']['rhat'].values()):.2f}", f"{DG['std']['langkah_per_tau']:.0f}", f"{min(DG['std']['ess'].values()):.0f}",
        f"{DG['std']['penerimaan']:.2f}"],
       ["2: WOFOST 8.1 + NLEAF (ext)", f"{POST['ext']['n_walker']} × {POST['ext']['n_step']}", str(DG['ext']['burn']),
        f"{max(DG['ext']['rhat'].values()):.2f}", f"{DG['ext']['langkah_per_tau']:.0f}", f"{min(DG['ext']['ess'].values()):.0f}",
        f"{DG['ext']['penerimaan']:.2f}"]],
      widths=[4.5, 2.4, 1.6, 2.2, 2.8, 1.8, 1.8], fs=8,
      note="Split-R̂ computed across walkers treated as chains (Gelman and Rubin, 1992); τ, integrated autocorrelation time; "
           "ESS, effective sample size. A split-R̂ close to 1 and a chain length well above the autocorrelation time indicate "
           "convergence. Stages 1 and 2 (std) used the affine-invariant stretch move; stage 2 (ext) used "
           "differential-evolution moves because of the NLEAF–NSOILBASE–N-recovery ridge (Section 2.9).")

docx_path = OUT / ("Manuscript_EJA.docx" if FINAL else ("draft_WOFOST81_Nrice_WestJava_versi_baca.docx" if BACA else "draft_WOFOST81_Nrice_WestJava.docx"))
doc.save(docx_path)
print("DOCX:", docx_path)
if FINAL:
    raise SystemExit(0)

# ------------------------------------------------------------------ PDF via Microsoft Word
try:
    import win32com.client
    word = win32com.client.DispatchEx("Word.Application"); word.Visible = False; word.DisplayAlerts = 0
    d = word.Documents.Open(str(docx_path.resolve()), ReadOnly=True)
    pdf_path = docx_path.with_suffix(".pdf")
    d.SaveAs2(str(pdf_path.resolve()), FileFormat=17)
    pages = d.ComputeStatistics(2); words = d.ComputeStatistics(0)
    d.Close(False); word.Quit()
    print("PDF:", pdf_path, "| halaman", pages, "| kata", words)
except Exception as e:  # noqa: BLE001
    print("Konversi PDF gagal:", type(e).__name__, e)
