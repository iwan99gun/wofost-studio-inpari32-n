"""Ambil metadata Crossref per DOI dan format gaya Elsevier (Harvard). Hasil: naskah/pustaka_terverifikasi.json
{key: {"ref": teks, "cite": "Sheehy et al., 1998", "doi": ...}}"""
import json, time, html, re, urllib.request
from pathlib import Path

DOIS = {
    "sheehy1998": "10.1016/s0378-4290(98)00105-1", "ataulkarim2013": "10.1016/j.fcr.2013.03.012",
    "evans1989": "10.1007/bf00377192", "vos2005": "10.1016/j.fcr.2004.09.013",
    "peng1993": "10.2134/agronj1993.00021962008500050005x", "cassman1998": "10.1016/s0378-4290(97)00140-8",
    "peng2006": "10.1016/j.fcr.2005.05.004", "vanwart2013": "10.1111/gcb.12302", "bai2010": "10.2134/agronj2009.0085",
    "agus2019": "10.1016/j.fcr.2019.04.006", "pampolino2007": "10.1016/j.agsy.2006.04.002",
    "drevon2017": "10.1177/0145445516673998", "li2015": "10.1111/gcb.12758", "mae1997": "10.1023/a:1004293706242",
    "makino2011": "10.1104/pp.110.165076", "ying1998": "10.1016/s0378-4290(98)00077-x",
    "sinclair1975": "10.1126/science.189.4202.565", "espe2015": "10.2136/sssaj2014.08.0328",
    "wallach2021": "10.1016/j.envsoft.2021.105206", "iizumi2009": "10.1016/j.agrformet.2008.08.015",
    "wang2013": "10.1016/j.envsoft.2013.06.007", "huang2015": "10.1016/j.agrformet.2015.02.001",
    "buresh2008": "10.2134/agronmonogr49.c11", "lemaire1997": "10.1007/978-3-642-60684-7_1",
    "hikosaka2016": "10.1093/aob/mcw099", "boling2007": "10.1016/j.agsy.2006.05.003",
    "zhong2003": "10.1081/pln-120020365", "roger1992": "10.1007/bf00011309", "beven2001": "10.1016/s0022-1694(01)00421-8",
    "monsi2005": "10.1093/aob/mci052", "wanthanaporn2024": "10.1016/j.agrformet.2024.110001",
    "lu2025": "10.1016/j.agrformet.2025.110600", "li2023": "10.3390/agronomy13092294",
    "berghuijs2024": "10.1016/j.eja.2024.127099",
    "song2020": "10.3390/agronomy10030367", "zha2020": "10.3390/rs12020215", "bonelli2020": "10.1016/j.fcr.2019.107557",
    "wang2024": "10.34133/plantphenomics.0217", "fukushima2019": "10.1080/1343943x.2018.1562308", "novelli2019": "10.3390/agronomy9050255",
    "gneiting2007": "10.1198/016214506000001437", "gelman1992": "10.1214/ss/1177011136", "goodman2010": "10.2140/camcos.2010.5.65",
    "chen2022": "10.1016/j.fcr.2021.108398", "huang2021": "10.1007/s42729-021-00714-7", "liu2026": "10.1007/s11104-026-08939-0",
}
# tahun cetak (volume) bila berbeda dengan tahun terbit daring di Crossref
YEAR_FIX = {"drevon2017": 2017, "li2015": 2015, "makino2011": 2011, "monsi2005": 2005}


def meta(doi):
    req = urllib.request.Request("https://api.crossref.org/works/" + doi, headers={"User-Agent": "WOFOSTStudio-refcheck/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["message"]


def initials(given):
    parts = re.split(r"[\s\-]+", given.strip())
    return "".join(p[0] + "." for p in parts if p)


def fmt(key, m):
    au = m.get("author", [])
    names = [f"{a.get('family', '').strip()}, {initials(a.get('given', ''))}" if a.get("given") else a.get("family", a.get("name", "")) for a in au]
    fam = [a.get("family", a.get("name", "")) for a in au]
    year = YEAR_FIX.get(key) or (m.get("published-print") or m.get("issued"))["date-parts"][0][0]
    title = html.unescape(re.sub(r"<[^>]+>", "", (m.get("title") or [""])[0])).strip().rstrip(".")
    cont = html.unescape((m.get("container-title") or [""])[0])
    vol, page = m.get("volume"), m.get("page") or m.get("article-number")
    typ = m.get("type")
    if len(names) > 20:
        names = names[:19] + ["et al."]
    auth = ", ".join(names)
    if typ in ("book-chapter",):
        eds = m.get("editor", [])
        src = f"In: {cont}. {m.get('publisher', '')}, pp. {page}"
    else:
        src = f"{cont} {vol}" + (f", {page}" if page else "")
    ref = f"{auth}, {year}. {title}. {src}. https://doi.org/{m['DOI']}"
    cite = fam[0] if len(fam) == 1 else (f"{fam[0]} and {fam[1]}" if len(fam) == 2 else f"{fam[0]} et al.")
    return dict(ref=ref, cite=f"{cite}, {year}", sortkey=f"{fam[0].lower()} {year}", doi=m["DOI"])


out = {}
for k, d in DOIS.items():
    m = meta(d); out[k] = fmt(k, m)
    print(f"{k:16s} ({out[k]['cite']}) {out[k]['ref'][:150]}")
    time.sleep(0.3)
Path(__file__).with_name("pustaka_terverifikasi.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print(len(out), "referensi terformat")
