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
POT = J("hasil_kalibrasi_syok_inpari32.json"); N4 = J("hasil_kalibrasi_n4_inpari32.json"); V = J("validasi_ltfe_sukamandi.json")
POST = J("posterior_n_inpari32.json"); SOB = J("sobol_model_final_n.json"); WX = J("sensitivitas_sumber_cuaca.json")
VAR = J("sensitivitas_asumsi_varietas.json")
STD, EXT = N4["Wofost81_NWLP_CWB_CNB"], N4["Wofost81_NWLP_CWB_CNB_NLV"]
ps, pe = STD["parameter"], EXT["parameter"]
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
        q = doc.add_paragraph(); q.paragraph_format.line_spacing = 1.0; rr = q.add_run(note); rr.font.size = Pt(8); rr.italic = True
    doc.add_paragraph()
    if BACA:
        set_cols(2)


# ================================================================== halaman judul
P("DRAFT manuscript generated from WOFOST Studio results on " + dt.date.today().strftime("%d %B %Y")
  + ". Text highlighted in yellow must be verified or completed by the authors before submission.", italic=True, size=9, verify=True)
P("Target journal: European Journal of Agronomy (alternatives: Agricultural Systems; Environmental Modelling & Software).", italic=True, size=9)
TITLE = ("Nitrogen-limited WOFOST 8.1 for tropical transplanted rice: parameter-consistency fixes, a leaf-level "
         "nitrogen extension and independent omission-plot validation in West Java, Indonesia")
P(TITLE, bold=True, size=15, align=WD_ALIGN_PARAGRAPH.CENTER)
P("[Author 1]ᵃ*, [Author 2]ᵇ, [Author 3]ᵃ", align=WD_ALIGN_PARAGRAPH.CENTER, verify=True)
P("ᵃ [Affiliation, address, country]\nᵇ [Affiliation, address, country]\n* Corresponding author: [e-mail]", size=9.5, align=WD_ALIGN_PARAGRAPH.CENTER, verify=True)

H("Highlights")
for h in ("WOFOST 8.1 was evaluated for Indonesian inbred rice with literature-mined data",
          "Three parameter-consistency problems were found in the default WOFOST 8.1 setup",
          f"Blind prediction of independent 0-N omission plots was within {max(abs(err0['std']['S2022']), abs(err0['std']['S2020'])):.1f}% error",
          "Indigenous soil N supply was stable over five years at the calibration station",
          f"A one-parameter leaf-N extension cut the LAI-response RMSE from {rm['std']:.2f} to {rm['ext']:.2f}"):
    P("• " + h)

H("Abstract")
P("Process-based crop models are increasingly used to evaluate nitrogen (N) management and yield gaps in tropical rice "
  "systems, yet N-limited versions of widely used models are rarely evaluated in humid tropical Asia and their "
  "implementations are seldom checked for internal consistency. We evaluated WOFOST 8.1 (PCSE 6.0.13) for the modern "
  "Indonesian inbred rice Inpari-32 using literature-mined data from West Java, Indonesia. Potential-production parameters "
  "were calibrated against three dry-season 2016 experiments, and N-supply parameters against an N-rate experiment (23, "
  "115 and 207 kg N ha⁻¹) at Sukamandi. Evaluation combined leave-one-dose-out cross-validation, Bayesian (MCMC) "
  "inference, Sobol sensitivity analysis and a blind prediction of two independent seasons of N-omission plots from a "
  "long-term fertility experiment (LTFE) at the same station. Three consistency problems were found in the default "
  "implementation: a recalibrated RGRLAI below the default RGRLAI_MIN makes N stress accelerate juvenile leaf growth; "
  "the calibrated AMAXTB is ignored because WOFOST 8.1 uses AMAX_REF; and N stress acts on sink-limited leaf expansion "
  f"only when DVS < 0.2 and LAI < 0.75, although the simulated N nutrition index of the low-N crop fell to "
  f"{nni[(23, 35)]:.2f} by 35 days after transplanting. After correction, the model reproduced grain yield across N rates "
  f"(cross-validated RMSE {100 * STD['rmse_lodo']['TWSO'] / 5716:.1f}%) and predicted the 0-N yields of both LTFE seasons "
  f"within {abs(err0['std']['S2022']):.1f}–{abs(err0['std']['S2020']):.1f}% without re-calibration. Indigenous N supply "
  f"estimated from the omission plots ({f1(nsbB['S2022'])} and {f1(nsbB['S2020'])} kg N ha⁻¹) matched the calibrated "
  f"value ({f1(ps['NSOILBASE'])} kg N ha⁻¹). The standard model did not reproduce the observed reduction of leaf area "
  f"under N deficiency (0-N/140-N LAI ratio {min(o22['rLAI60'], o20['rLAIFL']):.2f}–{max(o22['rLAI21'], o20['rLAI21']):.2f} "
  f"observed). A one-parameter LINTUL3-type extension applying N stress to specific leaf area and exponential-phase leaf "
  f"expansion reduced the RMSE of this ratio from {rm['std']:.2f} to {rm['ext']:.2f}, with similar AICc on the "
  f"calibration data ({STD['AICc']:.2f} vs {EXT['AICc']:.2f}). Indigenous N supply was not transferable to farmers' "
  f"fields 30–75 km away, where yields were underestimated by {abs(TR['indramayu']['err_126N_pct']):.0f}–"
  f"{abs(TR['subang']['err_126N_pct']):.0f}%. WOFOST 8.1 is suitable for N-response analysis of tropical transplanted rice "
  "once parameter consistency is enforced, canopy-level N responses need a structural extension, and indigenous N supply "
  "must be measured locally.")
