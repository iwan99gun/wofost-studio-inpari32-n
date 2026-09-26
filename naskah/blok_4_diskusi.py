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
  "dilution curve that is largely a consequence of reduced leaf area per unit biomass " + C("sheehy1998", "ataulkarim2013")
  + ". Leaf area is the plastic variable, because both tiller outgrowth and leaf elongation require a threshold leaf N "
  + C("zhong2003", "vos2005") + ". Our decomposition shows that about "
  f"{100 * min(til_share):.0f}–{100 * max(til_share):.0f}% of the late-season LAI reduction came from fewer tillers and the "
  "rest from smaller leaves, and that the 0-N crop carried "
  f"{bpl[('S2022', '60')]:.2f} times more biomass per unit leaf area. WOFOST 8.1, in contrast, fixes specific leaf area as a "
  "function of development stage and lets N deficiency act on photosynthesis per unit leaf area; the model therefore "
  f"keeps expanding leaves with diluted N (SLN reduced by {min(sln_red_std):.0f}–{max(sln_red_std):.0f}%), a strategy that "
  "rice avoids because photosynthesis per unit N falls steeply at low SLN " + C("evans1989", "makino2011") + ".")
P("Both strategies reduce canopy photosynthesis, one through interception and one through leaf-level capacity, so the "
  "yield response alone cannot discriminate between them; this is why the two model versions had similar AICc and "
  "cross-validated yield errors. They diverge, however, in every canopy variable: leaf area, light interception, canopy "
  "N distribution and spectral reflectance. The distinction is therefore essential when WOFOST is combined with "
  "remotely sensed LAI " + C("huang2015", "lu2025") + ": the standard model would interpret a low observed LAI of an "
  "N-deficient field as a growth deficit of unknown cause and correct it by adjusting state variables that are "
  "physiologically unrelated to N. The one-parameter extension corrects the strategy rather than the outcome: it lowers "
  "specific leaf area and exponential-phase expansion in proportion to (1 − NNI), raising the simulated SLN ratio to "
  f"{min(sln_ratio_ext):.2f}–{max(sln_ratio_ext):.2f}, and it improved the leaf-area response in data never used for "
  "calibration, which AICc on the calibration set could not reveal.")
P("The residual yield effect not explained by interception (factor "
  f"{inter['S2022']['rasio_hasil_per_intersepsi']:.2f} in DS 2022) points to sink limitation. N deficiency around panicle "
  "initiation reduces spikelet differentiation and the number of productive panicles; the 0-N plots had 44% fewer "
  "panicles per hill (Susanti et al., 2023). Grain number is a major determinant of the yield advantage of high-yielding "
  "tropical rice " + C("ying1998") + ", yet WOFOST partitions assimilates to grain by development stage only and has no "
  "N-dependent sink size. The same structural feature explains why observed harvest indices dropped at 115–207 kg N ha⁻¹ "
  "(0.38–0.42), when surplus N stimulates vegetative and unproductive tiller growth, whereas simulated harvest indices "
  f"remained at {min(tab_s[d]['TWSO_sim'] / tab_s[d]['TAGP_sim'] for d in (115, 207)):.2f}–"
  f"{max(tab_s[d]['TWSO_sim'] / tab_s[d]['TAGP_sim'] for d in (115, 207)):.2f}.")

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
  "N from past fertilisation, drainage and water source. Soil-test classes such as total N capture these differences "
  "poorly (Dobermann et al., 2003a); soil organic carbon predicted indigenous N supply in one temperate region "
  + C("espe2015") + ", but such relations are regional. The failed transfer to farmers' fields that share the station's "
  "\"low N\" soil class is therefore expected and supports the omission-plot approach of site-specific N management "
  + C("Dobermann et al., 2003b", "pampolino2007") + ".")

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
P("All data are secondary, several were digitised from figures, and no transplanting date was reported; the effects of "
  "these assumptions were quantified but cannot be eliminated. The independent validation used Inpari-33 rather than "
  "Inpari-32, although results were robust to eight variety assumptions. SPAD was available only for 2020 and is a proxy "
  "rather than a measurement of leaf N per area. The NLEAF extension was supported by independent data but rests on three "
  "datasets from one station and should be tested across sites and varieties. A dedicated field season with weekly green "
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
