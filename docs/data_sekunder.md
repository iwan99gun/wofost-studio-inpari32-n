# Data sekunder (literature-derived) untuk kalibrasi dan validasi

Disusun 25 September 2026 dari halaman penuh ScienceDirect (akses institusi UMPSA). Semua nilai yang dibaca dari
grafik ditandai sebagai digitasi visual dengan ketidakpastiannya. Pengguna wajib memverifikasi ulang terhadap
sumber asli sebelum dipakai di naskah.

## 1. Agustiani et al. (2018), *European Journal of Agronomy* 101:10-19

DOI 10.1016/j.eja.2018.08.002. Percobaan hasil tinggi (HY) Balai Besar Padi (ICRR), musim kemarau 2016, varietas
**Inpari 32**, tiga lokasi Jawa Barat, 4 ulangan, plot 30 m2, kepadatan 16 dan 21 rumpun/m2, N 126 P 11 K 25 kg/ha,
genangan 5 cm (mendekati potensial). Sampel destruktif pada 7, 67 (10 % pembungaan), dan 112 HST (masak fisiologis).

| Lokasi | Lintang | Bujur | Catatan |
|---|---|---|---|
| Subang | -6.624 | 107.746 | |
| Indramayu | -6.518 | 108.291 | |
| Bandung | -7.011 | 107.746 | cekaman air saat pengisian biji; dataran tinggi |

Nilai observasi dari **digitasi piksel** Fig. 3 (skrip: deteksi marker berwarna, kalibrasi sumbu-y dari empat tick mayor,
klasifikasi bentuk marker dari rasio isi kotak pembatas; 1 piksel = 0,025 Mg/ha TAGP, 0,012 Mg/ha batang, 0,007 LAI;
ketidakpastian pusat marker +/- 3 piksel digabung kuadratis dengan SD percobaan):

| Lokasi | TAGP 67 | TAGP 112 | Batang 67 | Batang 112 | LAI 67 | LAI 112 |
|---|---|---|---|---|---|---|
| Subang | 7,37 | 17,12 | 4,07 | 7,52 | 5,04 | 2,15 |
| Indramayu | 6,43 | 14,09 | 4,80 | 5,77 | 4,50 | 1,90 |
| Bandung | 8,52 | 15,11 | 7,06 | 7,41 | 4,62 | 2,22 |

(Mg/ha untuk biomassa; 7 HST: TAGP 0,11, batang 0,09, LAI 0,08 rata-rata tiga lokasi karena marker tumpang tindih.)
Perbedaan terhadap bacaan visual awal <= 0,25 Mg/ha dan <= 0,06 LAI. SD observasi antar ulangan (teks): TAGP 1,1 Mg/ha,
batang 0,6 Mg/ha, LAI 0,2, sehingga ketidakpastian total didominasi SD percobaan, bukan digitasi. Hasil gabah 7,8-10
Mg/ha (14 % KA), tidak dilaporkan per lokasi.

**Tanggal tanam pindah tidak dilaporkan** (hanya April-September). Diperlakukan sebagai ketidakpastian terukur:
19 tanggal tanam (1 April s.d. 30 Juni 2016, langkah 5 hari) disimulasikan dengan prior ORYZA
(`data/lapangan/sensitivitas_tanggal_tanam_2016.csv`):

| Lokasi | Umur berbunga (HST) | Umur masak (HST) | TWSO (kg/ha) | LAImax |
|---|---|---|---|---|
| Subang | 53-55 | 87-89 | 7195-8794 | 6-7 |
| Indramayu | 50-52 | 82-84 | 6682-7691 | 6-7 |
| Bandung | 60-62 | 99-102 | 8555-10138 | 7-8 |

Fenologi dalam HST hanya bergeser 1-2 hari sepanjang jendela tiga bulan (iklim tropis, suhu stabil), sehingga kalibrasi
TSUM dari DVS tidak sensitif terhadap tanggal; hasil bergeser +/- 10 %. Kesimpulan untuk naskah: asumsi tanggal
memengaruhi hasil dan LAI (dilaporkan sebagai rentang), tidak memengaruhi parameter fenologi. Sumber tanggal sebenarnya:
makalah pendamping Agustiani et al. (2018) *J. Penelitian Pertanian Tanaman Pangan* 2(3):145-153,
DOI 10.21082/JPPTP.V2N3.2018.P145-153 (percobaan yang sama, Inpari-32 dan Hipa-18, musim kemarau 2016, Bandung, Subang,
Indramayu, split plot 6 ulangan) - server ejurnal.litbang.pertanian.go.id tidak dapat dijangkau dari mesin ini dan
academia.edu memerlukan login; unduh manual, tanggal tanam biasanya ada di Bahan dan Metode.

Konversi fenologi ORYZA v3 (Tabel 2) ke WOFOST: DVRJ 0,0008753, DVRI 0,0007576, DVRP 0,0007787, DVRR 0,0015390
(per C.d, Tbase 8, Topt 30, Thigh 42,5, sama dengan DTSMTB padi PCSE) memberi **TSUM1 = 0,4/DVRJ + 0,25/DVRI +
0,35/DVRP = 1236 C.d** dan **TSUM2 = 1/DVRR = 650 C.d**. Nilai ini dipakai sebagai prior/override di proyek
`data/projects/agustiani2018_<lokasi>_inpari32.json`, dan dikalibrasi ulang terhadap DVS = 1 (67 HST) dan DVS = 2 (112 HST).

MLCE (evaluasi): 13 lahan petani irigasi, 2010-2016, 24 kombinasi lokasi-tahun-musim, varietas Inpari 10/13/18/23/28/33,
Ciherang, Dodokan, Silugonggo; hasil 3,6-9,1 Mg/ha; hanya tersedia sebagai sebaran (Fig. 5), tidak per lokasi.

## 2. Boling et al. (2010), *Agricultural Systems* 103:307-315

DOI 10.1016/j.agsy.2010.02.003. Padi tadah hujan lahan petani, Jakenan, Jawa Tengah, 4 desa (Megulung, Jadi, Sidomukti,
Pelemgede) x 4 posisi toposekuen, musim 2000/2001 EWS, 2001 LWS, 2001/2002 EWS, 2002 LWS. Hasil petani 0,32-5,88 Mg/ha;
curah hujan musiman 354-1235 mm; pupuk N 76-166, P 0-45, K 0-51 kg/ha. Cuaca stasiun Jakenan tersedia sebagai rata-rata
musiman (Tabel 3). Hasil per desa-musim ada di gambar (perlu digitasi). Cocok untuk skenario terbatas air, bukan potensial.

Dari teks: potensi hasil simulasi ORYZA2000 4,05-8,19 Mg/ha; hasil terukur 0,32 (Sidomukti, 2001/2002 EWS) sampai 5,88 Mg/ha
(Jadi, 2000/2001 EWS); model dikalibrasi untuk IR64 (Boling et al. 2007). Nilai per desa-musim hanya di Fig. 3-4.

## 3. BPS Provinsi Jawa Barat (diakses lewat Chrome, 25 September 2026)

Subjek "Pertanian, Kehutanan, Perikanan" (subject=557) di jabar.bps.go.id. Dua tabel dibaca langsung dari halaman (tanpa
unduh berkas):

- **Luas Panen, Produktivitas, dan Produksi Padi Menurut Kabupaten/Kota** (metode KSA, 2018-2025), URL
  `https://jabar.bps.go.id/id/statistics-table/3/WmpaNk1YbGFjR0pOUjBKYWFIQlBSU3MwVHpOVWR6MDkjMyMzMjAw/...html?year=YYYY`
  -> `data/lapangan/bps_jabar_padi_kabupaten_2018_2025.csv` (Bandung, Indramayu, Subang, Karawang, Jawa Barat;
  produktivitas ku/ha GKG dan konversi ke kg BK/ha x0,86).
