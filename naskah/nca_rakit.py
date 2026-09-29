# -*- coding: utf-8 -*-
"""Perakit naskah versi Nutrient Cycling in Agroecosystems (Springer).
DIJALANKAN DI DALAM namespace buat_naskah.py (python buat_naskah.py nca): semua angka/variabel dan BLOCKS tersedia.

Syarat jurnal yang dipenuhi di sini (Submission guidelines, dibaca 29 Sep 2026):
  judul <= 90 karakter tanpa lokasi; abstrak 150-250 kata tanpa singkatan tak terdefinisi; 4-6 kata kunci;
  <= 7000 kata (tanpa pustaka); 4-8 gambar+tabel di teks utama; spasi ganda, 12 pt, nomor halaman & nomor baris;
  tabel di badan teks; keterangan gambar di badan teks, gambar di lembar terpisah di akhir;
  sitasi (Nama Tahun) tanpa koma; daftar pustaka gaya Springer Basic; subjudul diskusi menyatakan temuan;
  bagian 'Statements and Declarations'; penggunaan AI generatif didokumentasikan di Metode;
  daftar pustaka hanya memuat yang disitasi di teks utama (pustaka suplemen punya daftar sendiri).
Keluaran: naskah/nca/NCA_Manuscript.docx, NCA_Supplementary_Information.docx, gambar Fig1-3 + ESM, laporan."""
import re, shutil
from collections import OrderedDict

NCA_DIR = OUT / "nca"
NCA_DIR.mkdir(exist_ok=True)

TITLE_NCA = "Leaf-area plasticity and indigenous nitrogen supply in nitrogen-limited WOFOST for rice"
assert len(TITLE_NCA) <= 90, len(TITLE_NCA)

# ------------------------------------------------------------------ 1. kelompokkan blok per bagian
SECS = OrderedDict(); _cur = "FRONT"; SECS[_cur] = []
for b in BLOCKS:
    if b[0] == "H":
        _cur = b[1]; SECS[_cur] = []
    else:
        SECS[_cur].append(b)


def PT(name, i=None):
    """Teks paragraf ke-i (atau semua paragraf) dari bagian asli."""
    ps_ = [b[1] for b in SECS[name] if b[0] == "P"]
    return ps_ if i is None else ps_[i]


def BL(name, kind):
    return [b for b in SECS[name] if b[0] == kind]


# ------------------------------------------------------------------ 2. transformasi teks
FIGMAP = {"1": "S1", "2": "S2", "3": "1", "4": "2", "5": "3", "6": "S3", "S1": "S4", "S2": "S5"}
TABMAP = {"3": "S6", "4": "3", "5": "4", "6": "5"}
SECMAP = {"4.7": "4.5"}


def renum(t):
    t = re.sub(r"(?<!\d{4}, )\bFig\. (S?\d+)", lambda m: "Fig. " + FIGMAP.get(m.group(1), m.group(1)), t)
    t = re.sub(r"(?<!\d{4}, )\bTable (S?\d+)", lambda m: "Table " + TABMAP.get(m.group(1), m.group(1)), t)
    t = re.sub(r"(Sections? (?:\d\.\d+, )?)4\.7", lambda m: m.group(1) + "4.5", t)
    return t


_CIT = re.compile(r"(?<=[A-Za-zÀ-ɏ\.'’]), (?=(?:19|20)\d{2}[a-z]?(?:\b|[,;)]))")
CIT_LOG = []


def cit(t):
    for m in _CIT.finditer(t):
        CIT_LOG.append(t[max(0, m.start() - 28):m.end() + 6])
    return _CIT.sub(" ", t)


def T(t):
    t = cit(renum(str(t)))
    return re.sub(r"(?<![\w.–\-])-(?=\d)", "−", t)      # tanda minus tipografis untuk bilangan negatif


