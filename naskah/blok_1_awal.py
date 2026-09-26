# ---- blok 1: pustaka terverifikasi, highlights, abstrak, pendahuluan (disisipkan ke buat_naskah.py) ----
import re as _re
MEK = J("mekanisme_n_daun.json")
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
PUS["iizumi2009"]["cite"] = "Iizumi et al., 2009"; PUS["monsi2005"]["cite"] = "Monsi and Saeki, 2005"
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
    "Nitrogen (N)-limited crop models increasingly guide fertiliser management in tropical rice, but their implementations are "
    "rarely tested for internal consistency or against independent N-omission data. We evaluated WOFOST 8.1 (PCSE 6.0.13) for "
    "the Indonesian inbred rice Inpari-32 with literature-mined data from West Java. Potential-production parameters were "
    "calibrated on three 2016 experiments and N parameters on an N-rate trial (23–207 kg N ha⁻¹); evaluation combined "
    "cross-validation, MCMC, Sobol analysis and blind prediction of two seasons of 0-N omission plots from a long-term "
    "experiment. Three consistency problems were corrected: a recalibrated RGRLAI below RGRLAI_MIN inverted the juvenile "
    "N-stress response, calibrated AMAXTB was ignored by the N-dependent photosynthesis, and N stress acted on leaf expansion "
    "only in a juvenile window that closed before N deficiency developed. The corrected model reproduced grain yield across "
    f"N rates (cross-validated RMSE {100 * STD['rmse_lodo']['TWSO'] / 5716:.1f}%) and predicted independent 0-N yields within "
    f"{max(abs(err0['std']['S2022']), abs(err0['std']['S2020'])):.1f}%; indigenous N supply inferred from the omission plots "
    f"({f1(nsbB['S2022'])}–{f1(nsbB['S2020'])} kg N ha⁻¹) matched the calibrated value ({f1(ps['NSOILBASE'])} kg N ha⁻¹). "
    f"Mechanistically, N-deficient rice kept leaf greenness (SPAD −{min(spad_red):.0f} to −{max(spad_red):.0f}%) while reducing "
    f"leaf area by {min(lai_red_obs):.0f}–{max(lai_red_obs):.0f}%, mostly through smaller leaf area per tiller, whereas WOFOST 8.1 "
    f"kept leaf area and diluted specific leaf N by {min(sln_red_std):.0f}–{max(sln_red_std):.0f}%. A one-parameter "
    f"LINTUL3-type extension reversing this strategy reduced the error in the leaf-area response from {rm['std']:.2f} to "
    f"{rm['ext']:.2f}. Indigenous N supply was stable over five years but not transferable to farmers' fields. Enforcing "
    "parameter consistency and representing leaf-area plasticity are prerequisites for simulating N responses of tropical rice.")
P(ABSTRACT)
N_ABS = len(ABSTRACT.split())
PR([("Keywords: ", "b"), ("crop model; WOFOST; nitrogen nutrition index; leaf area plasticity; indigenous nitrogen supply; "
                          "omission plot; Bayesian calibration; Oryza sativa", "")])
if BACA:
    for par in doc.paragraphs[-2:-1]:
        pPr = par._p.get_or_add_pPr(); shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), "EEF2F6"); pPr.append(shd)
    set_cols(2)

# ================================================================== 1 Introduction
H("1. Introduction")
P("Rice is the staple food of Indonesia, and the irrigated lowlands of Java supply a large share of national production. "
  "Nitrogen (N) is the nutrient that most often limits rice yield in these systems, while farmer N rates and N-use efficiency "
  "vary widely " + C("cassman1998", "Dobermann et al., 2003a") + ". Yield gaps of intensive rice in Indonesia remain "
  "substantial " + C("agus2019") + ", and site-specific N management based on indigenous N supply has repeatedly "
  "increased N-use efficiency in Asian irrigated rice " + C("pampolino2007") + ". Process-based crop models are the "
  "standard tool for exploring such management options beyond the range of field trials " + C("van Ittersum et al., 2013") + ", "
  "but multi-model comparisons show large structural uncertainty in simulated rice yield " + C("li2015") + ", and "
  "calibration choices alone can change model behaviour substantially " + C("wallach2021") + ".")
PR([("WOFOST is one of the most widely used crop growth models (van Diepen et al., 1989; de Wit et al., 2019). In Asia it "
     "has been used for regional yield estimation with leaf area assimilation " + C("huang2015", "lu2025") + ", seasonal "
     "rice yield forecasting in mainland Southeast Asia " + C("wanthanaporn2024") + " and global sensitivity analysis "
     + C("wang2013", "li2023") + ". WOFOST 8.1 couples crop growth to soil and crop N balances and makes leaf photosynthesis "
     "depend on specific leaf N " + C("berghuijs2024") + ". ", ""),
    ("Applications to tropical transplanted rice remain scarce; a Scopus search returned eight WOFOST documents for tropical "
     "Southeast Asia (search string and date to be reported)", "v"),
    (". In Indonesia, rice modelling has relied mainly on ORYZA " + C("boling2007") + ", which, like LINTUL3 (Shibu et al., "
     "2010), represents N effects on leaf area expansion, whereas WOFOST 7.x did not simulate N at all.", "")])
P("How a model reproduces the N response matters as much as whether it does. N-deficient rice reduces tillering and leaf "
  "expansion and increases specific leaf weight, so that N per unit leaf area changes much less than leaf area "
  + C("peng1993", "zhong2003", "vos2005") + "; the critical N concentration of the crop declines with biomass along a dilution curve "
  + C("sheehy1998", "ataulkarim2013") + " as N is concentrated in the upper, well-lit leaves " + C("lemaire1997", "hikosaka2016")
  + ". Photosynthetic capacity, in turn, scales with leaf N per unit area because most leaf N is invested in the "
  "photosynthetic apparatus " + C("evans1989", "makino2011") + ". A model can therefore reach the right yield by reducing "
  "leaf area (as rice does) or by diluting leaf N at constant leaf area; the two routes diverge in leaf area, canopy "
  "reflectance and N uptake, which are exactly the variables used for remote-sensing assimilation and N diagnosis.")
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
