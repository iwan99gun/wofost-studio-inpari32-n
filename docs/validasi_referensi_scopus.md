# Validasi klaim dan arah riset dengan Scopus

Tanggal pencarian: 24 September 2026, Scopus via proxy perpustakaan UMPSA. Semua kueri memakai
`TITLE-ABS-KEY(...)` dan, kecuali disebut lain, `PUBYEAR > 2019`.

## 1. Volume publikasi dan jurnal utama

| Kueri (2020-2026) | Dokumen | Lima sumber teratas |
|---|---|---|
| WOFOST | 292 | Comput. Electron. Agric. 18, Agric. Water Manag. 16, **Agric. Forest Meteorol. 14**, Eur. J. Agron. 12, Agric. Systems 11 |
| DSSAT | 980 | Agric. Water Manag. 77, Eur. J. Agron. 47, Agronomy 43, Field Crops Res. 43, Agric. Systems 34 |
| APSIM | 876 | Agric. Systems 64, Field Crops Res. 55, Eur. J. Agron. 51, Agric. Water Manag. 45, Agronomy 36 |
| AquaCrop | 863 | Agric. Water Manag. 104, Agronomy 38, Irrig. Drain. 31, Water 27, Agriculture 20 |
| WOFOST AND SRCTITLE("Field Crops Research") | 8 | - |

Interpretasi:

- Klaim "WOFOST #1" **tidak terbukti dari sisi volume**: DSSAT, APSIM, dan AquaCrop masing-masing sekitar tiga kali lebih banyak.
- Klaim bahwa jurnal *Computers and Electronics in Agriculture* dan *Agricultural and Forest Meteorology* akrab dengan WOFOST **terbukti** (dua dari tiga sumber teratas). *Field Crops Research* hanya 8 dokumen sejak 2020, jadi kurang tepat disebut sebagai jurnal utama WOFOST.
- Keunggulan WOFOST yang nyata di data: kata kunci teratas hasil pencarian adalah *Crop Yield*, *Remote Sensing* (77), dan *Data Assimilation* (71). WOFOST menonjol pada asimilasi data penginderaan jauh, bukan pada volume umum.

## 2. Validasi jalur riset yang diusulkan

| Jalur | Kueri tambahan | Dokumen | Contoh referensi Q1 (sitasi Scopus) |
|---|---|---|---|
| Sensitivitas global | "sensitivity analysis" OR morris OR sobol | 31 | Paleari et al. 2021, *Ecol. Modell.* 455:109648 (58); Liu et al. 2025, *Eur. J. Agron.* 171:127807 (time-dependent SA WOFOST-Potato); Xu et al. 2021, *Int. J. Plant Prod.* 15:231 |
| Kalibrasi Bayesian / MCMC | bayesian OR mcmc OR "markov chain" | 12 | Song et al. 2024, *Agric. Forest Meteorol.* 355:110101 (24); Wu et al. 2022, *Remote Sensing* 14:3727 (19); Zheng & Zhang 2025, *Agric. Systems* 224:104215 (16) |
| Data assimilation (EnKF/4DVar) | "data assimilation" OR kalman | 85 | Zhuo et al. 2022, *Int. J. Appl. Earth Obs.* 106:102668 (135); Luo et al. 2023, *Agric. Systems* 210:103711 (122, review); Wu et al. 2021, *Remote Sens. Environ.* 255:112276 (81); Guo et al. 2024, *Field Crops Res.* 315:109477 (49) |
| Hybrid ML + WOFOST | "machine learning" OR "deep learning" OR "neural network" | 38 | Lu et al. 2025, *Agric. Forest Meteorol.* 370:110600 (49, padi); Xie et al. 2025, *Agric. Forest Meteorol.* 372:110687 (24); Ren et al. 2023, *Plants* 12:446 (56) |
| Cuaca ekstrem / heatwave | heatwave OR "heat stress" OR "extreme weather" | 12 | Zheng et al. 2025, *Geosci. Model Dev.* 18:8379 (WOFOST-EW v1); Egorov et al. 2026, *Field Crops Res.* 345:110547 (kedelai & jagung vs heatwave); Chevuru et al. 2025, *Agric. Water Manag.* 311:109403 |
| Konteks tropis / Asia Tenggara (2015-2026) | indonesia OR tropical OR "southeast asia" OR malaysia | 8 | Wanthanaporn et al. 2024, *Agric. Forest Meteorol.* 351:110001 (padi Asia Tenggara, 23); Hariadi et al. 2026, *Climatic Change* 179:60 (padi Asia Tenggara, penulis BMKG); Abadi et al. 2018, *Agrivita* 40:544 (kedelai Jawa Timur) |
| PCSE eksplisit | "python crop simulation environment" OR (pcse AND wofost) | 6 | de Wit et al. 2019, *Agric. Systems* 168:154 (445 sitasi, rujukan utama PCSE/WOFOST); Mohamed et al. 2026, *J. Agrometeorol.* 28:249 (WOFOST-PCSE) |