# ------------------------------------------------------------------ 3. teks baru / ringkas (semua angka dari variabel)
ABSTRACT_NCA = (
    "Nitrogen (N)-limited crop models increasingly guide fertiliser management in irrigated rice, but their N modules are "
    "rarely tested for internal consistency or against independent N-omission data. We evaluated the N-limited crop model "
    "WOFOST 8.1 for transplanted tropical rice with published field data only: three near-potential experiments, an N-rate "
    "trial (23–207 kg N ha⁻¹), two seasons of 0-N omission plots in a long-term fertility experiment, and an "
    "independent N-rate trial at a second site. Recalibration exposed three parameter inconsistencies that inverted or "
    "disabled the simulated N response of leaf growth and photosynthesis. After correction, the model reproduced grain yield "
    f"at all N rates (error ≤{cal_err:.0f}%) and predicted the omission-plot yields blind within "
    f"{max(abs(err0['std']['S2022']), abs(err0['std']['S2020'])):.1f}%. Indigenous soil N supply inferred from the omission "
    f"plots ({nsbB['S2022']:.0f}–{nsbB['S2020']:.0f} kg N ha⁻¹) matched the value calibrated five years earlier "
    f"({ps['NSOILBASE']:.0f} kg N ha⁻¹), but was lower at the second site "
    f"({MAR['std']['NSOILBASE_fit']:.0f}–{MAR['ext']['NSOILBASE_fit']:.0f} kg N ha⁻¹) and did not transfer to "
    f"farmers' fields. N-deficient rice conserved leaf N per unit area (leaf greenness −{min(spad_red):.0f} to "
    f"−{max(spad_red):.0f}%; tissue N −{100 * (1 - mar_nj0 / mar_njF):.0f}%) and reduced leaf area by "
    f"{min(lai_red_obs):.0f}–{max(lai_red_obs):.0f}%, whereas the model kept leaf area and diluted leaf N by "
    f"{min(sln_red_std):.0f}–{max(sln_red_std):.0f}%. A one-parameter extension that lets N deficiency reduce leaf "
    "expansion and specific leaf area reproduced the leaf-area response in both independent datasets (root mean square "
    f"error of leaf-area ratios {rm['ext']:.2f} versus {rm['std']:.2f}, and {mar_rmse['ext']:.2f} versus "
    f"{mar_rmse['std']:.2f}). Yield alone cannot validate an N module: canopy variables and locally measured indigenous N "
    "supply are required.")
N_ABS_NCA = len(ABSTRACT_NCA.split())
assert 150 <= N_ABS_NCA <= 245, N_ABS_NCA
KEYWORDS_NCA = ["Crop model", "Indigenous nitrogen supply", "Nitrogen omission plot", "Leaf area plasticity",
                "Fertiliser nitrogen recovery", "Bayesian calibration"]
assert 4 <= len(KEYWORDS_NCA) <= 6

# --- Pendahuluan
_intro = PT("1. Introduction")
_intro[0] = _intro[0].replace(
    "Rice is the staple food of Indonesia, and the irrigated lowlands of Java supply a large share of national production. "
    "Nitrogen (N) is the nutrient that most often limits rice yield in these systems",
    "Irrigated lowland rice is the main staple of tropical Asia, and nitrogen (N) is the nutrient that most often limits "
    "its yield")
assert "main staple" in _intro[0]
_intro[1] = re.sub(r"an OpenAlex search for works.*?\(search filter given in Table S1\)",
                   "an OpenAlex search for WOFOST studies with authors from tropical Southeast Asia (accessed 26 September "
                   "2026) returned four distinct works, three of them on rice " + C("wanthanaporn2024").replace(")", "")
                   + "; search filter in Table S1)", _intro[1], flags=re.S)
assert "four distinct works, three" in _intro[1]
_intro[4] = _intro[4] + (
    " We hypothesised that (H1) rice responds to N deficiency mainly by reducing leaf area while conserving leaf N per unit "
    "area, so that a model that dilutes leaf N at constant leaf area can reproduce yield but not canopy variables; and (H2) "
    "indigenous N supply is a stable property of a field that can be estimated from a single omission plot but cannot be "
    "transferred between fields.")

# --- Metode
_m21 = PT("2.1. Modelling framework", 0).replace(
    "a PySide6 application developed for this study that provides model runs, sowing-date batches, Morris/Sobol/eFAST "
    "sensitivity analysis, least-squares and MCMC calibration, ensemble Kalman filtering and climate scenarios (Fig. 1)",
    "an open-source desktop application developed for this study (Fig. 1)")
assert "open-source desktop application" in _m21
_m24_full = PT("2.4. Step 1: potential production", 0)
_k = _m24_full.index(" WOFOST allocates all post-anthesis")
_m24 = _m24_full[:_k] + (
    " Because WOFOST allocates all post-anthesis assimilate to the storage organ whereas rice stems keep growing after "
    "flowering, an optional parameter that delays this switch (PART_DELAY) was also tested; it is described and evaluated "
    "in Supplementary Text S1.")