- **Luas Panen Tanaman Padi Kabupaten/Kota menurut Bulan** (2025) -> `bps_jabar_luas_panen_bulanan_2025.csv`.
  Puncak panen April-Mei (Indramayu 38 %, Subang 33 %) dan Oktober-November (31 %, 25 %): dua musim, tanam pindah
  sekitar awal Desember (MT1) dan awal Juni (MT2). Pemilih tahun tabel ini tidak menerima parameter URL; tahun lain
  perlu dipilih manual di halaman.
- Tabel produktivitas 2010-2017 (metode lama) ada di daftar yang sama (nomor 8-13) dan belum diambil; jangan digabung
  dengan deret KSA tanpa catatan perubahan metode 2018.

Produktivitas BPS (ku/ha GKG): Bandung 55,3-64,3; Indramayu 58,1-66,1; Subang 57,1-60,3 (2018-2025).

### 3b. Validasi lintas tahun: potensi hasil WOFOST vs BPS (`validasi_bps_per_musim.csv`, `validasi_bps_ringkasan.json`)

WOFOST 7.2 potensial dengan parameter Inpari 32 gabungan, dua musim per tahun (tanam 1 Des dan 1 Jun), cuaca Open-Meteo,
dibandingkan dengan produktivitas kabupaten. Karena statistik kabupaten adalah hasil aktual petani (semua varietas,
semua tingkat pengelolaan), perbandingan yang sahih adalah **kesenjangan hasil** dan **anomali antar tahun**, bukan 1:1:

| Kabupaten | Rasio BPS / Yp | r anomali antar tahun (n = 8) | CV BPS | CV Yp |
|---|---|---|---|---|
| Indramayu | 0,66 | 0,41 | 4,8 % | 5,9 % |
| Subang | 0,60 | 0,24 | 1,8 % | 4,6 % |
| Bandung | 0,43 | 0,57 | 4,8 % | 2,9 % |

Rasio 0,6-0,66 di dataran rendah sejalan dengan Agustiani et al. (2018): hasil petani sekitar 55-70 % dari Yp. Yp Bandung
12 t/ha tidak realistis (dataran tinggi, suhu rendah memperpanjang durasi di model potensial tanpa cekaman air dan hara);
untuk Bandung pakai model terbatas air atau batasi durasi. Metrik 1:1 langsung (nRMSE 92 %) tidak bermakna dan tidak
boleh dilaporkan sebagai validasi; laporkan rasio kesenjangan hasil dan r anomali seperti Wanthanaporn et al. (2024).
Format tab Batch tersedia di `hasil_observasi_bps_format_batch.csv`; figur `validasi_bps_2018_2025.png`.

## 3e. Makalah pendamping: Agustiani, Sujinah, Hikmah (2018), *Penelitian Pertanian Tanaman Pangan* 2(3):145-153

