# Validasi fitur lanjutan WOFOST Studio terhadap literatur

Tanggal: 25 September 2026. Sumber: halaman penerbit terbuka (ScienceDirect, Copernicus GMD, MDPI, Elsevier
artwork policy). Sesi proxy Scopus UMPSA kedaluwarsa saat validasi ini, sehingga artikel diakses langsung lewat DOI.

## 1. Asimilasi data EnKF (tab 6)

| Rancangan aplikasi | Literatur | Status |
|---|---|---|
| Ansambel dari perturbasi Gaussian/lognormal parameter tanaman, observasi LAI diperturbasi (Burgers et al. 1998), analisis skalar K = P/(P+R) | Guo et al. 2024, *Field Crops Res.* 315:109477: perturbasi Gaussian pada **TDWI dan SPAN**, observasi LAI UAV diperturbasi Gaussian, operator observasi identitas, persamaan analisis EnKF standar | Sesuai |
| Ukuran ansambel default | Guo et al. 2024 menguji 50/100/150/200 anggota; akurasi terbaik pada **100** (galat absolut 132 kg/ha, relatif 2,01 %) | Default diubah 30 -> **100**; perturbasi default TDWI, SPAN, TSUM1 |
| Opsi inflasi kovarians | de Wit & van Diepen 2007, *Agric. Forest Meteorol.* 146:38-56: inovasi ternormalisasi EnKF-WOFOST tidak Gaussian, rata-rata tidak nol, sebaran berlebih -> kovarians forecast dan observasi diremehkan | Ditambahkan kolom **inovasi ternormalisasi** per tanggal dan ringkasannya (rata-rata dan SD) sebagai diagnostik; inflasi > 1 disarankan bila SD > 1 |
| Update state saja (parameter tetap) | Song et al. 2024, *Agric. Forest Meteorol.* 355:110101: inferensi Bayesian dua-langkah (parameter + state) mengalahkan EnKF standar (RMSE 1112 vs 1328 kg/ha) | Belum ada; jalur pengembangan: gabungkan tab 5 (MCMC) dan tab 6 |

## 2. Analisis sensitivitas (tab 4)

- Paleari et al. 2021, *Ecol. Modell.* 455:109648: pada WOFOST (padi), peringkat parameter Morris konkordan
  dengan E-FAST (signifikan p < 0,10 untuk fenologi) dengan < 3 % jumlah eksekusi. Mendukung Morris sebagai
  metode peringkat, bukan sekadar screening. **Sesuai** dengan pilihan default Morris di aplikasi.
- Li et al. 2023, *Agronomy* 13:2294: EFAST pada WOFOST gandum; parameter paling sensitif TMNFTB, SPAN, SLATB,
  CFET. SPAN juga muncul dominan pada uji padi di aplikasi ini. Catatan: TMNFTB/SLATB adalah parameter **tabel**
  (AFGEN) yang belum bisa dipilih di aplikasi (hanya parameter skalar). Ini keterbatasan yang perlu disebut di naskah
  atau ditambahkan (perturbasi tabel dengan faktor pengali).

## 3. Kalibrasi Bayesian MCMC (tab 5)

- Song et al. 2024 memakai inferensi Bayesian untuk parameter WOFOST dengan observasi LAI Sentinel-2. Likelihood
  Gaussian dengan kesalahan observasi relatif (default 10 %) di aplikasi adalah pilihan standar; pilihan
  kesalahan observasi perlu dilaporkan sebagai analisis sensitivitas prior/likelihood di naskah.

## 4. Skenario iklim dan gelombang panas (tab 7)

- Zheng et al. 2025, *Geosci. Model Dev.* 18:8379-8400 (WOFOST-EW): model berbasis proses "sering kesulitan
  mensimulasikan dampak cuaca ekstrem secara akurat"; WOFOST asli R2 hasil 0,61-0,71 pada tahun ekstrem vs 0,80-0,86
  setelah ditambah indeks cuaca ekstrem + deep learning. **Mengonfirmasi** peringatan di tab 7 bahwa dampak heatwave
  WOFOST murni adalah batas bawah.
- Toda et al. 2026, *Field Crops Res.*: sterilitas spikelet padi akibat panas saat pembungaan dihitung dari suhu
  malai dan relasi empiris sterilitas-suhu; mekanisme ini tidak ada di WOFOST. Aplikasi kini menambahkan
  **pasca-proses sterilitas empiris** tipe Horie sebagai kolom TWSO_sterilitas terpisah dari TWSO WOFOST.
- Sun et al. 2025, *Eur. J. Agron.* (S1161-0301(25)00245-X) **mengonfirmasi bentuk dan parameter fungsi**: seed-setting
  rate SR = 1/(1+exp(0,853 (Tm,a - T50))) (Horie 1993; Yoshida & Horie 2009) dipakai di APSIM-Oryza, DNDC-Rice,
  ORYZA v3, SIMRIW dengan T50 = 36,6 C; T50 bervariasi 34,9-43,2 C antar varietas (indica hibrida vs japonica).
  Di aplikasi a dan T50 dapat diubah; Tm,a dihitung dari Tmax harian pada jendela antesis +/- 5 hari.
- Wanthanaporn et al. 2024, *Agric. Forest Meteorol.* 351:110001: pada padi Asia Tenggara dengan WOFOST,
  ketersediaan air bukan faktor utama skill prediksi hasil, suhu lebih berpengaruh. Konsisten dengan hasil uji
  aplikasi: skenario hujan -30 % tidak mengubah hasil musim hujan Jawa Barat, sedangkan +1 s.d. +6 C menurunkan
  hasil 2-15 %.

## 5. Ekspor figur (tombol "Figur jurnal...")