_m29 = (
    "Parameter uncertainty was quantified by staged Bayesian inference with the ensemble sampler emcee "
    + C("goodman2010").replace(")", "") + "; Foreman-Mackey et al., 2013), as in Bayesian calibration of rice models "
    + C("iizumi2009") + ". Stage 1 sampled AMAXTB@y, SPAN, TDWI and RGRLAI against the 2016 data with uniform priors. Its "
    "posterior of SPAN and AMAXTB@y, the two potential-production parameters with the largest Sobol indices, was "
    "approximated by a bivariate normal distribution and used as the prior in stage 2, which sampled them jointly with the "
    "N parameters, so that uncertainty from Step 1 was propagated to the N parameters and predictions. Convergence was "
    "assessed with split-R̂ computed across walkers " + C("gelman1992") + ", the integrated autocorrelation time and the "
    "effective sample size (sampler settings and diagnostics in Supplementary Text S2 and Table S4). Sixty-four posterior "
    "draws were propagated to both independent datasets, and predictive skill was scored with the continuous ranked "
    "probability score (CRPS) and the coverage of 95% intervals " + C("gneiting2007") + ". The posterior of the extension "
    "was then updated with the three Karangploso LAI ratios by importance sampling (sequential Bayesian updating). "
    "Robustness to the observation model was tested by recalibrating with the ratio errors halved, doubled, or without "
    "ratio data. Global sensitivity of grain yield and maximum LAI to 11 parameters was quantified with Sobol indices "
    "(Sobol', 2001; Saltelli, 2002) as implemented in SALib (Herman and Usher, 2017; N = 128) at 23 and 207 kg N "
    "ha⁻¹. Weather uncertainty was assessed by repeating key simulations with NASA POWER, and variety uncertainty "
    "by eight variants of phenology (±10%, unscaled Inpari-32), AMAX (±10%) and SLA (±10%).")
_m211 = (
    "Generative artificial-intelligence tools (large language models) were used to assist in developing the WOFOST Studio "
    "software and the analysis scripts, and in drafting and editing the text of this article. All model formulations, "
    "calibration choices and interpretations were directed and verified by the authors, every numerical result is "
    "generated by the openly archived scripts, and the authors take full responsibility for the content.")

# --- Hasil
_r31 = (
    f"The calibrated potential model (TSUM1 {f0(POT['parameter']['TSUM1'])} and TSUM2 {f0(POT['parameter']['TSUM2'])} °C d, "
    f"SPAN {f1(POT['parameter']['SPAN'])} d, TDWI {f0(POT['parameter']['TDWI'])} kg ha⁻¹, AMAXTB multiplier "
    f"{f2(POT['parameter']['AMAXTB@y'])}) reproduced LAI at flowering with a normalised RMSE of "
    f"{m('subang', 'LAI', 'nRMSE_%'):.0f}–{m('bandung', 'LAI', 'nRMSE_%'):.0f}% and above-ground biomass (AGB) with "
    f"{m('bandung', 'TAGP', 'nRMSE_%'):.0f}–{m('subang', 'TAGP', 'nRMSE_%'):.0f}% (Fig. 2). Grain yield was within "
    f"{m('subang', 'TWSO', 'nRMSE_%'):.1f}% at Subang and {m('indramayu', 'TWSO', 'nRMSE_%'):.1f}% at Indramayu, but "
    f"overestimated by {m('bandung', 'TWSO', 'nRMSE_%'):.0f}% at the highland site Bandung, where the source study reported "
    "water stress during grain filling that a potential-production run cannot represent. Compared with ORYZA v3 calibrated "
    "on the same experiments (Agustiani et al., 2018a), WOFOST had a lower RMSE for AGB "
    f"({ORY['semua']['RMSE_AGB_t']:.1f} vs 1.6 t ha⁻¹) and the same mean normalised RMSE "
    f"({ORY['tanpa LAI masak']['RMSEn_rata2_pct']:.0f}% vs 23%), but a larger stem RMSE "
    f"({ORY['semua']['RMSE_batang_t']:.1f} vs 0.7 t ha⁻¹; Table S2), because simulated stem mass levelled off after "
    "flowering. Delaying post-anthesis partitioning (PART_DELAY) removed most of this bias (AICc reduced by "
    f"{KP['AICc_A'] - KP['AICc_B']:.0f}) at the cost of a 7–9% lower grain yield; repeating the N calibration and the "
    "blind prediction with this alternative baseline left the conclusions on indigenous N supply and leaf area unchanged "
    "(Supplementary Text S1; Table S5).")
_r35_full = PT("3.5. Uncertainty and sensitivity")
_k = _r35_full[0].index("Stage 1 constrained SPAN")
_r35a = (f"All chains converged (split-R̂ ≤ {rhat_max:.2f}; Table S4; Supplementary Text S2). " + _r35_full[0][_k:])

# --- Diskusi
_d42 = PT("4.2. Two canopy strategies: why yield alone cannot validate the N module")
_k = _d42[2].index("The benchmark against ORYZA points to")
_d42c = _d42[2][:_k] + (
    "The same feature causes the underestimation of stem mass after flowering, which a partitioning delay can remove only "
    "by trading it against grain yield (Supplementary Text S1); a stem-reserve pool with remobilisation to the grain "
    + C("mae1997") + ", as implemented in ORYZA2000 and LINTUL3, would resolve both.")

