"""Verifikasi kandidat pustaka lewat Crossref REST API (metadata publik). Cetak judul, jurnal, tahun, volume, halaman,
DOI dan penulis pertama dari kecocokan teratas supaya bisa dicek manual sebelum masuk naskah."""
import json, sys, time, urllib.parse, urllib.request

CAND = {
    "sheehy1998": "Sheehy 1998 Critical nitrogen concentrations implications for high-yielding rice cultivars in the tropics Field Crops Research",
    "ataulkarim2013": "Ata-Ul-Karim 2013 Development of critical nitrogen dilution curve of Japonica rice Yangtze River Reaches Field Crops Research",
    "evans1989": "Evans 1989 Photosynthesis and nitrogen relationships in leaves of C3 plants Oecologia",
    "hirose1987": "Hirose Werger 1987 Maximizing daily canopy photosynthesis with respect to the leaf nitrogen allocation pattern in the canopy Oecologia",
    "vos2005": "Vos van der Putten Birch 2005 Effect of nitrogen supply on leaf appearance leaf growth leaf nitrogen economy photosynthetic capacity maize Field Crops Research",
    "peng1993": "Peng Garcia Laza Cassman 1993 Adjustment for specific leaf weight improves chlorophyll meter estimate of rice leaf nitrogen concentration Agronomy Journal",
    "cassman1998": "Cassman Peng Olk 1998 Opportunities for increased nitrogen-use efficiency from improved resource management in irrigated rice systems Field Crops Research",
    "peng2006": "Peng Buresh Huang 2006 Strategies for overcoming low agronomic nitrogen use efficiency in irrigated rice systems in China Field Crops Research",
    "vanwart2013": "Van Wart Grassini Cassman 2013 Impact of derived global weather data on simulated crop yields Global Change Biology",
    "white2008": "White Hoogenboom Stackhouse Hoell 2008 Evaluation of NASA satellite- and assimilation model-derived long-term daily temperature data over the continental US",
    "bai2010": "Bai Chen Dobermann 2010 Evaluation of NASA satellite- and model-derived weather data for simulation of maize yield potential in China Agronomy Journal",
    "agus2019": "Agus Andrade Rattalino Edreira 2019 Yield gaps in intensive rice-maize cropping sequences in the humid tropics of Indonesia Field Crops Research",
    "pampolino2007": "Pampolino 2007 Environmental impact and economic benefits of site-specific nutrient management SSNM in irrigated rice systems Agricultural Systems",
    "drevon2017": "Drevon Fursa Malcolm 2017 Intercoder reliability and validity of WebPlotDigitizer in extracting graphed data Behavior Modification",
    "li2015": "Li Hasegawa Yin 2015 Uncertainties in predicting rice yield by current crop models under a wide range of climatic conditions Global Change Biology",
    "asseng2013": "Asseng 2013 Uncertainty in simulating wheat yields under climate change Nature Climate Change",
    "mae1997": "Mae 1997 Physiological nitrogen efficiency in rice nitrogen utilization photosynthesis and yield potential Plant and Soil",
    "makino2011": "Makino 2011 Photosynthesis grain yield and nitrogen utilization in rice and wheat Plant Physiology",
    "ying1998": "Ying Peng He 1998 Comparison of high-yield rice in tropical and subtropical environments determinants of grain and dry matter yields Field Crops Research",
    "sinclair1975": "Sinclair de Wit 1975 Photosynthate and nitrogen requirements for seed production by various crops Science",
    "espe2015": "Espe Kirk van Kessel Horwath Linquist 2015 Indigenous nitrogen supply of rice is predicted by soil organic carbon Soil Science Society of America Journal",
    "wallach2021": "Wallach 2021 The chaos in calibrating crop models lessons learned from a multi-model calibration exercise Environmental Modelling Software",
    "iizumi2009": "Iizumi Yokozawa Nishimori 2009 Parameter estimation and uncertainty analysis of a large-scale crop model for paddy rice Bayesian approach Agricultural and Forest Meteorology",
    "tan2017oryza": "Tan Cao Cui Duan Gong 2019 Comparison of the generalized likelihood uncertainty estimation and Markov chain Monte Carlo methods uncertainty analysis ORYZA_V3",
    "wang2013efast": "Wang Li Lu Fang 2013 Parameter sensitivity analysis of crop growth models based on the extended Fourier Amplitude Sensitivity Test method Environmental Modelling Software",
    "berghuijs2024": "Berghuijs Silva Reidsma de Wit 2024 Expanding the WOFOST crop model to explore options for sustainable nitrogen management winter wheat Netherlands",
    "huang2015": "Huang 2015 Assimilating a synthetic Kalman filter leaf area index series into the WOFOST model to improve regional winter wheat yield estimation",
    "yin2017": "Yin Struik 2017 Can increased leaf photosynthesis be converted into higher crop mass production A simulation study for rice using the crop model GECROS",
    "buresh2008": "Buresh Reddy van Kessel 2008 Nitrogen transformations in submerged soils Nitrogen in Agricultural Systems",
    "lemaire1997": "Lemaire Gastal 1997 N uptake and distribution in plant canopies Diagnosis of the Nitrogen Status in Crops",
    "hikosaka2016": "Hikosaka Anten Borjigidai 2016 A meta-analysis of leaf nitrogen distribution within plant canopies Annals of Botany",
    "wopereis2000": "Wopereis ORYZA rice nitrogen model evaluation 2000",
    "boling2007": "Boling Bouman Tuong 2007 Modelling the effect of groundwater depth on yield-increasing interventions in rainfed lowland rice in Central Java Indonesia Agricultural Systems",
    "yuan2017": "Yuan Linquist Wilson 2017 Sensitivity of crop models to parameter ORYZA rice nitrogen",
    "tian2021wofost": "WOFOST rice calibration China 2021 simulation yield",
    "ceglar2019": "Ceglar van der Wijngaart de Wit 2019 Improving WOFOST model to simulate winter wheat phenology in Europe Agricultural Systems",
    "zhuo2022": "WOFOST nitrogen limited crop model evaluation 2023 European Journal of Agronomy",
    "dewit2020pcse": "de Wit Boogaard Supit van den Berg 2020 System description of the WOFOST 7.2 cropping systems model",
    "asseng2013b": "Asseng Ewert Rosenzweig Jones Hatfield 2013 Uncertainty in simulating wheat yields under climate change Nature Climate Change 3 827",
    "huang2015b": "Huang Tian Liang Ma Kong Wu 2015 Improving winter wheat yield estimation by assimilation of the leaf area index from Landsat TM and MODIS data into the WOFOST model Agricultural and Forest Meteorology 204",
    "zhong2003": "Zhong Peng Sanico Liu 2003 Quantifying the interactive effect of leaf nitrogen and leaf area on tillering of rice Journal of Plant Nutrition",
    "roger1992": "Roger Ladha 1992 Biological N2 fixation in wetland rice fields estimation and contribution to nitrogen balance Plant and Soil",
    "beven2001": "Beven Freer 2001 Equifinality data assimilation and uncertainty estimation in mechanistic modelling of complex environmental systems GLUE Journal of Hydrology",
    "monsi2005": "Monsi Saeki 2005 On the factor light in plant communities and its importance for matter production Annals of Botany",
    "sparks2018": "Sparks 2018 nasapower a NASA POWER global meteorology surface solar energy and climatology data client for R Journal of Open Source Software",
    "wallach2023": "Wallach 2023 Proposal and extensive test of a calibration protocol for crop phenology models Agronomy for Sustainable Development",
    "wofostrice": "WOFOST model rice yield simulation calibration Asia paddy",
    "oryzaindo": "ORYZA2000 rice model calibration validation Indonesia",
    "kobayashi": "Horie Kropff rice leaf area nitrogen specific leaf area model",
    "gastal2015": "Gastal Lemaire Durand Louarn 2015 Quantifying crop responses to nitrogen and avenues to improve nitrogen-use efficiency Crop Physiology",
    "seas5wofost": "Skill of rice yields forecasting over Mainland Southeast Asia using the ECMWF SEAS5 ensemble prediction system and the WOFOST crop model",
    "rsdl2025": "Estimation of rice yield using multi-source remote sensing data combined with crop growth model and deep learning algorithm",
    "efastyr2023": "Sensitivity Analysis of the WOFOST Crop Model Parameters Using the EFAST Method and Verification of Its Adaptability in the Yellow River Irrigation Area",
    "lintul2011": "Shibu LINTUL3 nitrogen rice 2010",
}