Elsevier *Artwork sizing*: kolom tunggal **90 mm** (255 pt), 1,5 kolom **140 mm**, kolom ganda **190 mm** (539 pt);
resolusi **300 dpi halftone, 500 dpi kombinasi, 1000 dpi line art**. Preset aplikasi disesuaikan (default line art
1000 dpi; PDF/SVG/EPS vektor tetap tersedia).

## 6. Keterbatasan: status setelah perbaikan (25 September 2026)

| Keterbatasan awal | Status | Cara perbaikan di aplikasi |
|---|---|---|
| Parameter tabel AFGEN (TMNFTB, SLATB, AMAXTB, TMPFTB, ...) tidak bisa dianalisis | **Diperbaiki** | Parameter virtual `NAMA@y` (pengali nilai-y) untuk 10 tabel dan `NAMA@x` (geseran suhu, C) untuk TMPFTB, TMNFTB, DTSMTB, EFFTB; tersedia di override, sensitivitas, kalibrasi, MCMC, dan EnKF. TMPFTB/TMNFTB di-clip 0-1. Uji Morris: AMAXTB@y menjadi parameter paling berpengaruh pada hasil padi (mu* 1372), TMPFTB@x berpengaruh nyaris linear (sigma 20). |
| EnKF hanya memperbarui state, parameter tetap (Song et al. 2024 menunjukkan inferensi gabungan lebih baik) | **Diperbaiki** | Opsi **ES-MDA** (Emerick & Reynolds 2013): ensemble smoother dengan inflasi R sebanyak N iterasi memperbarui parameter ansambel (log-ruang untuk parameter positif, linear untuk @x) memakai semua observasi, lalu EnKF pada state. Tabel "Parameter anggota" memuat prior dan posterior. Uji: SD posterior TDWI turun 8,8 -> 1,7; SPAN 3,0 -> 1,7. Catatan: skema dua-langkah ini ansambel-Gaussian, bukan MCMC penuh seperti Song et al.; sebut sebagai "iterative ensemble smoother + EnKF". |
| Dampak heatwave belum dibandingkan dengan data lapangan | **Tidak bisa diganti kode**; alat validasi disiapkan | Tab Batch kini menerima file hasil observasi (tanggal_tanam, TWSO_obs, lokasi) dan menghasilkan figur 1:1 plus metrik standar naskah crop-model: RMSE, nRMSE, bias, R2, r, d-Willmott, EF Nash-Sutcliffe. Yang masih dibutuhkan: data hasil panen multi-musim/lokasi (BPS, Balai Besar Padi, atau percobaan sendiri) dan idealnya LAI lapangan. |
| Interval kepercayaan eFAST dari SALib indikatif | Tetap | Laporkan S1/ST eFAST tanpa CI, atau gunakan Sobol (CI bootstrap sahih). |

Implikasi untuk naskah: semua metode kini dapat mencakup parameter fisiologis penuh WOFOST (skalar + tabel),
sehingga klaim "global sensitivity analysis of WOFOST" dan "joint parameter-state assimilation" dapat dipertahankan
di hadapan reviewer. Validasi lapangan tetap menjadi syarat yang tidak bisa dilewati untuk jurnal Q1.

## 7. WOFOST 8.1 terbatas nitrogen (25 September 2026)

- Model `Wofost81_NWLP_CWB_CNB` ditambahkan (PCSE 6.0.13). Parameter tanaman diambil dari salinan lokal cabang
  `wofost81` repositori resmi (`data/crop_params/`), bukan unduhan daring saat runtime, agar tereproduksi.
- Ketidaksesuaian upstream: modul asimilasi 8.1 di PCSE 6.0.13 memerlukan AMAX_REF dan KN yang belum ada di berkas
  parameter mana pun (cabang wofost81/wofost80/develop, diperiksa 25 Sep 2026). WOFOST Studio mengisi default
  (AMAX_REF = maks AMAXTB; KN = 0,4, koefisien pemadaman N tajuk umum untuk padi/serealia) dan menampilkannya sebagai
  parameter yang dapat di-override. Ini harus disebut di bagian metode naskah.
- Pemupukan N dijadwalkan lewat sinyal `apply_n` (N_amount x N_recovery). Parameter N tanah (NAVAILI, NSOILBASE,
  NSOILBASE_FR, BG_N_SUPPLY) ada di tabel lokasi; diabaikan oleh model 7.2/7.3.
- Semua analisis (sensitivitas, kalibrasi, MCMC, EnKF, skenario) berjalan pada model 8.1 karena memakai
  SimulationRunner yang sama; parameter N (NMAXLV_TB@y, NSLLV_TB@y, RGRLAI_MIN, NMAXSO, RNUPTAKEMAX, AMAX_REF, KN)
  ikut muncul di daftar parameter.
- Studi kasus dan hasil kalibrasi respons N Inpari-32: docs/data_sekunder.md bagian 6.
- Parameter virtual `RGRLAI_MIN_FR` (RGRLAI_MIN = FR x RGRLAI) mencegah RGRLAI_MIN > RGRLAI setelah kalibrasi
  (sebelumnya cekaman N mempercepat pertumbuhan daun juvenil).
- Model ekstensi opsional `Wofost81_NWLP_CWB_CNB_NLV`: efek N pada SLA dan fraksi daun tipe LINTUL3 (Shibu et al. 2010,
  Agric. Syst. 103:113-125), NSLA/NPART default 1,0 (nilai bawaan LINTUL3 di PCSE). Terbukti identik dengan 8.1 bila
  koefisien 0. Perbandingan dengan 8.1 standar: docs/data_sekunder.md bagian 6b.