_lim = PT("4.7. Limitations", 0)

# ------------------------------------------------------------------ 4. susunan naskah utama
MAIN = []
_A_SIMPAN = A            # 'A' di buat_naskah.py = hasil LTFE; dipakai sementara sebagai alias append lalu dipulihkan
A = MAIN.append
A(("H", "1. Introduction", 1))
for t in _intro: A(("P", t))
A(("H", "2. Materials and methods", 1))
A(("H", "2.1. Modelling framework", 2)); A(("P", _m21))
A(("H", "2.2. Data", 2)); MAIN += SECS["2.2. Data"]
A(("H", "2.3. Weather and soil", 2)); MAIN += SECS["2.3. Weather and soil"]
A(("H", "2.4. Step 1: potential production", 2)); A(("P", _m24))
for h in ("2.5. Step 2: parameter consistency in WOFOST 8.1", "2.6. Leaf-N extension", "2.7. Calibration of N parameters",
          "2.8. Evaluation"):
    A(("H", h, 2)); MAIN += SECS[h]
A(("H", "2.9. Uncertainty and sensitivity", 2)); A(("P", _m29))
A(("H", "2.10. Mechanistic diagnostics", 2)); MAIN += SECS["2.10. Mechanistic diagnostics"]
A(("H", "2.11. Use of generative artificial-intelligence tools", 2)); A(("P", _m211))
A(("H", "3. Results", 1))
A(("H", "3.1. Potential production", 2)); A(("P", _r31))
A(("H", "3.2. Nitrogen response and model comparison", 2))
for b in SECS["3.2. Nitrogen response and model comparison"]:
    if not (b[0] == "TABLE" and b[1].startswith("Table 3.")):
        A(b)
for h in ("3.3. Why leaf area did not respond to N", "3.4. Independent validation with omission plots"):
    A(("H", h.replace("with omission plots", "with omission plots and a second N-rate trial"), 2)); MAIN += SECS[h]
A(("H", "3.5. Uncertainty and sensitivity", 2)); A(("P", _r35a)); A(("P", _r35_full[1]))
A(("H", "3.6. Mechanistic diagnosis of the leaf-area response", 2)); MAIN += SECS["3.6. Mechanistic diagnosis of the leaf-area response"]
A(("H", "4. Discussion", 1))
A(("H", "4.1. Recalibrated and default parameters interact and can invert the simulated nitrogen response", 2))
MAIN += SECS["4.1. What the inconsistent parameters represent physiologically"]
A(("H", "4.2. Rice conserves leaf nitrogen and cuts leaf area, whereas the model dilutes leaf nitrogen", 2))
A(("P", _d42[0])); A(("P", _d42[1])); A(("P", _d42c))
A(("H", "4.3. A single fertiliser recovery overestimates the early nitrogen supply", 2))
MAIN += SECS["4.3. Why the early N response is still missing"]
A(("H", "4.4. Indigenous nitrogen supply is stable in time but local in space", 2))
MAIN += SECS["4.4. Indigenous N supply: stable in time, local in space"]
A(("H", "4.5. Secondary data and a wide leaf-nitrogen coefficient limit the inference", 2)); A(("P", _lim))
A(("H", "5. Conclusion", 1)); MAIN += SECS["5. Conclusions"]
A = _A_SIMPAN

# ------------------------------------------------------------------ 5. suplemen
SUPP = []
S = SUPP.append
S(("H", "Supplementary Text S1. Potential production and post-anthesis partitioning (PART_DELAY)", 1))
S(("P", _m24_full)); S(("P", PT("3.1. Potential production", 0))); S(("P", _d42[2]))
S(("H", "Supplementary Text S2. Sampler settings and convergence of the staged Bayesian inference", 1))
S(("P", PT("2.9. Uncertainty and sensitivity", 0))); S(("P", _r35_full[0]))
S(("H", "Supplementary Text S3. Sensitivity reflects the nitrogen economy of grain filling", 1))
for t in PT("4.5. Sensitivity reflects the N economy of grain filling"): S(("P", t))
S(("H", "Supplementary Text S4. Weather source as a mechanistic uncertainty", 1))
for t in PT("4.6. Weather source as a mechanistic uncertainty"): S(("P", t))
S(("H", "Supplementary figures", 1))
_figs = {b[1]: b for sec_ in SECS.values() for b in sec_ if b[0] == "FIG"}
for n in ("Fig1_workflow", "Fig2_potential_calibration", "Fig6_Sobol", "FigS1_weather_source", "FigS2_variety_assumption"):
    S(_figs[n])
S(("H", "Supplementary tables", 1))
_tabs = [b for sec_ in SECS.values() for b in sec_ if b[0] == "TABLE"]
_tS = {re.match(r"Table (S?\d+)", b[1]).group(1): b for b in _tabs}
for k in ("S1", "S2", "S3", "S4", "S5", "3"):
    S(_tS[k])