PR([("Keywords: ", "b"), ("crop model; WOFOST; nitrogen nutrition index; indigenous nitrogen supply; omission plot; "
                          "Bayesian calibration; Oryza sativa; Indonesia", "")])
if BACA:
    for par in doc.paragraphs[-2:-1]:
        pPr = par._p.get_or_add_pPr(); shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), "EEF2F6"); pPr.append(shd)
    set_cols(2)

# ================================================================== 1 Introduction
H("1. Introduction")
P("Rice is the staple food of Indonesia, and irrigated lowlands of Java supply a large share of national production. "
  "Nitrogen (N) is the nutrient that most limits rice yield in these systems, while farmer N rates and N-use efficiency "
  "vary widely (Cassman et al., 2002; Dobermann et al., 2003a). Process-based crop models are the standard tool for "
  "exploring N management, yield gaps and climate impacts beyond the range of field trials (van Ittersum et al., 2013), "
  "but their value depends on calibration and on independent evaluation against data that were not used for fitting "
  "(Wallach et al., 2019).")
PR([("WOFOST is one of the most widely used crop growth models (van Diepen et al., 1989; de Wit et al., 2019). Its "
     "Python implementation PCSE now includes WOFOST 8.1, which couples crop growth to soil and crop N balances and "
     "makes leaf photosynthesis depend on specific leaf N (Berghuijs et al., 2024). ", ""),
    ("Applications of WOFOST in tropical Southeast Asia remain scarce; a Scopus search returned eight documents for "
     "this region (search string and date to be reported)", "v"),
    (", and we are not aware of an evaluation of WOFOST 8.1 for transplanted tropical rice. For rice, ORYZA2000 "
     "(Bouman et al., 2001) and LINTUL3 (Shibu et al., 2010) are the reference N-limited models, and both represent N "
     "effects on leaf area that WOFOST 7.x did not simulate.", "")])
P("Two obstacles hamper such evaluations. First, experimental data with the detail required for calibration (dates, "
  "leaf area and biomass time series, N treatments) are rarely publicly available in Indonesia, so modellers have to "
  "reconstruct datasets from published tables and figures. Second, recalibrating a subset of parameters of a complex "
  "model can silently create inconsistencies with parameters that were left at their defaults, particularly when a "
  "newer model version replaces some parameters by others. Both issues are seldom reported, yet both affect the "
  "credibility of model-based N recommendations.")
P("Here we calibrate and evaluate WOFOST 8.1 for the modern inbred rice variety Inpari-32 in West Java using only "
  "literature-mined data, with an open desktop tool (WOFOST Studio) that wraps PCSE. The objectives were (i) to identify "
  "and correct parameter-consistency problems that arise when WOFOST 8.1 is recalibrated for tropical rice; (ii) to test "
  "whether the standard model reproduces the observed N response of yield, biomass and leaf area, and whether a minimal "
  "LINTUL3-type extension improves it; and (iii) to evaluate the calibrated N supply by blind prediction of independent "
  "N-omission plots, with explicit quantification of parameter, weather and variety uncertainty.")

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
  "pixel level with axis calibration on four major ticks; the digitising error (±3 px) was combined with the reported "
  "experimental standard deviation to weight observations. Transplanting dates were not reported for any dataset and "
  "were assumed (1 May 2016; 22 November 2017; 1 May 2022; 2 August 2020); the sensitivity of all results to ±21 days "
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
        "Grain; leaf area at 21/35 DAT and flowering", "Independent validation"]],
      widths=[3.0, 3.0, 1.8, 2.8, 4.0, 2.0],
      note="DS, dry season; WS, wet season; DAT, days after transplanting; AGB, above-ground biomass; LTFE, long-term fertility experiment (since 1994).")

