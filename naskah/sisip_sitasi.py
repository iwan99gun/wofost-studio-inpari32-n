from pathlib import Path
p = Path(__file__).with_name("buat_naskah.py")
s = p.read_text(encoding="utf-8")
reps = [
    ('C("cassman1998", "Dobermann et al., 2003a")', 'C("cassman1998", "Cassman et al., 2002", "Dobermann et al., 2003a")'),
    ('"calibration choices alone can change model behaviour substantially " + C("wallach2021") + ".")',
     '"calibration choices alone can change model behaviour substantially " + C("Wallach et al., 2019", "wallach2021") + ".")'),
    ('"reflectance and N uptake, which are exactly the variables used for remote-sensing assimilation and N diagnosis.")',
     '"reflectance and N uptake, which are exactly the variables used for remote-sensing assimilation and N diagnosis "\n  + C("zha2020", "chen2022") + ".")'),
    ('"dilution curve that is largely a consequence of reduced leaf area per unit biomass " + C("sheehy1998", "ataulkarim2013")',
     '"dilution curve that is largely a consequence of reduced leaf area per unit biomass " + C("sheehy1998", "ataulkarim2013", "song2020")'),
    ('+ C("zhong2003", "vos2005") + ". Our decomposition', '+ C("zhong2003", "vos2005", "Gastal and Lemaire, 2002") + ". Our decomposition'),
    ('"rice avoids because photosynthesis per unit N falls steeply at low SLN " + C("evans1989", "makino2011") + ".")',
     '"rice avoids because photosynthesis per unit N falls steeply at low SLN " + C("evans1989", "makino2011") + ". Canopy "\n'
     '  "radiation-use efficiency is highest when leaf N follows the light profile, and the benefit of that distribution itself "\n'
     '  "depends on leaf area (" + PUS["bonelli2020"]["cite"] + "; " + PUS["wang2024"]["cite"] + ", both in maize), so leaf area and N per "\n'
     '  "unit leaf area are co-regulated rather than independent.")'),
    ('"remotely sensed LAI " + C("huang2015", "lu2025")', '"remotely sensed LAI " + C("huang2015", "novelli2019", "lu2025")'),
    ('"tropical rice " + C("ying1998")', '"tropical rice " + C("ying1998", "fukushima2019")'),
    ('"0-N plots still produced 3.3–3.4 t ha⁻¹ of grain dry matter. Across fields, however, the same inputs vary with organic matter quality, legacy "\n  "N from past fertilisation, drainage and water source.',
     'XX'),
]
for a, b in reps[:-1]:
    if a not in s:
        raise SystemExit("MISS: " + a[:80])
    s = s.replace(a, b)
# paragraf INS: sisipkan sitasi legasi N dan potensi mineralisasi
a = '"N from past fertilisation, drainage and water source. Soil-test classes'
if a not in s:
    raise SystemExit("MISS INS")
s = s.replace(a, '"N from past fertilisation " + C("huang2021") + ", drainage and water source; differences in mineralisation potential "\n'
                 '  "between paddy soils alone change rice N supply and the fate of fertiliser N " + C("liu2026") + ". Soil-test classes')
# Liu 2026 belum bervolume
a2 = 'PUS["iizumi2009"]["cite"] = "Iizumi et al., 2009"'
s = s.replace(a2, a2 + '\nPUS["liu2026"]["ref"] = PUS["liu2026"]["ref"].replace("Plant and Soil None.", "Plant and Soil, in press.")')
p.write_text(s, encoding="utf-8")
print("ok")