# ------------------------------------------------------------------ 6. pustaka gaya Springer
_INI = re.compile(r"^(?:[A-Z][a-z]?\.-?)+$")


def _authors(a):
    a = a.replace(", et al.", ", ET_AL").replace(" et al.", " ET_AL")
    toks = [x.strip() for x in a.split(", ") if x.strip()]
    out, fam, i = [], [], 0
    while i < len(toks):
        tk = toks[i]
        if tk == "ET_AL":
            out.append("et al"); i += 1; continue
        if i + 1 < len(toks) and _INI.match(toks[i + 1]):
            out.append(tk + " " + toks[i + 1].replace(".", "")); fam.append(tk); i += 2
        else:
            out.append(tk); fam.append(tk); i += 1
    s = ", ".join(out).replace(", et al", " et al")
    return s, fam


def springer_ref(r):
    body, _, doi = r.partition(" https://doi.org/")
    mm = re.match(r"^(.*?), ((?:19|20)\d{2}[a-z]?)\. (.*)$", body, flags=re.S)
    assert mm, r
    au, fam = _authors(mm.group(1))
    year, rest = mm.group(2), mm.group(3).strip()
    # jurnal: "... Journal Name 59, 31–41."  ->  "... Journal Name 59:31–41"
    rest = re.sub(r" (\d+(?:\([^)]*\))?), ([0-9A-Za-z–\-]+)\.?$", r" \1:\2", rest)
    rest = rest.rstrip(".")
    # bab buku & edisi -> gaya Springer
    for a_, b_ in (("In: Schepers, J.S., Raun, W.R. (Eds.), Nitrogen in Agricultural Systems.",
                    "In: Schepers JS, Raun WR (eds) Nitrogen in agricultural systems."),
                   ("In: Lemaire, G. (Ed.), Diagnosis of the Nitrogen Status in Crops.",
                    "In: Lemaire G (ed) Diagnosis of the nitrogen status in crops."),
                   (", Madison, WI, pp. ", ", Madison, pp "), (", Berlin, pp. ", ", Berlin, pp "),
                   (", 2nd ed.", ", 2nd edn."), (", 3rd ed.", ", 3rd edn.")):
        rest = rest.replace(a_, b_)
    assert "(Ed" not in rest and " pp. " not in rest, rest
    out = f"{au} ({year}) {rest}"
    if doi:
        out += ". https://doi.org/" + doi.strip()
    y = year
    if len(fam) == 1:
        c = f"{fam[0]} {y}"
    elif len(fam) == 2 and "et al" not in au:
        c = f"{fam[0]} and {fam[1]} {y}"
    else:
        c = f"{fam[0]} et al. {y}"
    return out, c, fam[0], y


REF_ALL = [springer_ref(t) for t, _ in REFS]


def cited(fam, year, text):
    f = re.escape(fam)
    y, suf = year[:4], year[4:]
    pats = [rf"{f}(?: et al\.| and [^\d(]{{1,40}}?)?,? \(?{y}{suf}\b"]
    if suf:   # bentuk gabungan "2018a, b"
        pats.append(rf"{f}(?: et al\.)?,? \(?{y}[a-z](?:, [a-z])*, {suf}\b")
        pats.append(rf"{f}(?: et al\.)? \(?{y}[a-z], {suf}\b")
    return any(re.search(p, text) for p in pats)


def all_text(blocks):
    out = []
    for b in blocks:
        if b[0] == "P": out.append(T(b[1]))
        elif b[0] == "FIG": out.append(T(b[2]))
        elif b[0] == "TABLE":
            out.append(T(b[1])); out += [T(x) for x in b[2]]
            out += [T(c) for r_ in b[3] for c in r_]
            if b[5]: out.append(T(b[5]))
    return "\n".join(out)


TXT_MAIN = all_text(MAIN) + "\n" + T(ABSTRACT_NCA)
TXT_SUPP = all_text(SUPP)
REF_MAIN = sorted([r for r in REF_ALL if cited(r[2], r[3], TXT_MAIN)], key=lambda r: (r[0].lower().replace("'", "")))
REF_SUPP = sorted([r for r in REF_ALL if not cited(r[2], r[3], TXT_MAIN) and cited(r[2], r[3], TXT_SUPP)],
                  key=lambda r: r[0].lower())
REF_NONE = [r for r in REF_ALL if not cited(r[2], r[3], TXT_MAIN) and not cited(r[2], r[3], TXT_SUPP)]


