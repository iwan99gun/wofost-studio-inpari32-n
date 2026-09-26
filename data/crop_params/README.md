# Parameter tanaman WOFOST 8.1 (salinan lokal)

`rice.yaml` disalin dari cabang `wofost81` repositori resmi
https://github.com/ajwdewit/WOFOST_crop_parameters (komit terakhir 17 Agustus 2026, Version 1.0.0).
Berisi parameter nitrogen padi (NMAXLV_TB, NMAXSO, NRESID*, TCNT, RNUPTAKEMAX, NSLLV_TB, RGRLAI_MIN, dll.)
yang tidak ada pada salinan PCSE 6.0.13 untuk WOFOST 7.2/7.3.

Catatan: modul asimilasi WOFOST 8.1 di PCSE 6.0.13 (`pcse.crop.assimilation.WOFOST_Assimilation2`) juga
memerlukan `AMAX_REF` (AMAX maksimum pada SLN tinggi, kg CO2/ha/jam) dan `KN` (koefisien pemadaman N
tajuk) yang BELUM ada di berkas upstream. WOFOST Studio mengisi keduanya otomatis: AMAX_REF = nilai
maksimum AMAXTB varietas, KN = 0,4 (nilai umum tajuk padi/serealia); keduanya tampil di tabel parameter dan
bisa di-override.
