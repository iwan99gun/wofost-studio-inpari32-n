"""Paket unggahan untuk Nutrient Cycling in Agroecosystems (Springer) -> D:/riset_tani_1/SUBMISSION_NCA/
Urutan: python buat_naskah.py nca  ->  python buat_paket_nca.py
Isi: naskah (docx), Supplementary Information (docx+pdf), Fig1-3 (tif+png), surat pengantar dengan 5 calon reviewer
(wajib), DATA_FORMULIR.txt, CHECKLIST.txt."""
import shutil, datetime as dt, re
from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

HERE = Path(__file__).resolve().parent
NCA = HERE / "nca"
PKG = HERE.parent / "SUBMISSION_NCA"
if PKG.exists():
    shutil.rmtree(PKG)
(PKG / "Figures").mkdir(parents=True)

src = Document(NCA / "NCA_Manuscript.docx")
paras = [p.text for p in src.paragraphs]
TITLE = paras[0]
abstract = paras[paras.index("Abstract") + 1]
kw = next(t for t in paras if t.startswith("Keywords ")).replace("Keywords ", "").split(" \u00b7 ")
rep = (NCA / "laporan_kepatuhan.txt").read_text(encoding="utf-8").split("\n\nSITASI")[0]
n_words = int(re.search(r"\+ abstrak = (\d+)", rep).group(1))

# ---- kandidat reviewer (kontak diverifikasi dari sumber resmi pada 29 Sep 2026; lihat CHECKLIST)
REVIEWERS = [
    ("Dr Allard de Wit", "Wageningen Environmental Research, Wageningen University & Research, the Netherlands",
     "allard.dewit@wur.nl", "lead developer of WOFOST and PCSE; crop model development and data assimilation"),
    ("Dr Kazuki Saito", "International Rice Research Institute (IRRI), Los Ba\u00f1os, Philippines",
     "k.saito@cgiar.org", "rice agronomy, nutrient management and yield-gap analysis in irrigated rice"),
    ("Prof. Shaobing Peng", "Huazhong Agricultural University, Wuhan, China",
     "speng@mail.hzau.edu.cn", "rice nitrogen physiology, leaf nitrogen and nitrogen-use efficiency"),
    ("Prof. Gerrit Hoogenboom", "University of Florida, Gainesville, USA",
     "gerrit@ufl.edu", "development, calibration and evaluation of process-based crop models (DSSAT)"),
    ("Dr Heidi Webber", "Leibniz Centre for Agricultural Landscape Research (ZALF), M\u00fcncheberg, Germany",
     "webber@zalf.de", "evaluation and uncertainty of process-based crop models"),
]

# ---- surat pengantar
d = Document()
s = d.sections[0]; s.page_width, s.page_height = Cm(21), Cm(29.7)
for a in ("top_margin", "bottom_margin", "left_margin", "right_margin"):
    setattr(s, a, Cm(2.5))
st = d.styles["Normal"]; st.font.name = "Arial"; st.font.size = Pt(10.5)
st.paragraph_format.space_after = Pt(7); st.paragraph_format.line_spacing = 1.12


def P(t, bold=False, italic=False, align=None):
    p = d.add_paragraph(); r = p.add_run(t); r.bold = bold; r.italic = italic
    if align is not None:
        p.alignment = align
    return p


P(dt.date.today().strftime("%d %B %Y"), align=WD_ALIGN_PARAGRAPH.RIGHT)
P("Dr Else K. B\u00fcnemann-K\u00f6nig and Dr Florian Wichern\nEditors-in-Chief, Nutrient Cycling in Agroecosystems")
P("Dear Editors,", bold=True)
P(f'Please consider our manuscript "{TITLE}" for publication as a full paper in Nutrient Cycling in Agroecosystems.')
P("The manuscript addresses two elements of the nitrogen cycle of irrigated rice that determine fertiliser "
  "recommendations: the indigenous nitrogen supply of the soil and the way the crop adjusts its canopy to nitrogen "
  "deficiency. It evaluates the nitrogen-limited crop model WOFOST 8.1 against published field observations from seven "
  "experiments or seasons at five locations in two provinces of Indonesia, including two seasons of nitrogen-omission plots from a long-term fertility "
  "experiment running since 1994. We believe it fits the scope of the journal because its conclusions are mechanistic and "
  "of general applicability rather than local:")
P("1. Rice conserved leaf nitrogen per unit area and reduced leaf area under nitrogen deficiency, whereas the model kept "
  "leaf area and diluted leaf nitrogen. Both routes give similar yields, so yield alone cannot validate a nitrogen module. "
  "A one-parameter extension reproduced the observed leaf-area response in two independent datasets predicted blind.")
P("2. Indigenous nitrogen supply estimated from omission plots was stable over five years within a field but differed "
  "between fields and sites with the same soil-test class, which supports the omission-plot approach over transfer of "
  "soil nitrogen supply between fields.")