# ------------------------------------------------------------------ 7. penulisan dokumen
def new_doc(double=True, fs=12, lines=True):
    d = Document()
    st_ = d.styles["Normal"]; st_.font.name = "Times New Roman"; st_.font.size = Pt(fs)
    st_.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    st_.paragraph_format.line_spacing = 2.0 if double else 1.15
    st_.paragraph_format.space_after = Pt(0 if double else 4)
    for lvl, size in ((1, fs + 1), (2, fs), (3, fs)):
        h_ = d.styles[f"Heading {lvl}"]; h_.font.name = "Times New Roman"; h_.font.size = Pt(size); h_.font.bold = True
        h_.font.italic = (lvl == 2) and False
        h_.font.color.rgb = RGBColor(0, 0, 0); h_.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        for a_ in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            h_.element.rPr.rFonts.attrib.pop(qn(a_), None)
        h_.paragraph_format.space_before = Pt(12); h_.paragraph_format.space_after = Pt(0)
        h_.paragraph_format.line_spacing = 2.0 if double else 1.15
        h_.paragraph_format.keep_with_next = True
    s_ = d.sections[0]
    s_.page_height, s_.page_width = Cm(29.7), Cm(21.0)
    s_.left_margin = s_.right_margin = Cm(2.5); s_.top_margin = s_.bottom_margin = Cm(2.5)
    if lines:
        ln_ = OxmlElement("w:lnNumType"); ln_.set(qn("w:countBy"), "1"); ln_.set(qn("w:restart"), "continuous")
        ln_.set(qn("w:distance"), "283")
        c_ = s_._sectPr.find(qn("w:cols"))
        (c_.addprevious(ln_) if c_ is not None else s_._sectPr.append(ln_))
    fp_ = s_.footer.paragraphs[0]; fp_.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for tag, txt in (("begin", None), (None, "PAGE"), ("end", None)):
        r_ = fp_.add_run()
        if tag:
            e_ = OxmlElement("w:fldChar"); e_.set(qn("w:fldCharType"), tag); r_._r.append(e_)
        else:
            e_ = OxmlElement("w:instrText"); e_.set(qn("xml:space"), "preserve"); e_.text = txt; r_._r.append(e_)
    return d


def w_par(d, text, bold=False, italic=False, align=None, size=None, indent=False):
    p_ = d.add_paragraph(); r_ = p_.add_run(text); r_.bold = bold; r_.italic = italic
    if size: r_.font.size = Pt(size)
    if align is not None: p_.alignment = align
    return p_


def w_caption(d, caption, size=None):
    p_ = d.add_paragraph()
    head, _, tail = caption.partition(".")
    if head.startswith("Fig"):
        head, tail = caption.split(".", 2)[0] + "." + caption.split(".", 2)[1], caption.split(".", 2)[2]
        r_ = p_.add_run(head.strip()); r_.bold = True
    else:
        r_ = p_.add_run(head.strip()); r_.bold = True
    r2 = p_.add_run(" " + tail.strip())
    for x in (r_, r2):
        if size: x.font.size = Pt(size)
    return p_


def w_table(d, b, fs_cap=None):
    _, caption, header, rows, widths, note, fs = b
    cp = w_caption(d, T(caption), size=fs_cap); cp.paragraph_format.keep_with_next = True
    cp.paragraph_format.line_spacing = 1.15
    t_ = d.add_table(rows=1, cols=len(header)); t_.style = "Table Grid"; t_.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h_ in enumerate(header):
        c_ = t_.rows[0].cells[i]; c_.text = ""; rr = c_.paragraphs[0].add_run(T(h_)); rr.bold = True; rr.font.size = Pt(9)
    for row in rows:
        cells = t_.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""; rr = cells[i].paragraphs[0].add_run(T(v)); rr.font.size = Pt(9)
    k_ = 16.0 / sum(widths) if widths else 1
    for row in t_.rows:
        for j, c_ in enumerate(row.cells):
            for pp in c_.paragraphs:
                pp.paragraph_format.line_spacing = 1.0; pp.paragraph_format.space_after = Pt(0)
                pp.alignment = WD_ALIGN_PARAGRAPH.LEFT
            if widths:
                c_.width = Cm(widths[j] * k_)
    if note:
        q_ = d.add_paragraph(); q_.paragraph_format.line_spacing = 1.15; q_.alignment = WD_ALIGN_PARAGRAPH.LEFT
        rr = q_.add_run(T(note)); rr.font.size = Pt(9)
    sp = d.add_paragraph(); sp.paragraph_format.line_spacing = 1.0


def fig_no(caption):
    return re.match(r"Fig\. (S?\d+)", T(caption)).group(1)