## 3. Implikasi untuk WOFOST Studio dan rencana publikasi

1. **Celah riset yang terkonfirmasi**: hanya 8 dokumen WOFOST bertema tropis/Asia Tenggara dan 12 bertema heatwave. Kombinasi
   "WOFOST + kalibrasi Bayesian + heatwave tropis" hampir kosong di Scopus, sehingga judul yang diusulkan berpotensi novel.
2. **Sensitivitas**: banyak makalah WOFOST memakai **EFAST** (Xing et al. 2020; Li et al. 2023). SALib menyediakan `fast_sampler`/`fast`,
   sehingga menambahkan opsi eFAST di tab Sensitivitas akan menyelaraskan aplikasi dengan praktik literatur. Paleari et al. (2021)
   mendukung Morris sebagai metode peringkat yang efektif, bukan sekadar screening.
3. **Kalibrasi**: literatur Q1 (Song et al. 2024; Wu et al. 2022) memakai inferensi Bayesian (posterior), bukan least-squares.
   Tab Kalibrasi saat ini (least-squares/Nelder-Mead) cocok sebagai tahap awal; MCMC (emcee/pyDREAM) perlu ditambahkan untuk
   klaim "Bayesian calibration".
4. **Data assimilation** adalah jalur dengan jumlah dan sitasi tertinggi (85 dokumen; makalah 135 dan 122 sitasi). Modul
   `SimulationRunner` sudah mendukung override parameter per run, tetapi EnKF membutuhkan akses state harian di tengah simulasi
   (PCSE `run(days)` + `set_variable`), yang belum diekspos di UI.
5. **Positioning naskah**: hindari klaim "WOFOST paling banyak dipakai". Argumen yang didukung data: WOFOST adalah model standar
   untuk asimilasi data penginderaan jauh dan pemantauan hasil regional (MARS/JRC), tersedia sebagai pustaka Python murni (PCSE),
   dan dirujuk 445 kali lewat de Wit et al. (2019).

## 4. String kueri untuk direproduksi

```
TITLE-ABS-KEY(WOFOST) AND PUBYEAR > 2019
TITLE-ABS-KEY(WOFOST) AND TITLE-ABS-KEY("sensitivity analysis" OR morris OR sobol) AND PUBYEAR > 2019
TITLE-ABS-KEY(WOFOST) AND TITLE-ABS-KEY(bayesian OR mcmc OR "markov chain") AND PUBYEAR > 2019
TITLE-ABS-KEY(WOFOST) AND TITLE-ABS-KEY("data assimilation" OR kalman) AND PUBYEAR > 2019
TITLE-ABS-KEY(WOFOST) AND TITLE-ABS-KEY("machine learning" OR "deep learning" OR "neural network") AND PUBYEAR > 2019
TITLE-ABS-KEY(WOFOST) AND TITLE-ABS-KEY(heatwave OR "heat wave" OR "heat stress" OR "extreme weather" OR "extreme heat") AND PUBYEAR > 2019
TITLE-ABS-KEY(WOFOST) AND TITLE-ABS-KEY(indonesia OR tropical OR tropics OR "southeast asia" OR malaysia) AND PUBYEAR > 2014
TITLE-ABS-KEY("python crop simulation environment" OR (pcse AND wofost))
```