def query(q):
    url = "https://api.crossref.org/works?rows=3&select=DOI,title,container-title,issued,volume,page,author,article-number&query.bibliographic=" + urllib.parse.quote(q)
    req = urllib.request.Request(url, headers={"User-Agent": "WOFOSTStudio-refcheck/1.0 (mailto:noreply@example.org)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["message"]["items"]


out = {}
keys = sys.argv[1:] or list(CAND)
for k in keys:
    try:
        items = query(CAND[k])
    except Exception as e:  # noqa: BLE001
        print(k, "GAGAL", e); continue
    res = []
    for it in items[:2]:
        au = it.get("author", [{}])[0]
        res.append(dict(title=(it.get("title") or [""])[0], journal=(it.get("container-title") or [""])[0],
                        year=(it.get("issued", {}).get("date-parts") or [[None]])[0][0], volume=it.get("volume"),
                        page=it.get("page") or it.get("article-number"), doi=it.get("DOI"),
                        first=f"{au.get('family', '')}, {au.get('given', '')}", n_auth=len(it.get("author", []))))
    out[k] = res
    r0 = res[0] if res else {}
    print(f"[{k}] {r0.get('first')} ({r0.get('year')}) {r0.get('title')[:95]} | {r0.get('journal')} {r0.get('volume')}:{r0.get('page')} | doi:{r0.get('doi')}")
    time.sleep(0.4)
json.dump(out, open(__file__.replace("cek_pustaka.py", "pustaka_crossref.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