# ----- naskah utama
doc_m = new_doc(double=True, fs=12, lines=True)
w_par(doc_m, TITLE_NCA, bold=True, size=14)
w_par(doc_m, "Zainal Arifin¹ · Iwan Gunawan²")
w_par(doc_m, "¹ Department of Agribusiness, Vocational School, Universitas Sebelas Maret, Surakarta, Indonesia")
w_par(doc_m, "² Department of Mechanical Engineering, Universitas Khairun, Ternate 97719, Indonesia")
w_par(doc_m, "Corresponding authors: Zainal Arifin (responsible corresponding author), zainal.arifin@staff.uns.ac.id; "
             "Iwan Gunawan, iwan99gun@unkhair.ac.id")
w_par(doc_m, "ORCID: Zainal Arifin 0009-0008-0345-3167; Iwan Gunawan 0000-0002-2784-4436")
doc_m.add_heading("Abstract", level=1); w_par(doc_m, T(ABSTRACT_NCA))
p_ = doc_m.add_paragraph(); r_ = p_.add_run("Keywords "); r_.bold = True; p_.add_run(" · ".join(KEYWORDS_NCA))
ABBR = [("AGB", "above-ground biomass"), ("AICc", "corrected Akaike information criterion"),
        ("CRPS", "continuous ranked probability score"), ("CV", "coefficient of variation"),
        ("DAT", "days after transplanting"), ("DS, WS", "dry season, wet season"), ("DVS", "development stage (0 emergence, 1 anthesis, 2 maturity)"),
        ("LAI", "leaf area index"), ("LODO", "leave-one-dose-out cross-validation"),
        ("LTFE", "long-term fertility experiment"), ("MCMC", "Markov chain Monte Carlo"),
        ("NNI", "nitrogen nutrition index"), ("PCSE", "Python Crop Simulation Environment"),
        ("PGPR", "plant growth-promoting rhizobacteria"), ("RMSE", "root mean square error"),
        ("SLA", "specific leaf area"), ("SLN", "specific leaf nitrogen (leaf N per unit leaf area)"),
        ("SPAD", "chlorophyll-meter reading of leaf greenness")]
PARS = [("AMAXTB, AMAX_REF", "maximum leaf CO₂ assimilation rate (table; reference value)"),
        ("KN", "extinction coefficient of leaf N in the canopy"), ("NLEAF", "leaf-N coefficient of the extension (= N_SLA = N_LAI)"),
        ("NMAXSO", "maximum N concentration of the storage organs"), ("NSOILBASE", "indigenous soil N supply"),
        ("PART_DELAY", "delay of post-anthesis partitioning to the storage organs"),
        ("RGRLAI, RGRLAI_MIN", "maximum relative increase of LAI and its floor under N deficiency"),
        ("SLATB", "specific leaf area (table)"), ("SPAN", "leaf life span"), ("TDWI", "initial total crop dry weight"),
        ("TSUM1, TSUM2", "thermal time from emergence to anthesis and from anthesis to maturity")]
assert [a for a, _ in ABBR] == sorted([a for a, _ in ABBR], key=str.lower)
doc_m.add_heading("Abbreviations", level=1)
w_par(doc_m, "; ".join(f"{a}, {b}" if "," not in a else f"{a}: {b}" for a, b in ABBR) + ".")
w_par(doc_m, "Model parameters: " + "; ".join(f"{a}, {b}" if "," not in a else f"{a}: {b}" for a, b in PARS) + ".")
FIG_MAIN = []
for b in MAIN:
    if b[0] == "H":
        doc_m.add_heading(T(b[1]), level=b[2])
    elif b[0] == "P":
        w_par(doc_m, T(b[1]))
    elif b[0] == "TABLE":
        w_table(doc_m, b)
    elif b[0] == "FIG":
        w_caption(doc_m, T(b[2])); FIG_MAIN.append(b)
doc_m.add_heading("Acknowledgements", level=1)
w_par(doc_m, PT("Acknowledgements", 0))
doc_m.add_heading("Statements and Declarations", level=1)
for hd, tx in (
    ("Funding", "The authors declare that no funds, grants, or other support were received during the preparation of this manuscript."),
    ("Competing interests", "The authors have no relevant financial or non-financial interests to disclose."),
    ("Author contributions", "I.G. developed the WOFOST Studio software, the nitrogen extension and the analysis scripts. "
     "Z.A. and I.G. performed the literature search and reference compilation, wrote the manuscript and edited it. "
     "Both authors read and approved the final manuscript."),
    ("Data availability", "All datasets extracted from the literature (with source, table or figure and extraction method for "
     "every value), the model code, the analysis scripts and the simulation results that support the findings of this study "
     "are openly available in Zenodo at https://doi.org/10.5281/zenodo.22969838 and at "
     "https://github.com/iwan99gun/wofost-studio-inpari32-n (MIT licence)."),
):
    doc_m.add_heading(hd, level=2); w_par(doc_m, tx)
