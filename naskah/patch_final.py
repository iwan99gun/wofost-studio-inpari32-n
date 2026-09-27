"""Tambah mode 'final' pada buat_naskah.py: naskah bersih untuk diunggah ke Editorial Manager
(tanpa catatan draf/jurnal target di halaman judul, tanpa sorot kuning, nama berkas Manuscript_EJA.docx,
tanpa konversi PDF)."""
from pathlib import Path

F = Path(__file__).resolve().parent / "buat_naskah.py"
s = F.read_text(encoding="utf-8")

# 1. flag
old = 'BACA = "baca" in sys.argv[1:]\n'
new = 'BACA = "baca" in sys.argv[1:]\nFINAL = "final" in sys.argv[1:]\n'
assert old in s and "FINAL =" not in s
s = s.replace(old, new, 1)

# 2. buang dua baris catatan draf di halaman judul pada mode final
old = ('P("DRAFT manuscript generated from WOFOST Studio results on " + dt.date.today().strftime("%d %B %Y")\n'
       '  + ". Text highlighted in yellow must be verified or completed by the authors before submission.", italic=True, size=9, verify=True)\n'
       'P("Target journal: European Journal of Agronomy (alternatives: Agricultural Systems; Environmental Modelling & Software).", italic=True, size=9)\n')
new = ('if not FINAL:\n'
       '    P("DRAFT manuscript generated from WOFOST Studio results on " + dt.date.today().strftime("%d %B %Y")\n'
       '      + ". Text highlighted in yellow must be verified or completed by the authors before submission.", italic=True, size=9, verify=True)\n'
       '    P("Target journal: European Journal of Agronomy (alternatives: Agricultural Systems; Environmental Modelling & Software).", italic=True, size=9)\n')
assert old in s, "catatan draf"
s = s.replace(old, new, 1)

# 3. nama berkas + lewati PDF pada mode final
old = 'docx_path = OUT / ("draft_WOFOST81_Nrice_WestJava_versi_baca.docx" if BACA else "draft_WOFOST81_Nrice_WestJava.docx")'
new = ('docx_path = OUT / ("Manuscript_EJA.docx" if FINAL else ("draft_WOFOST81_Nrice_WestJava_versi_baca.docx" if BACA else "draft_WOFOST81_Nrice_WestJava.docx"))')
assert old in s, "docx_path"
s = s.replace(old, new, 1)

old = 'print("DOCX:", docx_path)\n'
new = 'print("DOCX:", docx_path)\nif FINAL:\n    raise SystemExit(0)\n'
assert old in s
s = s.replace(old, new, 1)
F.write_text(s, encoding="utf-8")
print("patch final ok")