H("2.3. Weather and soil", 2)
P("Daily weather was taken from Open-Meteo (ERA5-based reanalysis; Hersbach et al., 2020) at each site; NASA POWER was "
  "used as an alternative source to quantify weather uncertainty. Soils were parameterised as clayey paddy soils "
  "(field capacity 0.42, wilting point 0.22 m³ m⁻³) with a 5 cm surface storage.")

H("2.4. Step 1: potential production", 2)
P(f"Phenology (TSUM1, TSUM2) was fitted to the reported flowering and maturity dates. Growth parameters (AMAXTB@y, SPAN, "
  f"TDWI, RGRLAI) were fitted jointly to the three 2016 experiments by weighted least squares with multi-start "
  f"optimisation, while the specific leaf area multipliers were fixed at literature-consistent values "
  f"(SLATB@ya = {POT['parameter']['SLATB@ya']}, SLATB@yb = {POT['parameter']['SLATB@yb']}) because free calibration "
  f"drove SLA to its lower bound. Leaf area at maturity measured with a canopy analyser includes senescent leaves and "
  f"was given a large uncertainty because WOFOST simulates green LAI only.")

H("2.5. Step 2: parameter consistency in WOFOST 8.1", 2)
P("Three problems were identified while moving the calibrated crop to WOFOST 8.1, and corrected in WOFOST Studio.")
P("(i) Juvenile N effect. PCSE reduces juvenile leaf expansion by RFRGRL = 1 − (1 − I)(RGRLAI − RGRLAI_MIN)/RGRLAI, where "
  "I is an index of leaf N concentration. The recalibrated RGRLAI (0.0035) is lower than the default RGRLAI_MIN (0.004), "
  "which turns RFRGRL above 1 so that N stress accelerates leaf growth. RGRLAI_MIN was therefore expressed as a fraction "
  "of RGRLAI (RGRLAI_MIN_FR = 0.5, the ratio of the IR72 defaults).")
P("(ii) Photosynthesis. WOFOST 8.1 computes maximum leaf photosynthesis from AMAX_REF and specific leaf N and does not "
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
P(f"Crop parameters from Step 1 were kept fixed. Indigenous soil N supply (NSOILBASE, released at a constant "
  f"NSOILBASE_FR = 0.01 d⁻¹, i.e. evenly over the season) and fertiliser N recovery were calibrated for both model "
  f"versions, plus NLEAF for the extension. Maximum grain N concentration was fixed at 0.0144 kg N kg⁻¹ and initial "
  f"mineral N at zero; urea was split equally at 7, 28 and 42 DAT. The objective used {STD['n_obs']} observations: grain "
  "yield and AGB at maturity of Inpari-32 at the three N rates (weights 1/(CV·obs), CV 8.75% and 16.8%), and eight "
  "relative responses (23/115 and 207/115 ratios of leaf area and biomass at 28 DAT and flowering) derived from the "
  "dose main effects over six genotypes. Because the dose × genotype interaction was significant, ratio errors were "
  "set conservatively to √2 × plot CV. Using ratios removes the bias in the absolute early LAI (Section 4.4) from the "
  "N-response signal. Models were compared with the small-sample Akaike criterion (AICc; Burnham and Anderson, 2002).")

H("2.8. Evaluation", 2)
P("Internal evaluation used leave-one-dose-out (LODO) cross-validation: each N rate was predicted after re-calibrating "
  "on the other two. Independent evaluation used the LTFE seasons (Table 1) in two stages: (A) blind prediction with the "
  "calibrated parameters, and (B) estimation of NSOILBASE from the 0-N yield alone, following the omission-plot "
  "principle (Dobermann et al., 2003b), followed by prediction of the 140-N yield and of the 0-N/140-N ratios of LAI and "
  "biomass. Inpari-33 phenology (107 days after sowing versus 120 for Inpari-32) was represented by scaling TSUM1 and "
  "TSUM2 so that simulated duration matched the variety description. Transfer to the farmers' fields of the 2016 "
  "experiments (126 kg N ha⁻¹) was also tested.")

H("2.9. Uncertainty and sensitivity", 2)
P("Posterior distributions of the N parameters were sampled with the affine-invariant ensemble sampler emcee "
  "(Foreman-Mackey et al., 2013; 16 walkers, 120 steps, 40 burn-in, integrated autocorrelation time 4–8 steps) using "
  "the same likelihood, and 32 posterior draws were propagated to the LTFE predictions. Global sensitivity of grain yield "
  "and maximum LAI to 11 parameters was quantified with Sobol indices (Sobol', 2001; Saltelli, 2002) as implemented in "
  "SALib (Herman and Usher, 2017; N = 128, bootstrap confidence intervals) at 23 and 207 kg N ha⁻¹. Weather uncertainty "
  "was assessed by repeating key simulations with NASA POWER, and variety uncertainty by eight variants of phenology "
  "(±10%, unscaled Inpari-32), AMAX (±10%) and SLA (±10%).")

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
  "to ±30 days changed simulated flowering by 1–2 days after transplanting and yield by up to 10%.")
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
  f"flowering biomass ratio more closely, at a small cost in grain yield fit (LODO RMSE {f0(EXT['rmse_lodo']['TWSO'])} "
  f"kg ha⁻¹). The two versions had similar support (AICc {STD['AICc']:.2f} vs {EXT['AICc']:.2f}). Neither reproduced "
  f"the 28-DAT leaf area ratio ({tab_s[23]['rLAI28_obs']:.2f} observed; {tab_s[23]['rLAI28_sim']:.2f} and "
  f"{tab_e[23]['rLAI28_sim']:.2f} simulated).")