doc_m.add_heading("References", level=1)
for r in REF_MAIN:
    p_ = w_par(doc_m, r[0]); p_.paragraph_format.left_indent = Cm(0.75); p_.paragraph_format.first_line_indent = Cm(-0.75)
for b in FIG_MAIN:                          # gambar: satu per lembar, setelah semua keterangan
    doc_m.add_page_break()
    doc_m.add_picture(str(G / f"{b[1]}.png"), width=Cm(16.0))
    doc_m.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    w_par(doc_m, "Fig. " + fig_no(b[2]), bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
doc_m.save(NCA_DIR / "NCA_Manuscript.docx")

# ----- suplemen
doc_s = new_doc(double=False, fs=11, lines=False)
w_par(doc_s, "Supplementary Information", bold=True, size=14)
w_par(doc_s, TITLE_NCA, bold=True)
w_par(doc_s, "Zainal Arifin · Iwan Gunawan")
w_par(doc_s, "Nutrient Cycling in Agroecosystems. Corresponding author: Zainal Arifin, zainal.arifin@staff.uns.ac.id", size=10)
for b in SUPP:
    if b[0] == "H":
        doc_s.add_heading(T(b[1]), level=b[2])
    elif b[0] == "P":
        w_par(doc_s, T(b[1]))
    elif b[0] == "TABLE":
        w_table(doc_s, b)
    elif b[0] == "FIG":
        doc_s.add_picture(str(G / f"{b[1]}.png"), width=Cm(16.0))
        doc_s.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        w_caption(doc_s, T(b[2]), size=10)
if REF_SUPP:
    doc_s.add_heading("Supplementary references", level=1)
    for r in REF_SUPP:
        p_ = w_par(doc_s, r[0], size=10); p_.paragraph_format.left_indent = Cm(0.75); p_.paragraph_format.first_line_indent = Cm(-0.75)
doc_s.save(NCA_DIR / "NCA_Supplementary_Information.docx")

# ----- berkas gambar terpisah
(NCA_DIR / "Figures").mkdir(exist_ok=True)
for b in FIG_MAIN:
    for ext in ("tif", "png"):
        shutil.copy(G / f"{b[1]}.{ext}", NCA_DIR / "Figures" / f"Fig{fig_no(b[2])}.{ext}")

# ------------------------------------------------------------------ 8. laporan kepatuhan
def wc(blocks):
    return sum(len(T(b[1]).split()) for b in blocks if b[0] == "P") + sum(len(T(b[2]).split()) for b in blocks if b[0] == "FIG")


n_text = wc(MAIN)
n_items = sum(1 for b in MAIN if b[0] in ("FIG", "TABLE"))
rep = [f"judul: {len(TITLE_NCA)} karakter (batas 90)",
       f"abstrak: {N_ABS_NCA} kata (150-250)",
       f"kata kunci: {len(KEYWORDS_NCA)} (4-6)",
       f"teks utama (Pendahuluan-Kesimpulan, termasuk keterangan gambar): {n_text} kata; + abstrak = {n_text + N_ABS_NCA} (batas 7000)",
       f"gambar+tabel di teks utama: {n_items} (4-8): " + ", ".join(
           (("Fig. " + fig_no(b[2])) if b[0] == "FIG" else T(b[1]).split(".")[0]) for b in MAIN if b[0] in ("FIG", "TABLE")),
       f"pustaka: utama {len(REF_MAIN)}, suplemen {len(REF_SUPP)}, tidak tersitasi {len(REF_NONE)}"]
for r in REF_NONE:
    rep.append("   TIDAK TERSITASI: " + r[1])
secs_ref = sorted(set(re.findall(r"Sections? (\d\.\d+)", TXT_MAIN)))
heads = {re.match(r"(\d\.\d+)", b[1]).group(1) for b in MAIN if b[0] == "H" and re.match(r"\d\.\d+", b[1])}
rep.append("rujukan silang bagian di teks utama: " + ", ".join(secs_ref) + " | tidak ada judulnya: "
           + (", ".join(s for s in secs_ref if s not in heads) or "-"))
rep.append("rujukan gambar/tabel di teks utama: " + ", ".join(sorted(set(re.findall(r"(?:Fig\.|Table) S?\d+", TXT_MAIN)))))
(NCA_DIR / "laporan_kepatuhan.txt").write_text("\n".join(rep) + "\n\nSITASI YANG DIUBAH (pemeriksaan manual):\n"
                                               + "\n".join(sorted(set(CIT_LOG))), encoding="utf-8")
(NCA_DIR / "pustaka_utama.txt").write_text("\n".join(r[0] for r in REF_MAIN), encoding="utf-8")
print("\n".join(rep))
print("NCA:", NCA_DIR)