PDF di `unduh_pdf/Kesesuaian_Ketinggian_Tempat_terhadap_Pe.pdf` (judul cetak: "Kesesuaian Cara Tanam Menurut Elevasi pada
Ekosistem Padi Sawah Irigasi"). Percobaan yang sama dengan EJA 2018: MK 2016, split plot 6 ulangan, Inpari-32 vs Hipa-18,
tiga cara tanam, bibit 21 hari setelah sebar, 2-3 bibit/lubang, plot 5 x 6 m. **Tanggal tanam tetap tidak dilaporkan**
(hanya "MK 2016" dan umur dalam HST); email korespondensi tercantum (wulan_bbpadi@yahoo.co.id) bila ingin meminta
tanggal langsung. Tambahan yang dipakai:

| Lokasi (elevasi) | Desa | Hasil GKG t/ha (2 varietas x 3 cara tanam) | Biomassa menjelang panen g/m2 | LAI primordia / menjelang panen |
|---|---|---|---|---|
| Bandung, 690 m | Bojongemas, Solokan Jeruk | 7,76 | 1188 | 3,7 / 1,5 |
| Subang, 236 m | Gunungtua, Cijambe | 8,78 | 1746 | 5,1 / 2,3 |
| Indramayu, 35 m | Wanasari, Bango Dua | 8,09 | 1470 | 5,2 / 2,0 |

Inpari-32 rata-rata 8,29 vs rata-rata umum 8,21 t/ha (Tabel 6). Hasil per lokasi dikoreksi x 8,29/8,21 lalu x 0,86 (BK)
menggantikan nilai gabungan 7650 kg/ha di file observasi: Subang 7626, Indramayu 7026, Bandung 6740 kg BK/ha (+/- 8 %).
Status hara N rendah, P dan K tinggi di ketiga lokasi (Tabel 2). Nilai LAI Tabel 4 dibaca sebagai cm2/m2 (label "x10^3"
tidak konsisten dengan besaran); rata-rata dua varietas, jadi tidak dicampur dengan LAI Inpari-32 dari EJA Fig. 3.

## 3d. Sujinah et al. (2020), *Penelitian Pertanian Tanaman Pangan* 4(2):63-71 (PDF di `unduh_pdf/01-Sujinah_2.pdf`)

DOI 10.21082/jpptp.v4n2.2020.p63-71. Balai Besar Padi. Dua percobaan:

- **Percobaan I** (MH 2016/2017, Sukamandi 5 m dpl dan Muara Bogor 250 m dpl, 27 genotipe): Inpari-32 **umur berbunga 88
  hari setelah semai** (Tabel 2), tinggi 100 cm, 19 anakan, biomassa 896 g/m2, hasil 5,81 t/ha GKG, indeks panen 0,55
  (Tabel 3). Angka 88 HSS = 67 HST + 21 hari semai **persis sama** dengan Agustiani et al. (2018): konfirmasi independen
  fenologi.
- **Percobaan II** (KP Sukamandi, November 2017-Februari 2018, split plot 3 dosis N x 6 genotipe, 25 x 25 cm, bibit 21 HSS):
  Inpari-32 luas daun/rumpun 232 / 1007 / 3315 / 2487 cm2 dan biomassa 27,8 / 117,7 / 1040 / 1550 g/m2 pada 14 HST, 28 HST,
  berbunga, masak (Tabel 6-7, rata-rata dosis N); biomassa masak 115 N 1554 g/m2 (Tabel 8); hasil 5,41 / 6,92 / 7,61 t/ha
  GKG pada 23 / 115 / 207 N (Tabel 10). Konversi: LAI = luas daun/rumpun x 16 rumpun/m2 / 10^4 -> 0,37 / 1,61 / 5,30 / 3,98;
  TAGP = g/m2 x 10. Tanggal semai tidak eksplisit: **asumsi 1 November 2017** (tanam pindah 22 November); masak
  fisiologis diasumsikan 100 HST (umur panen 115-124 HSS menurut teks). File: `obs_sukamandi_mh2017_inpari32.csv`,
  proyek `sujinah2020_sukamandi_mh2017_inpari32.json` (koordinat KP Sukamandi -6,35; 107,65).

**Uji transfer** (parameter kalibrasi gabungan musim kemarau 2016 dipakai apa adanya pada musim hujan 2017/2018,
`transfer_sujinah2020.json`): antesis simulasi 26 Januari vs observasi 28 Januari; TSUM1 dari DVS musim hujan 1579 vs
1523 (selisih 4 %) -> **fenologi dapat ditransfer antar musim**. Biomassa masak 14,0 vs 15,5 t/ha (bias -10 %). LAI
kurang tersimulasi (LAImax 3,8 vs 5,3) karena SLATB@y yang menyentuh batas bawah pada kalibrasi 2016 (kompensasi
AMAX-SLA); ini bukti bahwa kalibrasi tiga titik per lokasi tidak cukup mengidentifikasi SLA. Hasil simulasi potensial
7,9 vs 5,95 t/ha BK pada 115 N: wajar, percobaan MH terbatas N (7,61 t/ha GKG pada 207 N).

**Kalibrasi gabungan 4 set** (`hasil_kalibrasi_gabungan_4set_inpari32.json`) dicoba dan **ditolak**: AMAXTB@y dan
SLATB@y lari ke batas (0,6 dan 0,8), biomassa 2016 kurang tersimulasi 30-40 %. Sebabnya struktural: percobaan MH
2017/2018 dibatasi N (115 kg N/ha; hasil naik ke 7,61 t/ha pada 207 N), sedangkan percobaan 2016 mendekati potensial,
sehingga keduanya tidak boleh dipaksa ke satu parameter model potensial. Keputusan: parameter Inpari-32 tetap dari
kalibrasi gabungan tiga lokasi 2016; set MH 2017/2018 dipakai sebagai **validasi independen fenologi** (lolos) dan
sebagai batas bawah biomassa. Untuk menggabungkan keduanya secara sahih diperlukan WOFOST 8.1 terbatas N
(Wofost81_NWLP) dengan data tanah dan pupuk, yang tersedia di PCSE tetapi belum diaktifkan di aplikasi.

## 3c. Sumber lain

- Ansari et al. (2023), *Heliyon*: review multimodel, tidak memuat data lapangan.

## 4. Hasil uji pipeline (25 September 2026, Open-Meteo, Wofost72_PP, least-squares 80 evaluasi)

Observasi per lokasi: LAI dan TAGP pada 67 & 112 HST, DVS = 1 (67 HST) dan 2 (112 HST), TWSO gabungan 7650 kg/ha BK
(+/- 1000) pada 112 HST. Parameter: TSUM1, TSUM2, SPAN, AMAXTB@y (batas 900-1800, 400-900, 25-50, 0,6-1,4).

| Lokasi | TSUM1 | TSUM2 | SPAN | AMAXTB@y | DOA sim (obs 7 Jul) | DOM sim (obs 21 Agu) | TWSO sim | nRMSE TAGP |
|---|---|---|---|---|---|---|---|---|
| Subang | 1375 | 900* | 50* | 0,63 | 30 Jun | 17 Agu | 8622 | 21,9 % |
| Indramayu | 1407 | 900* | 50* | 0,60 | 28 Jun | 12 Agu | 7430 | 16,6 % |
| Bandung | 1126 | 897 | 34,9 | 0,74 | 25 Jun | 18 Agu | 8762 | 9,6 % |

\* menyentuh batas. Bacaan: (i) pipeline data sekunder -> cuaca reanalisis -> kalibrasi berjalan; (ii) fenologi
WOFOST dengan prior ORYZA terlalu cepat 5-9 hari dan TSUM2 menyentuh batas atas, konsisten dengan tanggal tanam yang
masih asumsi dan tidak adanya cekaman pindah tanam di WOFOST; (iii) AMAXTB@y turun ke 0,6-0,74, artinya AMAXTB IR72
terlalu tinggi untuk Inpari 32 atau radiasi reanalisis terlalu tinggi; (iv) 6-7 titik per lokasi untuk 4 parameter
adalah underdetermined, sehingga hasil ini hanya layak sebagai uji alur, bukan kalibrasi final. Untuk naskah dibutuhkan
data MLCE per lokasi atau data pengguna, dan tanggal tanam yang benar dari penulis/ICRR.

## 4b. Kalibrasi dua tahap gabungan tiga lokasi (mengatasi underdetermination)

Skrip: tahap 1 fenologi per lokasi (TSUM1, TSUM2 dari DVS = 1 pada 67 HST dan DVS = 2 pada 112 HST), tahap 2 pertumbuhan
gabungan (AMAXTB@y, SPAN, SLATB@y, TDWI; TSUM tetap) dengan 28 residual LAI/TAGP/TWST/TWSO dari tiga lokasi dibobot
1/ketidakpastian, lalu MCMC gabungan (10 walker x 40 langkah) untuk interval kredibel. Hasil di
`data/lapangan/hasil_kalibrasi_gabungan_inpari32.json` dan figur `kalibrasi_gabungan_inpari32.png`.

Versi akhir (setelah hasil gabah per lokasi dari makalah pendamping menggantikan nilai gabungan):

| Parameter | Nilai | Keterangan |
|---|---|---|
| TSUM1 | 1523 (SD antar lokasi 113) | per lokasi 1560 / 1640 / 1370; DOA tepat 7 Juli di ketiga lokasi |
| TSUM2 | 837 (SD 66) | per lokasi 838 / 916 / 756; DOM 20-21 Agustus |
| AMAXTB@y | 1,14 (IK95 1,08-1,18) | sebelumnya 1,41 dengan hasil gabungan; kini lebih masuk akal |
| SPAN | 37,2 (35,4-38,2) | |
| SLATB@y | 0,60 (0,60-0,62) | **masih menyentuh batas bawah**: SLA IR72 terlalu tinggi untuk Inpari-32, perlu SLA terukur |
| TDWI | 79 (64-86) | |

Metrik: nRMSE LAI 9-11 % (Subang, Indramayu), TAGP 15-16 %, TWSO Indramayu 0,1 % dan Subang 4,1 %. Bandung tetap buruk
(nRMSE LAI 27 %, TWSO 27 %) karena model potensial tidak menangkap cekaman air yang dilaporkan;
gunakan Wofost72_WLP_FD untuk lokasi itu. Pasangan AMAXTB@y tinggi dan SLATB@y di batas menandakan kompensasi struktural
(AFGEN IR72 tidak cocok untuk Inpari 32); untuk naskah, kalibrasi SLATB dan AMAXTB harus dibatasi dengan pengukuran SLA
atau data MLCE tambahan. Dengan 28 titik untuk 4 parameter pertumbuhan, masalah underdetermination tahap awal teratasi
secara statistik, tetapi identifiabilitas AMAX-SLA tetap lemah.

## 4c. SLA dari literatur: menyelesaikan SLATB@y yang menempel di batas

Bukti literatur (25 September 2026):

- Tabel SLATB IR72 di PCSE (ha/kg): 0,0045 (DVS 0), 0,0033 (0,16-0,33), 0,0028 (0,65), 0,0021 (0,79), 0,0019 (1,0),
  0,0017 (>= 1,46).
- Zhang, Homma, Zha et al. 2025, *Agric. Systems* (S0308521X25000976), WOFOST padi dengan SLA dinamis: rentang parameter SLA
  0,001-0,0055 ha/kg; pengaturan empiris padi turun linear dari 0,0055 (DVS 0) ke 0,001 (DVS 0,5) lalu stabil 0,001-0,002
  (atau konstan 0,0022 menurut de Wit et al. 2020); SLA terukur turun dari ~0,0015 ke ~0,001 saat memasuki fase
  reproduktif; SLA di sekitar pembungaan (DVS 0,7-1,2) paling berpengaruh pada LAI dan hasil.
- Turunan dari Fig. 3 Agustiani (daun = TAGP - batang - malai 3-10 %): Subang SLA pembungaan 0,0016-0,0020 ha/kg (0,7-0,8 x
  IR72 pada DVS 0,79; ~0,9-1,0 x pada DVS 1,0). Indramayu dan Bandung tidak dipakai karena bobot batang hasil digitasi
  memberi bobot daun yang tidak masuk akal (klasifikasi bentuk panel tengah kurang andal).
- Dingkuhn et al. 2015, *Field Crops Res.* 182:43-58: SLA rendah (daun tebal) berkorelasi dengan RUE tinggi pada padi tropis
  modern di IRRI; mendukung SLA Inpari-32 di bawah IR72 lama pada fase reproduktif.

Aplikasi kini mendukung pengali SLA terpisah fase awal/akhir (`SLATB@ya` untuk DVS < 0,65, `SLATB@yb` untuk DVS >= 0,65,
transisi mulus). Dua uji:

| Varian | SLA | AMAXTB@y | SPAN | TDWI | RGRLAI | SSE (21 obs) |
|---|---|---|---|---|---|---|
| SLA bebas dikalibrasi | @ya 0,60*, @yb 0,40* (SLA pembungaan 0,00076, di bawah literatur) | 1,02 | 41,3 | 153 | default | 63,8 |
| **SLA dipaku literatur** | @ya 1,20 (0,0054 awal), @yb 0,90 (0,0017 pembungaan) | 0,88 (IK95 0,81-0,96) | 35,9 (34,6-37,6) | 98 (88-104) | 0,004* | **45,6** |

\* menyentuh batas. Varian literatur lebih baik (SSE turun 29 %), tidak ada parameter SLA di batas, LAI nRMSE 6,5-13 %
di tiga lokasi 2016, TWSO Subang 2,1 % dan Indramayu 4,1 %. Kesimpulan: SLATB@y = 0,6 pada kalibrasi awal adalah
kompensasi, bukan sifat varietas; dengan SLA literatur, penurunan ada di AMAX (0,88 x IR72), yang lebih masuk akal secara
fisiologis untuk varietas inbrida modern dibanding SLA 40 % IR72. Sisa masalah: RGRLAI di batas bawah 0,004 (fase
eksponensial awal setelah tanam pindah) dan LAI awal Sukamandi MH masih kurang tersimulasi; ini butuh data LAI 14-28 HST
dengan tanggal tanam pasti. Parameter final tersimpan di `hasil_kalibrasi_sla_literatur_inpari32.json`, dipakai di semua
proyek per lokasi; figur `kalibrasi_final_inpari32.png`.

## 4d. Diagnosis sisa masalah LAI (per tanggal, parameter final)

| Set | 7 HST obs / sim | 14 HST | 28 HST | Pembungaan (67 HST) | Masak |
|---|---|---|---|---|---|
| Subang | 0,08 / 0,22 | - | - | 5,04 / 4,85 | 2,15 / 0,61 |
| Indramayu | 0,08 / 0,22 | - | - | 4,50 / 4,67 | 1,90 / 0,45 |
| Bandung | 0,08 / 0,21 | - | - | 4,62 / 5,10 | 2,22 / 2,40 |
| Sukamandi MH | - | 0,37 / 0,38 | 1,61 / 1,01 | 5,30 / 5,18 | 3,98 / 1,67 |

Bacaan: (1) LAI 14 HST dan pembungaan tepat di semua set; (2) selisih terbesar ada pada **fase masak**: WOFOST menghitung
LAI daun hijau, sedangkan luas daun LiCor saat masak mencakup daun menguning (Dingkuhn et al. 2015 memisahkan jaringan
mati; Agustiani/Sujinah tidak menyebutkan) -> observasi LAI fase masak **tidak sebanding** dengan LAI WOFOST dan sebaiknya
dikecualikan atau diberi ketidakpastian besar; (3) 28 HST Sukamandi kurang tersimulasi (1,0 vs 1,6): fase pemulihan
setelah tanam pindah dan anakan awal, tidak ada modul tanam pindah di WOFOST 7.2.

**RGRLAI sangat sensitif dan nilai 0,004 adalah optimum interior, bukan batas.** Uji pada Sukamandi (TDWI 98): LAI 28 HST =
0,41 / 1,01 / 4,74 / 5,52 untuk RGRLAI 0,002 / 0,004 / 0,0085 (baku IR72) / 0,03. Nilai baku IR72 memberi LAI 28 HST tiga
kali observasi (1,61); nilai 0,004 (setengah IR72) adalah kompromi antara 7 HST (obs 0,08, sim 0,22 di tiga lokasi
2016) yang menarik ke bawah dan 28 HST (obs 1,61, sim 1,01) yang menarik ke atas. Bentuk ini (LAI rendah pada 7 HST,
lalu ekspansi cepat) adalah pola pemulihan setelah tanam pindah yang tidak ada di WOFOST 7.2. Posterior RGRLAI sangat
sempit karena parameter masuk secara eksponensial.

**Multi-start** (enam titik awal TDWI 25-150, RGRLAI 0,003-0,02; batas RGRLAI 0,002-0,03, TDWI 15-200): lima dari enam
konvergen ke solusi yang sama, AMAXTB@y 0,91-0,93, SPAN 35,3-35,8, TDWI 104-106, RGRLAI 0,0039, SSE 44,5-44,6; satu
titik awal (TDWI 25, RGRLAI 0,02) terjebak di minimum lokal buruk (SSE 440). Kesimpulan: solusi global kokoh, dan
ketidakcocokan 7 HST vs 28 HST adalah keterbatasan struktur model (tidak ada pemulihan tanam pindah), bukan artefak
optimizer. **Parameter final** = solusi multi-start (`hasil_kalibrasi_multistart_inpari32.json`): TSUM1 1523, TSUM2 837,
SLATB@ya 1,2, SLATB@yb 0,9, AMAXTB@y 0,915, SPAN 35,8, TDWI 105,7, RGRLAI 0,0039; dipakai di semua proyek per lokasi.
Metrik final: TWSO Subang 0,9 %, Indramayu 2,8 %; LAI 5,5-11,5 % (2016); Bandung TWSO +18 % (cekaman air, model potensial).

Cara mengungkapkan di naskah: RGRLAI Inpari-32 setengah nilai IR72 dilaporkan sebagai parameter efektif yang menyerap
efek tanam pindah, dengan uji sensitivitas di atas sebagai bukti; ini praktik yang diterima untuk model tanpa modul tanam
pindah (bandingkan ORYZA yang memodelkannya secara eksplisit).

Varian kalibrasi tanpa LAI fase masak (`hasil_kalibrasi_final_inpari32.json`): AMAXTB@y 0,77 (IK95 0,66-0,85), SPAN 43,8
(37,8-56,7; menjadi kurang teridentifikasi tanpa titik akhir), TDWI 105, SSE 41,0 (20 obs) vs 45,6 (21 obs). Perbaikan
kecil dengan identifiabilitas SPAN yang memburuk, sehingga **varian SLA-literatur dengan semua observasi tetap dipakai
sebagai parameter final**; LAI fase masak dilaporkan di naskah sebagai perbedaan konvensi pengukuran, bukan kegagalan model.

Yang benar-benar butuh data baru: LAI hijau 14-42 HST dengan tanggal tanam pasti (untuk fase pemulihan tanam pindah) dan
pemisahan daun hijau/mati pada pengukuran LAI akhir.

## 4e. Emulasi syok tanam pindah dari literatur ORYZA (menutup sebagian sisa masalah)

Mekanisme ORYZA2000 (Bouman & van Laar 2006, *Agric. Systems* 87:249-273; Tan et al. 2016, *Environ. Modell. Softw.*
83:36-46): saat tanam pindah LAI dan biomassa turun karena pengenceran kerapatan, lalu pertumbuhan baru berlanjut setelah
"syok tanam pindah" yang lamanya diturunkan dari jumlah suhu di persemaian (TSTR). Parameter ORYZA: SHCKL (penundaan
pertumbuhan daun = SHCKL x TSTR) dan SHCKD (penundaan perkembangan = SHCKD x TSTR); nilai baku ORYZA2000 0,25 dan 0,40
(Bouman et al. 2001, buku ORYZA2000). Bouman & van Laar (2006) menegaskan: "saat tanam pindah LAI dan seluruh biomassa
di-reset menurut rasio kerapatan tanam terhadap kerapatan persemaian; pertumbuhan berlanjut setelah syok tanam pindah
berlalu", dengan hubungan linear lama syok vs derajat-hari persemaian dari Kropff et al. (1994a). Amiri Larijani et al.
2011 (*Rice Science* 18:321-334) melaporkan umur bibit mengubah durasi tanaman 7-10 hari, sebanding dengan SHCKD x TSTR.
Di WOFOST reset biomassa menurut kerapatan diserap oleh TDWI (bobot kering awal per hektar setelah tanam pindah).

Implementasi di WOFOST Studio (opsi "Emulasi syok tanam pindah" di tab Pengaturan; `SimulationRunner.transplant_shock_info`):
TSTR dihitung dari cuaca persemaian (umur bibit, suhu efektif Tbase 8 / Topt 30); selama SHCKL x TSTR setelah tanam LAI
ditahan pada nilai awal lewat `set_variable("LAI")` (PCSE tidak menyediakan setter DVS, sehingga penundaan perkembangan
SHCKD x TSTR diemulasikan dengan menambah TSUM1 efektif). Untuk bibit 21 hari di Jawa Barat: TSTR ~ 400 C.d, penundaan
daun ~5 hari, penundaan perkembangan ~8 hari.

Kalibrasi ulang dengan syok aktif (`hasil_kalibrasi_syok_inpari32.json`, 3 titik awal konvergen):

| Parameter | Tanpa syok | Dengan syok | Keterangan |
|---|---|---|---|
| TSUM1 intrinsik | 1523 | 1365 | lebih dekat ke turunan ORYZA (1236) karena 8 hari syok kini eksplisit |
| TSUM2 | 837 | 796 | |
| AMAXTB@y | 0,915 | 0,90 | |
| SPAN | 35,8 | 36,6 | |
| TDWI | 106 | 144 | |
| RGRLAI | 0,0039 | 0,0035 | tetap ~0,4 x IR72 |
| SSE (21 obs) | 44,5 | **39,8** | perbaikan 11 % |

LAI 7 HST turun dari 0,22 ke ~0,15 (obs 0,08); LAI tiga lokasi 2016 nRMSE 6-9 %; TWSO Subang 2,0 %, Indramayu 2,7 %.
LAI 28 HST Sukamandi masih kurang (~1,0 vs 1,6): fase pemulihan cepat setelah syok tidak sepenuhnya tertangkap, dan RGRLAI
tetap rendah. Kesimpulan: literatur ORYZA menutup sebagian masalah (fenologi menjadi konsisten dengan ORYZA, 7 HST
membaik, SSE turun), tetapi bentuk pemulihan 14-28 HST tetap memerlukan data LAI hijau awal. Parameter final proyek kini
memakai syok aktif dengan SHCKL 0,25 dan SHCKD 0,40; keduanya bisa diubah dan layak dikalibrasi bila data 14-42 HST tersedia.

## 4f. Pencarian literatur untuk LAI hijau awal (14-42 HST) Inpari-32: hasil dan kesimpulan (25 September 2026)

Pencarian (Google Scholar, repositori UB/IPB/Unhas, JPPTP, ScienceDirect) untuk padi Indonesia dengan LAI diukur pada
14-42 HST dan tanggal tanam eksplisit. Yang ditemukan dan diunduh (`scratchpad/lit/`, PDF repositori terbuka):

| Sumber | Varietas, lokasi, musim | LAI yang tersedia | Tanggal tanam | Kegunaan |
|---|---|---|---|---|
| Aulya 2024 (skripsi UB) | Inpari 32, Jatimulyo Malang 450-506 m dpl, Okt 2023-Feb 2024, 25 x 20 cm, bibit 20 hari | 30 / 70 / 110 HST: konvensional 2,37 / 7,77 / 0,51 | hanya bulan | LAI 30 HST tunggal; dataran tinggi, irigasi tetes vs konvensional |
| Rahmah 2024 (skripsi UB) | Inpari 32, lokasi sama, mulai 27 Okt 2023, 30 x 20 cm | 30 / 70 / 110 HST: 0,85-1,12 / 3,4-4,0 / 1,3-1,5 (mulsa) | tanggal mulai percobaan | tidak konsisten dengan Aulya di lokasi-musim sama (LAI 70 HST 4 vs 8) |
| Abdullah 2024 (skripsi UB) | Inpari-32, koordinat 7,9445 S 112,6195 E, 450 m | LAI mulsa vs konvensional (tabel belum diekstrak) | bulan | sama seperti di atas |
| Ermanto 2020 (tesis UB) | Inpari 30, Jatimulyo 460 m, tanam Sept dan Okt 2019 | 30 / 60 / 90 HST: 0,54-1,21 / 2,3-4,7 / 2,0-4,1 per pola tanam | bulan | varietas berbeda; cuaca BMKG Karangploso |
| Hikmah & Pratiwi 2019 (JPPTP 3(2):75-81) | Inpari 31, KP Sukamandi, MK 2015 & MH 2015/16, bibit 20 vs 30 HSS | tidak ada LAI (tinggi & anakan 15/30/45 HST) | musim | efek umur bibit pada hasil (bibit 20 HSS lebih tinggi) |
| Anggraini et al. 2013; Susanti et al. 2013 (J. Produksi Tanaman) | Inpari 13, Malang | LAI 50-60 HST | - | di luar jendela |
| Bundel Academia Agustiani (unduh_pdf/more_papers_by_nurwulan_agustiani, 14 PDF dipindai) | Sujinah 2020 rendaman stagnan (10 genotipe, MH 2017/18 Sukamandi), Agustiani 2021 IJAS, drip irrigation 2019 (Hipa 8/18, Inpago 11, Inpari 42), RAISA Banyuasin 2019 | tidak ada LAI Inpari-32 (hit "LAI" = kata "nilai") | - | tidak berguna untuk LAI awal |

Kesimpulan: **tidak ada sumber terbuka yang memuat deret LAI hijau 14-42 HST Inpari-32 dataran rendah Jawa Barat dengan
tanggal tanam pasti.** Data skripsi UB memberi satu titik 30 HST di dataran tinggi Malang dengan variasi antar-skripsi
yang besar (0,85-2,37) dan hanya bulan tanam, sehingga tidak layak untuk mengalibrasi SHCKL/SHCKD/RGRLAI. Uji tambahan:
menghapus LAI 7 HST (marker Fig. 3 tumpang tindih di nol) dari kalibrasi **tidak** mengubah RGRLAI (tetap 0,0035; SSE 38,6
untuk 18 obs), sehingga bentuk pemulihan awal benar-benar ditentukan oleh kompromi dengan LAI/TAGP pembungaan, bukan
oleh titik 7 HST. Status akhir: sisa ini memerlukan pengukuran lapangan (LAI hijau mingguan 14-42 HST, tanggal tanam
pasti, idealnya di KP Sukamandi/Subang), dan ini dilaporkan di naskah sebagai keterbatasan yang jujur.

## 6. Respons N Inpari-32 dengan WOFOST 8.1 terbatas N (25 September 2026)

Model `Wofost81_NWLP_CWB_CNB` (PCSE 6.0.13: neraca air klasik + neraca N klasik, AMAX bergantung N daun spesifik)
kini tersedia di WOFOST Studio, sehingga Percobaan II Sujinah et al. (2020) - satu-satunya data Inpari-32 dengan
perlakuan N - bisa dipakai secara sah (sebelumnya hanya untuk fenologi karena model 7.2 tidak punya N).

Sumber parameter: `data/crop_params/rice.yaml` = salinan cabang `wofost81` repositori WOFOST_crop_parameters
(parameter N padi IRRI: NMAXLV_TB 0,06->0,015 kg N/kg, NRESIDLV 0,0043, TCNT 10 d, RNUPTAKEMAX 7,2 kg/ha/d,
RGRLAI_MIN 0,004). Dua parameter asimilasi 8.1 yang belum ada di berkas upstream (AMAX_REF, KN) diisi otomatis
(maks AMAXTB = 40 kg CO2/ha/jam; KN 0,4) dan dapat di-override.

Rancangan: parameter pertumbuhan potensial (TSUM1/2, SLATB@ya/@yb, AMAXTB@y, SPAN, TDWI, RGRLAI, syok tanam pindah)
DIPERTAHANKAN dari kalibrasi MK 2016; hanya parameter N yang dikalibrasi terhadap 6 observasi Inpari-32 per dosis
(Tabel 8 biomasa masak; Tabel 10 hasil GKG x 0,86; bobot 1/(CV x obs), CV 16,8 % dan 8,75 %). N dibagi 3 (7, 28,
42 HST = inisiasi malai), NAVAILI 0, NSOILBASE_FR 0,02.

| Parameter N | Nilai | Batas | Rujukan kewajaran |
|---|---|---|---|
| NSOILBASE (pasokan N tanah asli/musim) | 83,5 kg N/ha | 10-150 | INS sawah irigasi Asia 40-100 kg N/ha (Dobermann et al. 2003) |
| N_recovery (efisiensi pemulihan urea) | 0,46 | 0,2-0,8 | RE urea sawah 0,3-0,5 (Cassman et al. 2002) |
| NMAXSO (N maks gabah) | 0,0144 (dipaku) | - | ekotipe rice_eu upstream; N gabah 1,0-1,4 % |

Hasil (SSE tertimbang 2,20 untuk 6 obs; `hasil_kalibrasi_n_inpari32.json`, figur `respons_n_inpari32.png`):

| Dosis N | Hasil obs (kg BK/ha) | Hasil sim | Biomasa obs | Biomasa sim | Serapan N sim |
|---|---|---|---|---|---|
| 23 | 4653 | 4545 | 10065 | 11967 | 94 |
| 115 | 5951 | 5946 | 15539 | 13541 | 137 |
| 207 | 6545 | 6718 | 15468 | 14353 | 179 |

Tanpa kalibrasi N (NSOILBASE 30, NAVAILI 20, recovery 0,5, NMAXSO varietas 0,027) hasil sim 2765/3885/4979 -> jauh
terlalu rendah; jadi pasokan N tanah asli Sukamandi adalah kunci. Varian dengan NMAXSO bebas mencapai batas bawah
0,010 (SSE 2,08) dan ditolak (`hasil_kalibrasi_n_nmaxso_bebas_inpari32.json`).

Keterbatasan versi pertama (diperbarui di bagian 6b): (1) LAI simulasi hampir tidak merespons N (LAImax 5,3-5,4 pada semua dosis) padahal luas
daun rata-rata 6 genotipe naik 3,7 -> 6,5 saat berbunga; respons hasil di WOFOST 8.1 datang lewat AMAX(SLN), bukan
lewat tajuk -> ini titik kritik yang layak dibahas di naskah (dan alasan RGRLAI_MIN/NSLLV_TB pantas masuk analisis
sensitivitas). (2) Biomasa pada dosis tinggi kurang 8-13 %, sedangkan hasil pas: indeks panen simulasi terlalu tinggi
pada N tinggi. (3) 6 observasi untuk 2 parameter bebas: cukup untuk identifikasi, tidak untuk validasi independen;
validasi silang harus memakai musim lain (mis. data BPS atau musim MK).

Proyek siap pakai: `data/projects/sujinah2020_sukamandi_mh2017_inpari32_N{23,115,207}.json` (tab Pengaturan >
grup "Pemupukan N terjadwal" aktif untuk model 8.1) dan observasi `data/lapangan/obs_sukamandi_mh2017_inpari32_N*.csv`.

## 6b. Perbaikan tiga keterbatasan respons N (25 September 2026)

Skrip: `scratchpad/calib_n4.py`; hasil: `data/lapangan/hasil_kalibrasi_n2_inpari32.json` (menggantikan
`hasil_kalibrasi_n_inpari32.json` bagian 6); figur `respons_n_inpari32.png` (3 panel).

**Perbaikan kode.**
1. Bug konsistensi parameter: PCSE menghitung faktor pertumbuhan daun juvenil 1 - (1-idx)(RGRLAI - RGRLAI_MIN)/RGRLAI.
   RGRLAI Inpari-32 (0,0035) lebih kecil dari RGRLAI_MIN upstream (0,004), sehingga cekaman N justru MEMPERCEPAT
   pertumbuhan daun. Diperbaiki dengan parameter virtual `RGRLAI_MIN_FR` (RGRLAI_MIN = FR x RGRLAI; default 0,5 = rasio
   IR72 upstream 0,004/0,008). Efek numeriknya kecil karena jalur ini hanya aktif saat DVS < 0,2 dan LAI < 0,75.
2. Model ekstensi `Wofost81_NWLP_CWB_CNB_NLV` (`wofost_app/core/wofost81_nleaf.py`): menambah dua jalur LINTUL3
   (Shibu et al. 2010) ke WOFOST 8.1, SLA x exp(-NSLA(1-NNI)) dan FL x exp(-NPART(1-NNI)); NNI definisi WOFOST 8.0.
   Uji: NSLA = NPART = 0 identik dengan WOFOST 8.1 (selisih LAI harian 0,0). Catatan teknis: NNI untuk partisi harus
   dihitung di tahap laju karena PCSE mengosongkan state dari kiosk saat integrasi.

**Data tambahan.** Selain hasil dan biomasa masak Inpari-32 per dosis (6 obs), dipakai 8 observasi bentuk respons:
rasio 23/115 dan 207/115 luas daun & biomasa pada 28 HST dan berbunga dari efek utama dosis (Tabel 6 & 7, rata-rata
6 genotipe). Karena interaksi dosis x varietas nyata, sigma rasio = sqrt(2) x CV petak (konservatif). NSOILBASE_FR
dipaku 0,01/hari (pelepasan merata sepanjang musim) karena berkorelasi -0,99 dengan NSOILBASE.

| | WOFOST 8.1 standar | 8.1 + SLA(N) (ekstensi) |
|---|---|---|
| Parameter | NSOILBASE 93,5; recovery 0,45 | NSOILBASE 100 (batas); recovery 0,43; NSLA 2,17; NPART 0 |
| SSE (14 obs) / AICc | 13,40 / 4,47 | 11,22 / 5,30 (k = 3) |
| LAI berbunga 23/115 (obs 0,64) | 0,96 | 0,72 |
| LAI 28 HST 23/115 (obs 0,75) | 1,00 | 1,00 |
| RMSE LODO hasil | 235 kg/ha (4,1 %) | 373 kg/ha (6,5 %) |
| RMSE LODO biomasa | 1851 kg/ha (13,5 %) | 1644 kg/ha (12,0 %) |

**Status tiap keterbatasan.**
1. *LAI tidak merespons N*: sebagian teratasi. Dengan ekstensi SLA(N), respons LAI saat berbunga pulih (0,72 vs obs
   0,64; standar 0,96). Respons pada 28 HST tetap nol di kedua versi karena luas daun awal dibatasi kurva eksponensial
   suhu (GLAIEX, RGRLAI 0,0035), bukan oleh N; ini terkait langsung dengan masalah LAI awal (bagian 4f) yang hanya bisa
   diselesaikan dengan data lapangan. AICc tidak memihak ekstensi (selisih 0,8 < 2), jadi WOFOST 8.1 standar tetap
   model utama dan ekstensi dilaporkan sebagai uji struktur model. NPART ditolak data (menuju 0: menurunkan hasil).
2. *Biomasa N tinggi kurang 8-13 %*: bukan kesalahan yang perlu dipaksa hilang. Indeks panen (HI) Inpari-32 di set
   lain: Agustiani 2016 0,45/0,50/0,45; Sujinah P-II 23 N 0,46; Sujinah P-I (MH 2016/17) 0,55. Hanya Sujinah P-II
   115 N (0,38) dan 207 N (0,42) yang rendah. Model (HI 0,44-0,47) konsisten dengan mayoritas data; sisa biomasa
   < 1 sigma pengukuran (CV 16,8 %). Memaksa HI 0,38 akan merusak kecocokan 5 set lain.
3. *6 obs untuk 2 parameter*: kini 14 obs + validasi silang leave-one-dose-out (hasil diprediksi dalam 4,1 % untuk
   dosis yang tidak dipakai kalibrasi). Uji transfer ke 3 lokasi Agustiani 2016 (126 kg N/ha, 7/24/42 HST) GAGAL untuk
   Subang (-18 %) dan Indramayu (-21 %). Diagnosis: dengan N jenuh WOFOST 8.1 memberi Subang 7980 dan Indramayu 6880
   (obs 7624 dan 7025), jadi selisihnya murni pasokan N tanah asli (INS) Sukamandi yang tidak berlaku di lahan petani
   lain. Bandung cocok (+4 %) hanya kebetulan: pada N jenuh Bandung 9665 vs obs 6739 (cekaman air pengisian tidak
   tertangkap). Kesimpulan untuk naskah: parameter N tanaman dapat dipindah, INS harus diukur per lokasi (petak omisi
   0-N; Dobermann et al. 2003). Validasi independen modul N memerlukan data petak omisi di lokasi uji.

## 6c. Validasi independen modul N dengan petak omisi LTFE KP Sukamandi (25 September 2026)

Sumber (terbuka, stasiun sama dengan Sujinah 2020, musim/tahun/varietas berbeda; data di
`data/lapangan/ltfe_sukamandi_omisi_n.csv`, hasil `validasi_ltfe_sukamandi.json`, figur `validasi_ltfe_sukamandi.png`):
- Susanti et al. 2023, IOP Conf. Ser. EES 1165:012026 (CC BY 3.0): Long-Term Fertility Experiment BB Padi (sejak 1994),
  MK 2022, Inpari-33, bibit 21 HSS, 25 x 25 cm, tergenang 2-3 cm. +PK (tanpa N) vs +NPK 140 kg N/ha: hasil 4,01 vs
  6,87 t/ha (KA 14 %); luas daun & bobot kering per rumpun 21/35/60 HST.
- Hikmah et al. 2021, J. Agron. Indonesia 49(3):242-250: LTFE yang sama, Jul-Des 2020, Inpari-33, bibit 18 HSS,
  urea 7 HST/30 HST/primordia. Tanpa N vs NPK 140 kg N/ha: 3,80 vs 4,70 t/ha GKG; luas daun 21/35 HST & berbunga.
Sumber on-farm RTDP domain Sukamandi (Dobermann et al. 2003 Agron. J. 95:913 & 924; buku IRRI 2004) tidak bisa
diakses (paywall, verifikasi anti-bot, server IRRI hanya memberi unduhan berkas).

Asumsi: tanggal tanam tidak dilaporkan (1 Mei 2022, 2 Agustus 2020; sensitivitas +/-21 hari); fenologi Inpari-33
(107 HSS, deskripsi varietas) lewat skala TSUM1/TSUM2; parameter tanaman & N dari kalibrasi Inpari-32 TANPA perubahan.
Penting: tanpa irigasi, neraca air klasik (tanah drainase bebas) membuat padi Agustus-November tercekam air
(RFTRA 0,38), padahal petak digenangi -> semua simulasi validasi memakai irigasi 2 cm tiap 2 hari (tombol baru
"Isi genangan sawah" di tab Pengaturan).

| | MK 2022 | Jul-Des 2020 |
|---|---|---|
| Hasil tanpa N obs / simulasi buta | 3449 / 3500 kg/ha (+1,5 %) | 3268 / 3250 kg/ha (-0,6 %) |
| NSOILBASE dari petak omisi (vs kalibrasi 93,5) | 91,7 | 94,1 |
| Hasil 140 N obs / sim | 5908 / 5250 (-11 %) | 4042 / 5240 (+30 %) |
| Rasio hasil tanpa N/140 N obs / sim | 0,58 / 0,66 | 0,81 / 0,62 |
| Rasio LAI 21-35-60/berbunga obs | 0,95 - 0,66 - 0,45 | 0,70 - 0,54 - 0,34 |
| ... 8.1 standar | 1,00 - 1,00 - 0,93 | 1,00 - 0,99 - 0,88 |
| ... 8.1 + SLA(N) | 1,00 - 0,96 - 0,66 | 1,00 - 0,87 - 0,54 |

Kesimpulan:
1. **Pasokan N tanah asli tervalidasi secara independen.** Parameter hasil kalibrasi Sujinah memprediksi hasil petak
   tanpa N di dua musim lain dalam +/-2 %, dan NSOILBASE yang diestimasi dari petak omisi (91,7 dan 94,1) hampir sama
   dengan hasil kalibrasi (93,5). Tidak sensitif terhadap tanggal tanam (NSOILBASE 88-98 untuk +/-21 hari).
2. **Hasil pada N penuh**: MK 2022 -11 % (Inpari-33 berpotensi hasil 9,8 vs 8,4 t/ha Inpari-32; serangan penggerek
   batang). Tahun 2020 +30 % tetapi petak NPK 2020 anomali: hasilnya lebih rendah dari petak tanpa P (5,27 t/ha) dan
   penulis melaporkan tanah terdegradasi; jadi bukan uji yang adil untuk model.
3. **Respons luas daun terhadap N** gagal di WOFOST 8.1 standar pada kedua data independen, dan ekstensi SLA(N)
   (NSLA dari kalibrasi Sujinah, tanpa diubah) memperbaikinya secara konsisten: RMSE rasio LAI 0,39 -> 0,25. Bukti
   independen ini mendukung ekstensi untuk variabel tajuk, padahal AICc pada data kalibrasi saja belum memihak.
   Respons pada 21-35 HST tetap tidak tertangkap (fase eksponensial dibatasi suhu), konsisten dengan bagian 6b.
4. **Transfer ke lahan petani Agustiani 2016** (sekarang juga dengan penggenangan): Subang -18 %, Indramayu -18 % dengan
   INS Sukamandi; +5 % dan +4 % dengan N jenuh. Jadi INS Sukamandi valid di stasiun Sukamandi lintas musim/tahun,
   tetapi tidak dapat dipindah ke lahan petani lain. Bandung +4 % tetap kebetulan (N jenuh +43 %).

Implikasi naskah: validasi modul N kini bertumpu pada data independen (2 musim, 4 perlakuan, 12+ observasi) dengan
galat hasil tanpa N < 2 %, dan keterbatasan yang tersisa terlokalisasi (INS spesifik lokasi; respons LAI awal).

## 6d. Menjawab lima keberatan reviewer (25 September 2026)

Parameter final (menggantikan angka di 6b/6c; `hasil_kalibrasi_n4_inpari32.json`, proyek `..._N{23,115,207}.json` dan
`..._nlv.json`). Dua perbaikan kode lebih dulu: (i) **AMAX_REF kini mengikuti AMAXTB@y** (WOFOST 8.1 tidak memakai
AMAXTB, sehingga pengali 0,90 hasil kalibrasi potensial sebelumnya hilang diam-diam; kini AMAX_REF = 36,1); dengan ini
8.1 pada N jenuh memprediksi Subang/Indramayu -0,7/-1,5 % (sebelumnya +4,7/+4,1 %). (ii) **Ekstensi NLAI**: WOFOST 8.1
hanya menerapkan cekaman N pada ekspansi daun saat DVS < 0,2 dan LAI < 0,75, padahal NNI padi 23 kg N/ha sudah turun
sejak 21 HST (0,99 -> 0,75 pada 35 HST). Faktor LINTUL3 exp(-NLAI(1-NNI)) diterapkan sepanjang fase eksponensial.
NSLA dan NLAI tidak dapat diidentifikasi bersama (SE > nilai), maka dipakai satu koefisien NLEAF = NSLA = NLAI.

| | 8.1 standar | 8.1 + N-daun (NLEAF) |
|---|---|---|
| Parameter (kalibrasi Sujinah, 14 obs) | NSOILBASE 90,8; recovery 0,52 | NSOILBASE 97,0; recovery 0,45; NLEAF 1,50 |
| AICc | 4,66 | 4,49 |
| Validasi silang (LODO) hasil | 3,0 % | 4,8 % |
| LTFE: galat hasil tanpa N (2022 / 2020), buta | -0,3 % / -2,0 % | -1,4 % / -6,7 % |
| LTFE: RMSE rasio LAI tanpa N/140 N (6 titik) | 0,40 | 0,15 |
| LTFE 2022 rasio LAI 21-35-60 HST (obs 0,95-0,66-0,45) | 1,00-1,00-0,94 | 0,94-0,78-0,62 |

**Poin 1, tanpa data lapangan sendiri: dimitigasi, tidak terhapus.** Dampak setiap asumsi kini terkuantifikasi:
tanggal tanam (+/-21 hari, 4b dan 6c), digitasi (bobot ketidakpastian), varietas (poin 2), cuaca (poin 3). Kesimpulan
utama bertahan pada semua uji. Protokol minimum satu musim yang akan menutup poin ini:
- lokasi KP Sukamandi atau lahan petani Subang; Inpari-32; tanggal semai dan tanam dicatat;
- 3 perlakuan N (0, 60, 120 kg N/ha) termasuk petak omisi 0-N, 3-4 ulangan;
- LAI hijau (LAI-2200 atau destruktif) dan bobot kering organ tiap 7 hari 7-56 HST, lalu saat berbunga dan masak;
- tanggal berbunga 50 % dan masak; hasil ubinan (KA 14 %); serapan N tanaman saat masak (Kjeldahl);
- cuaca stasiun harian (Tmin, Tmax, radiasi atau lama penyinaran, hujan) di lokasi.

**Poin 2, varietas validasi berbeda: teratasi sebagai uji kepekaan** (`sensitivitas_asumsi_varietas.json`).
Delapan varian (fenologi Inpari-32 tanpa skala, fenologi +/-10 %, AMAX +/-10 %, SLA +/-10 %): galat hasil tanpa N
tetap -10 sampai +8 %, dan ekstensi selalu lebih baik untuk rasio LAI (RMSE 0,07-0,20 vs 0,34-0,45). Kesimpulan tidak
bergantung pada asumsi varietas. Hasil ini wajar karena hasil petak omisi terutama ditentukan pasokan N tanah.

**Poin 3, cuaca reanalisis: teratasi sebagian** (`sensitivitas_sumber_cuaca.json`). Open-Meteo vs NASA POWER:
kalibrasi Sujinah bergeser +1 sampai +5 %; Subang/Indramayu 0 sampai -3 %; LTFE 2022 hasil tanpa N +4,4 % (vs +1,6 %).
Peka: LTFE Agustus-Oktober 2020 (Tmax Open-Meteo 34,1 vs NASA POWER 29,7 C; galat +16,8 % dengan POWER) dan Bandung
(dataran tinggi, grid POWER 0,5 derajat). Literatur evaluasi ERA5-Land di stasiun Jawa melaporkan bias -1 sampai -2,4 C;
tidak ada evaluasi NASA POWER di Jawa Barat yang ditemukan. Data stasiun BMKG memerlukan akun, jadi tidak diakses.
Sikap untuk naskah: laporkan kedua sumber sebagai ansambel dan nyatakan kepekaan 2020/Bandung secara terbuka.

**Poin 4, ketidakpastian parameter: teratasi** (`posterior_n_inpari32.json`, `sobol_model_final_n.json`).
MCMC (emcee, 16 walker x 120 langkah, burn 40, tau 4-8, penerimaan 0,6-0,7):

| | NSOILBASE | recovery | NLEAF |
|---|---|---|---|
| 8.1 standar | 85 [60-99] | 0,57 [0,32-0,79] | - |
| ekstensi | 89 [70-99] | 0,60 [0,32-0,79] | 1,32 [0,12-2,87] |

Interval 95 % prediksi LTFE (32 sampel posterior): hasil tanpa N kedua musim tercakup untuk model standar. Dengan
ekstensi, MK 2022 seluruh rasio LAI, rasio biomasa 60 HST dan rasio hasil tercakup; 2020 rasio LAI 35 HST & berbunga
tercakup, hasil tanpa N sedikit di luar (2,69 [2,13-3,25] vs 3,27 t/ha). Model standar tidak mencakup satu pun rasio
LAI. Recovery pupuk berkorelasi dengan NSOILBASE dan hanya dibatasi lemah oleh 14 obs.
Sobol (N = 128, 11 parameter, CI bootstrap): pada 23 N hasil dikendalikan SPAN (ST 0,62) dan NMAXSO (0,25), LAI
maksimum oleh NLAI (0,37), TSUM1 (0,34), NSLA (0,28). Pada 207 N NLAI/NSLA berpengaruh nol (ekstensi hanya aktif saat
kekurangan N), dan AMAXTB@y kini berpengaruh (0,06), membuktikan perbaikan (i). NMAXSO dipaku dari literatur
(0,0144) padahal berpengaruh besar pada N rendah: laporkan sebagai ketidakpastian struktural.

**Poin 5, LAI awal dan transfer pasokan N tanah: sebagian teratasi.**
- LAI awal: dengan NLAI, respons 21-35 HST pada data independen LTFE kini muncul (2022: 0,94/0,78 vs obs 0,95/0,66).
  Pada data kalibrasi Sujinah (23 N) rasio 28 HST masih 0,98 vs 0,75 karena NNI model baru turun setelah 21 HST;
  neraca N klasik melepas N tanah dengan laju konstan (NSOILBASE_FR). Model SNOMIN di PCSE (mineralisasi mekanistik)
  adalah jalan lanjutan, tetapi memerlukan data C/N tanah yang tidak tersedia.
- Pasokan N tanah: stabil lintas waktu di Sukamandi (kalibrasi 2017/18 = 90,8; omisi 2020 = 92,9; omisi 2022 = 91,0),
  jadi transfer temporal tervalidasi. Transfer spasial ke lahan petani tidak dapat diprediksi dari uji tanah: ketiga
  lokasi Agustiani dan Sukamandi sama-sama berstatus "N rendah" (makalah pendamping Tabel 2), konsisten dengan
  Dobermann et al. 2003 bahwa uji tanah memprediksi INS dengan buruk. Rekomendasi naskah: INS diukur per lokasi
  dengan petak omisi.

## 5. Cara memakai di WOFOST Studio

1. Menu Proyek > Buka `data/projects/agustiani2018_subang_inpari32.json` (Open-Meteo dimuat otomatis saat menekan Jalankan).
2. Tab Kalibrasi: buka `data/lapangan/obs_subang_2016_inpari32.csv`; pilih LAI, TAGP, DVS; parameter TSUM1, TSUM2, SPAN,
   AMAXTB@y; jalankan MCMC untuk posterior.
3. Ulangi untuk Indramayu dan Bandung; Bandung sebaiknya memakai model terbatas air (Wofost72_WLP_FD).
4. Untuk validasi hasil lintas tahun gunakan data BPS di tab Batch.