P("3. Recalibrating a subset of parameters created three inconsistencies with default parameters that inverted or "
  "disabled the simulated nitrogen response. These are relevant to any user of the model.")
P("We state openly that all observations are secondary data extracted from peer-reviewed publications; no new field "
  "experiment was conducted. Every extracted value, the model code and all analysis scripts are openly archived "
  "(https://doi.org/10.5281/zenodo.22969838), so that every number in the manuscript can be regenerated.")
P(f"The manuscript has about {round(n_words, -2):,} words excluding references, three figures and five tables in the main "
  "text, and Supplementary Information. It has not been published before and is not under consideration elsewhere, and "
  "both authors have approved the submission. The use of generative artificial-intelligence tools is documented in the "
  "Methods section. The authors have no competing interests, and no funding was received.")
P("As requested in the submission guidelines, we suggest the following five reviewers, from five countries and five "
  "institutions. To our knowledge none of them has a conflict of interest with the authors:")
for i, (n, aff, em, ex) in enumerate(REVIEWERS, 1):
    P(f"{i}. {n}, {aff}; {em}. Expertise: {ex}.")
P("Thank you for considering our work.")
P("Yours sincerely,")
P("Zainal Arifin (responsible corresponding author)\n"
  "Department of Agribusiness, Vocational School, Universitas Sebelas Maret, Surakarta, Indonesia\n"
  "zainal.arifin@staff.uns.ac.id")
P("Iwan Gunawan (corresponding author)\n"
  "Department of Mechanical Engineering, Universitas Khairun, Ternate 97719, Indonesia\n"
  "iwan99gun@unkhair.ac.id")
d.save(PKG / "03_Cover_letter.docx")

# ---- berkas
shutil.copy(NCA / "NCA_Manuscript.docx", PKG / "01_Manuscript.docx")
shutil.copy(NCA / "NCA_Supplementary_Information.docx", PKG / "02_Supplementary_Information.docx")
if (NCA / "NCA_Supplementary_Information.pdf").exists():
    shutil.copy(NCA / "NCA_Supplementary_Information.pdf", PKG / "02_Supplementary_Information.pdf")
if (NCA / "NCA_Manuscript.pdf").exists():
    shutil.copy(NCA / "NCA_Manuscript.pdf", PKG / "01_Manuscript_untuk_dibaca.pdf")
for f in sorted((NCA / "Figures").glob("Fig*.*")):
    shutil.copy(f, PKG / "Figures" / f.name)

# ---- data formulir
form = f"""DATA UNTUK FORMULIR SUBMISSION - Nutrient Cycling in Agroecosystems (salin-tempel)
====================================================================================
Tipe artikel : Full paper (Original Article)
Judul ({len(TITLE)} karakter; batas 90):
{TITLE}

Penulis (urutan sama dengan naskah):
  1. Zainal Arifin  (PENANGGUNG JAWAB UTAMA korespondensi: dipilih di dropdown "responsible corresponding author")
     Department of Agribusiness, Vocational School, Universitas Sebelas Maret, Surakarta, Indonesia
     zainal.arifin@staff.uns.ac.id   ORCID 0009-0008-0345-3167
  2. Iwan Gunawan  (penulis korespondensi TAMBAHAN: dicentang di "other corresponding authors"; juga yang mengunggah)
     Department of Mechanical Engineering, Universitas Khairun, Ternate 97719, Indonesia
     iwan99gun@unkhair.ac.id         ORCID 0000-0002-2784-4436

Abstrak ({len(abstract.split())} kata; batas 150-250):
{abstract}

Kata kunci ({len(kw)}; batas 4-6):
{"; ".join(kw)}

PERNYATAAN YANG DIISI DI FORMULIR (jurnal memakai isi formulir, bukan isi naskah, untuk versi terbit):
Competing interests : The authors have no relevant financial or non-financial interests to disclose.
Funding             : The authors declare that no funds, grants, or other support were received during the preparation of this manuscript.
Author contributions: I.G. developed the WOFOST Studio software, the nitrogen extension and the analysis scripts. Z.A. and I.G. performed the literature search and reference compilation, wrote the manuscript and edited it. Both authors read and approved the final manuscript.
   (Formulir Springer meminta inisial; pernyataan ini menggantikan yang ada di naskah dan itulah yang diterbitkan.)

DATA INSTITUSI UNTUK LANGKAH "Affiliated institutions" (Save institution information untuk masing-masing):
  1. Institution name: Universitas Sebelas Maret | country: Indonesia | city: Surakarta | details: Department of Agribusiness, Vocational School
  2. Institution name: Universitas Khairun       | country: Indonesia | city: Ternate   | details: Department of Mechanical Engineering
Data availability   : All datasets extracted from the literature, the model code, the analysis scripts and the simulation results that support the findings of this study are openly available in Zenodo at https://doi.org/10.5281/zenodo.22969838 and at https://github.com/iwan99gun/wofost-studio-inpari32-n (MIT licence).

CALON REVIEWER (formulir meminta minimal 5 nama + kontak; sama dengan surat pengantar):
""" + "\n".join(f"  {i}. {n} | {aff} | {em}\n     keahlian: {ex}" for i, (n, aff, em, ex) in enumerate(REVIEWERS, 1)) + "\n"
(PKG / "DATA_FORMULIR.txt").write_text(form, encoding="utf-8")