FIG("Fig3_N_response", "Fig. 3. Response of Inpari-32 to N rate at Sukamandi, wet season 2017/18: (a) grain yield, "
    "(b) above-ground biomass at maturity, (c) LAI at flowering relative to 115 kg N ha⁻¹ (observations are dose main "
    "effects across six genotypes). Error bars: ±1 SD (a, b) and the conservative ratio error (c).")
TABLE("Table 2. Calibrated parameters. Posterior medians and 95% credible intervals from MCMC are given for the N parameters.",
      ["Parameter", "Unit", "Value", "Basis"],
      [["TSUM1 / TSUM2", "°C d", f"{f0(POT['parameter']['TSUM1'])} / {f0(POT['parameter']['TSUM2'])}", "Step 1 (DS 2016)"],
       ["SLATB@ya / SLATB@yb", "–", f"{POT['parameter']['SLATB@ya']} / {POT['parameter']['SLATB@yb']}", "Literature-constrained"],
       ["AMAXTB@y (→ AMAX_REF)", "– (kg CO₂ ha⁻¹ h⁻¹)", f"{f2(POT['parameter']['AMAXTB@y'])} (36.1)", "Step 1"],
       ["SPAN", "d", f1(POT["parameter"]["SPAN"]), "Step 1"],
       ["TDWI", "kg ha⁻¹", f0(POT["parameter"]["TDWI"]), "Step 1"],
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
  f"of the six ratios from {rm['std']:.2f} to {rm['ext']:.2f}; in 2022 all LAI ratios, the 60-DAT biomass ratio and the "
  "yield ratio fell within its 95% predictive intervals, whereas none of the LAI ratios did for the standard model.")
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
P(f"At the three farmers' fields of 2016, the Sukamandi N supply led to yield underestimates of "
  f"{abs(TR['subang']['err_126N_pct']):.0f}% (Subang) and {abs(TR['indramayu']['err_126N_pct']):.0f}% (Indramayu), "
  f"whereas N-saturated runs were within {abs(TR['subang']['err_jenuh_pct']):.1f}% and "
  f"{abs(TR['indramayu']['err_jenuh_pct']):.1f}%. All four locations were classified as low in soil N in the source "
  "publications, so soil tests did not explain the difference.")

H("3.5. Uncertainty and sensitivity", 2)
P(f"The posterior of NSOILBASE was bounded by the prior range (95% interval {ci('std', 'NSOILBASE')} kg N ha⁻¹ for the "
  f"standard model) and N recovery was weakly constrained ({ci('std', 'N_recovery', f2)}), reflecting their correlation "
  f"with only three N rates (Table 2). NLEAF was constrained to {ci('ext', 'NLEAF', f2)}. At 23 kg N ha⁻¹, grain yield "
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

# ================================================================== 4 Discussion
H("4. Discussion")
H("4.1. Parameter consistency is a prerequisite for recalibrating WOFOST 8.1", 2)
P("The three problems in Section 2.5 are not errors in the WOFOST 8.1 equations but interactions between recalibrated "
  "and default parameters, and between model versions. They are nevertheless consequential: problem (i) reverses the sign "
  "of a stress response, problem (ii) removed a 10% photosynthesis correction without warning, and problem (iii) "
  "determines whether early N deficiency can affect the canopy at all. Such problems are likely whenever a model is "
  "moved to a crop type (transplanted, fast early growth) or version for which the default parameter set was not "
  "designed. We recommend that N-limited WOFOST applications report RGRLAI_MIN relative to RGRLAI, the AMAX_REF used, and "
  "the timing of N stress relative to the juvenile window.")
H("4.2. Canopy N response requires a structural extension", 2)
P("Grain yield alone did not discriminate between the model versions: both reproduced yield within measurement error, "
  "and AICc on the calibration data was similar. The discriminating evidence came from leaf area, where the standard "
  "model consistently predicted almost no N effect in three independent datasets, whereas N-deficient rice reduces leaf "
  "expansion and specific leaf area (Gastal and Lemaire, 2002). The LINTUL3-type extension adds a single parameter, "
  "reproduces WOFOST 8.1 when set to zero, affects only N-stressed crops (Fig. 6), and improved the canopy response in "
  "data not used for calibration. This matters for applications that assimilate remotely sensed LAI or use canopy "
  "variables to diagnose N status, where the standard model would attribute low LAI to causes other than N.")
H("4.3. Indigenous N supply: stable in time, local in space", 2)
P("The agreement between NSOILBASE calibrated on the 2017/18 N-rate experiment and that derived independently from the "
  "2020 and 2022 omission plots supports the temporal stability of indigenous N supply at Sukamandi, in line with the "
  "omission-plot concept of Dobermann et al. (2003b). The failed spatial transfer to farmers' fields shows the opposite "
  "side: indigenous N supply differs among fields that share the same soil-test class, as also reported across Asian "
  "rice domains (Dobermann et al., 2003a). For regional applications, NSOILBASE should therefore be estimated from "
  "local omission plots or treated as an uncertain input, rather than transferred from a research station.")
H("4.4. Limitations", 2)
P("All data are secondary, several were digitised from figures, and no transplanting date was reported; the effects of "
  "these assumptions were quantified but cannot be eliminated. The independent validation used Inpari-33 rather than "
  "Inpari-32, although results were robust to eight variety assumptions. The early (28 DAT) leaf-area response at the "
  "calibration site was not reproduced because the classic N balance releases soil N at a constant rate; a mechanistic "
  "soil N module (e.g. SNOMIN in PCSE) would require soil C and N data that were not available. NMAXSO was fixed from "
  "the literature although it strongly influenced yield at low N. Weather came from reanalysis products whose "
  "differences were large in one season; station data would reduce this uncertainty. A dedicated field season with "
  "weekly green LAI from 7 to 56 DAT, 0/60/120 kg N ha⁻¹ including an omission plot, recorded sowing and transplanting "
  "dates, and on-site weather would address most of these limitations.")

H("5. Conclusions")
P("With parameter consistency enforced, WOFOST 8.1 reproduced the N response of grain yield of Indonesian transplanted "
  "rice and predicted independent omission-plot yields within 2.1% without re-calibration. Indigenous N supply was "
  "stable over five years at the calibration station but not transferable to other fields. The standard model does not "
  "reproduce the reduction of leaf area under N deficiency; a one-parameter LINTUL3-type extension corrects this and "
  "is recommended when canopy variables matter. All code and data are provided so that these checks can be repeated "
  "for other varieties and regions.")

H("Software and data availability")
P("WOFOST Studio (Python 3.12, PCSE 6.0.13, PySide6), the extension module, all datasets extracted from the literature "
  "(with source, table/figure and digitising method for every value), analysis scripts and figure scripts will be "
  "deposited in a public repository with a DOI upon acceptance: [repository URL / Zenodo DOI].", verify=True)
H("CRediT authorship contribution statement")
P("[To be completed by the authors.]", verify=True)
H("Declaration of competing interest")
P("[To be completed by the authors.]", verify=True)
H("Acknowledgements")
P("[To be completed by the authors.]", verify=True)

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
       ["Same-day events", "PCSE error for two events on one day", "Events merged (amounts summed)", "Run fails"]],
      widths=[3.2, 4.0, 4.6, 4.2])

docx_path = OUT / ("draft_WOFOST81_Nrice_WestJava_versi_baca.docx" if BACA else "draft_WOFOST81_Nrice_WestJava.docx")
doc.save(docx_path)
print("DOCX:", docx_path)

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
