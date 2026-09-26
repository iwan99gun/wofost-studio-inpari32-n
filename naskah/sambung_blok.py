"""Sambungkan blok teks baru ke buat_naskah.py (sekali jalan; membuat cadangan buat_naskah_v1.py)."""
from pathlib import Path
D = Path(__file__).parent
src = (D / "buat_naskah.py").read_text(encoding="utf-8")
(D / "buat_naskah_v1.py").write_text(src, encoding="utf-8")
b1 = (D / "blok_1_awal.py").read_text(encoding="utf-8")
b2 = (D / "blok_2_hasil.py").read_text(encoding="utf-8")
b3 = (D / "blok_3_hasil36.py").read_text(encoding="utf-8")
b4 = (D / "blok_4_diskusi.py").read_text(encoding="utf-8")


def cut(s, start, end):
    i = s.index(start); j = s.index(end, i)
    return s[:i], s[j:]


# 1) highlights + abstrak + pendahuluan
pre, post = cut(src, 'H("Highlights")', "# ================================================================== 2 Methods")
src = pre + b1 + "\n" + post
# 2) 2.10 setelah 2.9
pre, post = cut(src, "# ================================================================== 3 Results", "# ================================================================== 3 Results")
src = pre + b2 + "\n" + post
# 3) 3.6 sebelum diskusi, 4) diskusi & kesimpulan baru
pre, post = cut(src, "# ================================================================== 4 Discussion", 'H("Software and data availability")')
src = pre + b3 + "\n# ================================================================== 4 Discussion\n" + b4 + "\n" + post
# 5) daftar pustaka gabungan
i = src.index("REFS = ["); j = src.index("# ================================================================== lampiran")
old_block = src[i:j]
refs_list = old_block[:old_block.index("\nfor txt, v in REFS:")]
new_block = refs_list + '''
REFS = [(t, v) for t, v in REFS if not t.startswith("Berghuijs")]
REFS += [(PUS[k]["ref"], False) for k in PUS]
REFS.sort(key=lambda x: x[0].lower().replace("'", ""))
N_REFS = len(REFS)
for txt, v in REFS:
    p = P(txt, verify=v, size=8 if BACA else None); p.paragraph_format.line_spacing = 1.0 if BACA else 1.15
    p.paragraph_format.left_indent = Cm(0.6); p.paragraph_format.first_line_indent = Cm(-0.6)

'''
src = src[:i] + new_block + src[j:]
# 6) sitasi tambahan di metode
reps = [
    ("pixel level with axis calibration on four major ticks;", "pixel level with axis calibration on four major ticks, a procedure with high reported reliability \" + C(\"drevon2017\") + \";"),
    ("NASA POWER was \"\n  \"used as an alternative source to quantify weather uncertainty.",
     "NASA POWER was \"\n  \"used as an alternative source to quantify weather uncertainty \" + C(\"vanwart2013\", \"bai2010\") + \"."),
    ("P(\"(ii) Photosynthesis. WOFOST 8.1 computes maximum leaf photosynthesis from AMAX_REF and specific leaf N and does not \"",
     "P(\"(ii) Photosynthesis. WOFOST 8.1 computes maximum leaf photosynthesis from AMAX_REF and specific leaf N \" + C(\"evans1989\", \"hikosaka2016\") + \" and does not \""),
    ("\"(Foreman-Mackey et al., 2013; 16 walkers,", "\"(Foreman-Mackey et al., 2013), as in Bayesian calibration of rice models \" + C(\"iizumi2009\") + \" (16 walkers,"),
]
for a, b in reps:
    if a not in src:
        raise SystemExit("MISS: " + a[:70])
    src = src.replace(a, b)
(D / "buat_naskah.py").write_text(src, encoding="utf-8")
print("tersambung")