chk = f"""CHECKLIST - Nutrient Cycling in Agroecosystems (Springer)
Halaman jurnal : https://link.springer.com/journal/10705   (tombol "Submit manuscript")
=====================================================================================
KEPATUHAN TERHADAP PANDUAN (diperiksa otomatis saat naskah dirakit)
{rep}

YANG HARUS DIPUTUSKAN / DILAKUKAN PENULIS SEBELUM UNGGAH
 [ ] CALON REVIEWER. Lima nama di surat pengantar adalah USULAN saya berdasarkan keahlian; kontaknya saya verifikasi dari
     sumber resmi (metadata paket PCSE, halaman University of Nebraska, dan alamat korespondensi di artikel terbit).
     Anda berdua yang memutuskan. Ganti siapa pun yang pernah bekerja sama dengan Anda atau yang Anda anggap tidak tepat.
     Syarat jurnal: 5 orang, negara dan institusi beragam, minimal 3 dari luar Indonesia.
     Panduan Springer: reviewer harus "totally independent and not connected to the work in any way", dengan surel
     institusi. Karena itu Patricio Grassini TIDAK diusulkan (ia rekan penulis sumber data Agustiani et al. 2018).
     Allard de Wit adalah pengembang model yang diuji; ia tidak terkait dengan naskah ini, tetapi pertimbangkan sendiri.
 [ ] SIAPA YANG MENGUNGGAH. Panduan Springer mengizinkan komunikasi selama submission didelegasikan ke "Contact or
     Submitting Author" yang berbeda dari Corresponding Author, asal Corresponding Author jelas tertulis di naskah
     (sudah: Zainal Arifin). Jadi Iwan boleh login dan mengunggah; di formulir penulis, tandai ZAINAL sebagai
     corresponding author. Penulis korespondensi tidak bisa diganti setelah naskah diterima.
 [ ] ZENODO. Naskah merujuk DOI semua-versi 10.5281/zenodo.22969838. Arsip Zenodo yang ada (v1.0.0, 26 Sep) BELUM memuat
     skrip dan data terbaru (MCMC konvergen, validasi Karangploso, versi naskah ini). Unggah versi baru di Zenodo:
     buka rekam Zenodo -> "New version" -> unggah zip rilis v1.1.0 dari GitHub -> Publish. Tambahkan juga Zainal Arifin
     sebagai penulis di rekam itu.
 [ ] PENGGUNAAN AI. Springer meminta penggunaan model bahasa didokumentasikan di bagian Metode; sudah ada di Bagian 2.11.
     Nama alat tidak disebut, sesuai keputusan Anda. Editor bisa meminta nama alatnya.
 [ ] Saat submit, formulir menanyakan kesediaan menelaah hingga dua naskah untuk jurnal ini. Itu keputusan Zainal.
 [ ] Pilih jalur SUBSCRIPTION (tanpa biaya) bila ditanya; Open Choice berbayar.
 [ ] Kedua penulis sudah membaca dan menyetujui naskah final. Naskah ini TIDAK boleh sedang dipertimbangkan di jurnal lain.

BERKAS YANG DIUNGGAH
 1. Manuscript                 -> 01_Manuscript.docx   (halaman judul, abstrak, teks, tabel, keterangan gambar,
                                   pernyataan, pustaka, lalu gambar satu per lembar di akhir)
 2. Figure (satu per berkas)   -> Figures/Fig1.tif, Fig2.tif, Fig3.tif
 3. Supplementary Information  -> 02_Supplementary_Information.docx (atau .pdf)
 4. Cover letter               -> 03_Cover_letter.docx
 Setelah sistem membuat PDF gabungan, PERIKSA dulu (tabel, gambar, nomor baris) sebelum menyetujui.

CATATAN JUJUR TENTANG RISIKO
 Panduan jurnal menyebut full paper "biasanya berdasarkan observasi lapangan multi-tahun" dengan data orisinal.
 Naskah ini memakai data sekunder dari publikasi. Halaman cakupan jurnal menerima studi pemodelan, tetapi editor tetap
 bisa menilai naskah tidak cocok. Surat pengantar menyatakan hal ini secara terbuka.
"""
(PKG / "CHECKLIST.txt").write_text(chk, encoding="utf-8")
for p in sorted(PKG.rglob("*")):
    if p.is_file():
        print(f"{str(p.relative_to(PKG)):45s} {p.stat().st_size / 1024:7.0f} KB")
print("paket:", PKG)
