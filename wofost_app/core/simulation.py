"""Menjalankan model PCSE-WOFOST dari SimulationConfig."""
from __future__ import annotations

import datetime as dt
import time
from dataclasses import dataclass, field
from typing import Callable

import pandas as pd
from pathlib import Path

from .config import SimulationConfig

MODELS = {
    "Wofost72_PP": "WOFOST 7.2 - Potensial (tanpa batas air)",
    "Wofost72_WLP_FD": "WOFOST 7.2 - Terbatas air (drainase bebas)",
    "Wofost73_PP": "WOFOST 7.3 - Potensial (respon CO2)",
    "Wofost73_WLP_CWB": "WOFOST 7.3 - Terbatas air (neraca air klasik)",
    "Wofost81_NWLP_CWB_CNB": "WOFOST 8.1 - Terbatas N dan air (neraca air & N klasik)",
    "Wofost81_NWLP_CWB_CNB_NLV": "WOFOST 8.1 + efek N pada SLA & partisi daun (tipe LINTUL3; ekstensi)",
}
EXTENSION_MODELS = {"Wofost81_NWLP_CWB_CNB_NLV"}
# Folder parameter tanaman lokal untuk WOFOST 8.1 (salinan cabang wofost81; lihat data/crop_params/README.md)
CROP_PARAM_DIR_81 = Path(__file__).resolve().parents[2] / "data" / "crop_params"
# Parameter asimilasi WOFOST 8.1 (PCSE 6.0.13) yang belum ada di berkas parameter upstream -> diisi otomatis
N_ASSIM_EXTRA = {"AMAX_REF": "AMAX maksimum pada N daun spesifik tinggi [kg CO2/ha/jam] (WOFOST 8.1; default = maks AMAXTB)",
                 "KN": "Koefisien pemadaman N dalam tajuk [-] (WOFOST 8.1; default 0,4)",
                 "NSLA": "Koefisien efek cekaman N pada SLA: SLA x exp(-NSLA(1-NNI)) [-] (ekstensi LINTUL3; default 1,0)",
                 "NPART": "Koefisien efek cekaman N pada fraksi daun: FL x exp(-NPART(1-NNI)) [-] (ekstensi LINTUL3; default 1,0)",
                 "NLAI": "Koefisien efek cekaman N pada ekspansi daun fase eksponensial: GLAIEX x exp(-NLAI(1-NNI)) [-] (ekstensi; default 1,0)"}


# Parameter skalar virtual (tidak ada di PCSE; diterjemahkan oleh SimulationRunner.build_params)
#   RGRLAI_MIN_FR: RGRLAI_MIN = RGRLAI_MIN_FR x RGRLAI. PCSE menghitung faktor reduksi pertumbuhan daun akibat N sebagai
#   1 - (1-idx)(RGRLAI - RGRLAI_MIN)/RGRLAI; bila RGRLAI dikalibrasi di bawah RGRLAI_MIN upstream (0,004), cekaman N
#   justru MEMPERCEPAT pertumbuhan daun. Rasio menjaga konsistensi (IR72 upstream: 0,004/0,008 = 0,5).
VIRTUAL_SCALARS = {"RGRLAI_MIN_FR": "RGRLAI_MIN sebagai fraksi RGRLAI [-] (WOFOST 8.1; upstream IR72 = 0,5)",
                  "PART_DELAY": "Penundaan alokasi asimilat penuh ke organ simpan pasca-antesis [DVS] (default 0,0; "
                                "menggeser breakpoint FLTB/FSTB/FOTB/FRTB untuk DVS >= 1,0 secara serentak, sehingga "
                                "FL+FS+FO=1 tetap terjaga; lihat shift_postanthesis_partitioning)"}
POSTANTH_TABLES = ("FRTB", "FLTB", "FSTB", "FOTB")
POSTANTH_ANCHOR = 1.0


def shift_postanthesis_partitioning(table: list, shift: float, anchor: float = POSTANTH_ANCHOR) -> list:
    """Geser breakpoint DVS (x) tabel partisi untuk x >= anchor (antesis) sebesar `shift` [DVS], nilai-y (fraksi)
    tidak diubah. Karena FL(x)+FS(x)+FO(x)=1 berlaku titik demi titik pada tabel asli WOFOST dan interpolasi AFGEN
    bersifat afin, menggeser sumbu-x TIGA tabel (FLTB, FSTB, FOTB) dengan fungsi yang SAMA menjaga identitas ini di
    semua DVS -- tidak perlu menormalkan ulang. shift > 0 menunda alokasi penuh ke organ simpan (memperpanjang
    pertumbuhan batang pasca-berbunga); shift dibatasi agar breakpoint tidak turun di bawah anchor."""
    out = list(table)
    for i in range(0, len(out) - 1, 2):
        x = float(out[i])
        if x > anchor + 1e-9:
            out[i] = max(anchor + 1e-6, x + shift)
    return out


# Parameter yang hanya dipakai model terbatas N (WOFOST 8.1); diabaikan bila proyek dijalankan dengan model 7.x
N_ONLY_PARAMS = {"NMAXSO", "NMAXRT_FR", "NMAXST_FR", "NCRIT_FR", "NRESIDLV", "NRESIDST", "NRESIDRT", "TCNT", "NFIX_FR",
                 "RNUPTAKEMAX", "DVS_N_TRANSL", "RGRLAI_MIN", "RGRLAI_MIN_FR", "AMAX_SLP", "AMAX_LNB", "AMAX_REF", "KN",
                 "NSLA", "NPART", "NLAI", "NMAXLV_TB", "NSLLV_TB"}


def is_n_model(model_name: str) -> bool:
    return model_name.startswith("Wofost81")


def virtual_scalar_defaults(prov, model_name: str) -> dict[str, float]:
    out = {}
    if is_n_model(model_name) and "RGRLAI_MIN" in prov and float(prov.get("RGRLAI", 0) or 0) > 0:
        out["RGRLAI_MIN_FR"] = float(prov["RGRLAI_MIN"]) / float(prov["RGRLAI"])
    if all(t in prov for t in POSTANTH_TABLES):
        out["PART_DELAY"] = 0.0
    return out


def crop_provider_for(model_cls):
    """YAMLCropDataProvider yang cocok dengan model: WOFOST 8.1 memakai salinan lokal cabang wofost81
    (offline, tereproduksi); model lain memakai salinan bawaan PCSE."""
    from pcse.input import YAMLCropDataProvider
    if getattr(model_cls, "__cropmodelversion__", "") == "8.1" and (CROP_PARAM_DIR_81 / "crops.yaml").exists():
        return YAMLCropDataProvider(fpath=str(CROP_PARAM_DIR_81), model=model_cls)
    return YAMLCropDataProvider(model=model_cls)


def n_assim_defaults(prov, model_name: str = "") -> dict[str, float]:
    """Nilai default AMAX_REF/KN (dan NSLA/NPART untuk model ekstensi) bila varietas belum memilikinya."""
    out = {}
    if model_name in EXTENSION_MODELS:
        from .wofost81_nleaf import NLEAF_DEFAULTS
        out.update({k: v for k, v in NLEAF_DEFAULTS.items() if k not in prov})
    if "AMAX_REF" not in prov:
        tab = prov.get("AMAXTB", [0.0, 40.0])
        out["AMAX_REF"] = float(max(tab[1::2])) if len(tab) >= 2 else 40.0
    if "KN" not in prov:
        out["KN"] = 0.4
    return out

SUMMARY_VARS = {
    "TWSO": "Bobot organ penyimpanan / hasil [kg/ha]",
    "TAGP": "Total biomassa atas tanah [kg/ha]",
    "LAIMAX": "Indeks luas daun maksimum [-]",
    "TWLV": "Bobot daun [kg/ha]",
    "TWST": "Bobot batang [kg/ha]",
    "TWRT": "Bobot akar [kg/ha]",
    "CTRAT": "Transpirasi kumulatif [cm]",
    "CEVST": "Evaporasi tanah kumulatif [cm]",
    "RD": "Kedalaman akar akhir [cm]",
    "DVS": "Tahap perkembangan akhir [-]",
    "DURASI_HARI": "Durasi emergensi ke masak [hari]",
    "NuptakeTotal": "Serapan N kumulatif [kg N/ha] (WOFOST 8.1)",
    "NamountSO": "N dalam gabah [kg N/ha] (WOFOST 8.1)",
}

DAILY_VARS = {
    "DVS": "Tahap perkembangan [-]",
    "LAI": "Indeks luas daun [-]",
    "TAGP": "Biomassa atas tanah [kg/ha]",
    "TWSO": "Bobot organ penyimpanan [kg/ha]",
    "TWLV": "Bobot daun [kg/ha]",
    "TWST": "Bobot batang [kg/ha]",
    "TWRT": "Bobot akar [kg/ha]",
    "TRA": "Transpirasi [cm/hari]",
    "RD": "Kedalaman akar [cm]",
    "SM": "Kadar air zona akar [cm3/cm3]",
    "WWLOW": "Air di sub-tanah [cm]",
    "RFTRA": "Faktor reduksi transpirasi [-]",
    "NAVAIL": "N mineral tersedia di tanah [kg N/ha] (WOFOST 8.1)",
    "NuptakeTotal": "Serapan N kumulatif tanaman [kg N/ha] (WOFOST 8.1)",
    "NamountLV": "Kandungan N daun [kg N/ha] (WOFOST 8.1)",
    "NamountSO": "Kandungan N gabah/organ simpan [kg N/ha] (WOFOST 8.1)",
    "Ndemand": "Kebutuhan N tanaman [kg N/ha/hari] (WOFOST 8.1)",
}

# Parameter tanaman yang lazim dikalibrasi/dianalisis, dengan deskripsi singkat.
CROP_PARAM_INFO = {
    "TSUM1": "Suhu-jumlah dari emergensi ke antesis [C.d]",
    "TSUM2": "Suhu-jumlah dari antesis ke masak [C.d]",
    "TSUMEM": "Suhu-jumlah dari tanam ke emergensi [C.d]",
    "TBASEM": "Suhu dasar emergensi [C]",
    "TEFFMX": "Suhu efektif maksimum emergensi [C]",
    "TBASE": "Suhu dasar pertumbuhan awal daun [C]",
    "TDWI": "Bobot kering awal tanaman [kg/ha]",
    "RGRLAI": "Laju pertumbuhan relatif LAI maksimum [ha/ha/d]",
    "SPAN": "Umur daun pada 35 C [d]",
    "SPA": "Luas spesifik polong/organ [ha/kg]",
    "CVL": "Efisiensi konversi asimilat ke daun [kg/kg]",
    "CVO": "Efisiensi konversi asimilat ke organ penyimpanan [kg/kg]",
    "CVR": "Efisiensi konversi asimilat ke akar [kg/kg]",
    "CVS": "Efisiensi konversi asimilat ke batang [kg/kg]",
    "Q10": "Peningkatan respirasi per 10 C [-]",
    "RML": "Laju respirasi pemeliharaan daun [kg CH2O/kg/d]",
    "RMO": "Laju respirasi pemeliharaan organ penyimpanan",
    "RMR": "Laju respirasi pemeliharaan akar",
    "RMS": "Laju respirasi pemeliharaan batang",
    "PERDL": "Laju kematian relatif daun maksimum akibat cekaman air",
    "CFET": "Faktor koreksi transpirasi [-]",
    "DEPNR": "Nomor kelompok tanaman untuk kepekaan kekeringan [-]",
    "RDI": "Kedalaman akar awal [cm]",
    "RRI": "Laju pertambahan kedalaman akar [cm/d]",
    "RDMCR": "Kedalaman akar maksimum tanaman [cm]",
    "DVSI": "DVS awal [-]",
    "DVSEND": "DVS akhir [-]",
    "IDSL": "Sakelar respon panjang hari/vernalisasi",
    "DLO": "Panjang hari optimum [jam]",
    "DLC": "Panjang hari kritis [jam]",
    "IAIRDU": "Saluran udara di akar (0/1)",
    "IOX": "Sakelar cekaman oksigen (0/1)",
    # ---- WOFOST 8.1: nitrogen ----
    "NMAXRT_FR": "Konsentrasi N maks akar sebagai fraksi dari daun [-]",
    "NMAXST_FR": "Konsentrasi N maks batang sebagai fraksi dari daun [-]",
    "NMAXSO": "Konsentrasi N maksimum organ simpan [kg N/kg BK]",
    "NCRIT_FR": "Konsentrasi N kritis sebagai fraksi N maksimum [-]",
    "NRESIDLV": "Konsentrasi N residu daun [kg N/kg BK]",
    "NRESIDST": "Konsentrasi N residu batang [kg N/kg BK]",
    "NRESIDRT": "Konsentrasi N residu akar [kg N/kg BK]",
    "TCNT": "Koefisien waktu translokasi N ke organ simpan [hari]",
    "NFIX_FR": "Fraksi serapan N dari fiksasi biologis [-]",
    "RNUPTAKEMAX": "Laju serapan N maksimum [kg N/ha/hari]",
    "DVS_N_TRANSL": "DVS mulai translokasi N ke organ simpan [-]",
    "RGRLAI_MIN": "Laju pertambahan LAI relatif pada cekaman N maksimum [ha/ha/hari]",
    "AMAX_SLP": "Kemiringan AMAX terhadap N daun spesifik [kg CO2/ha/jam per kg N/ha]",
    "AMAX_LNB": "N daun spesifik saat fotosintesis nol [kg N/ha]",
    "REFCO2L": "CO2 referensi [ppm]",
    "VERNBASE": "Vernalisasi dasar [d]",
    "VERNSAT": "Vernalisasi jenuh [d]",
    "VERNDVS": "DVS kritis vernalisasi",
}

# Parameter sakelar/integer yang tidak cocok untuk analisis kontinu.
NON_CONTINUOUS_PARAMS = {"IDSL", "IAIRDU", "IOX", "DVSI", "DVSEND", "REFCO2L", "DEPNR"}

# Parameter tabel (AFGEN) yang dapat dimodifikasi lewat parameter virtual:
#   NAME@y = pengali seluruh nilai-y tabel (default 1.0); NAME@x = geseran sumbu-x [C] untuk tabel respons suhu.
TABLE_YSCALE = {
    "AMAXTB": "Laju asimilasi CO2 maksimum daun vs DVS",
    "EFFTB": "Efisiensi penggunaan cahaya vs suhu",
    "SLATB": "Luas daun spesifik vs DVS",
    "KDIFTB": "Koefisien pemadaman cahaya difus vs DVS",
    "TMPFTB": "Faktor reduksi AMAX vs suhu siang (di-clip 0-1)",
    "TMNFTB": "Faktor reduksi asimilasi vs suhu minimum (di-clip 0-1)",
    "DTSMTB": "Laju pertambahan suhu-jumlah vs suhu harian",
    "RDRRTB": "Laju kematian relatif akar vs DVS",
    "RDRSTB": "Laju kematian relatif batang vs DVS",
    "SSATB": "Luas batang spesifik vs DVS",
    "NMAXLV_TB": "Konsentrasi N maksimum daun vs DVS (WOFOST 8.1)",
    "NSLLV_TB": "Faktor percepatan senesens daun vs indeks cekaman N (WOFOST 8.1)",
}
TABLE_XSHIFT = {"TMPFTB": "Geser respons suhu siang", "TMNFTB": "Geser respons suhu minimum",
                "DTSMTB": "Geser respons fenologi terhadap suhu", "EFFTB": "Geser respons efisiensi cahaya vs suhu"}
TABLE_CLIP01 = {"TMPFTB", "TMNFTB"}
XSHIFT_RANGE = (-3.0, 3.0)
# Tabel vs DVS yang boleh diskalakan terpisah untuk fase awal (DVS < SPLIT) dan akhir (DVS >= SPLIT):
#   NAME@ya = pengali nilai-y untuk x < 0.65, NAME@yb = pengali untuk x >= 0.65 (nilai batas diinterpolasi mulus).
TABLE_YSPLIT = {"SLATB": "Luas daun spesifik: awal (@ya, DVS < 0.65) / akhir (@yb, DVS >= 0.65)",
                "AMAXTB": "AMAX: awal (@ya) / akhir (@yb)", "KDIFTB": "Koefisien pemadaman: awal / akhir"}
YSPLIT_DVS = 0.65


def table_param_info() -> dict[str, str]:
    info = {f"{t}@y": f"Pengali nilai-y tabel {t}: {d}" for t, d in TABLE_YSCALE.items()}
    info.update({f"{t}@x": f"Geseran sumbu-x [C] tabel {t}: {d}" for t, d in TABLE_XSHIFT.items()})
    for t, d in TABLE_YSPLIT.items():
        info[f"{t}@ya"] = f"Pengali nilai-y tabel {t} untuk DVS < {YSPLIT_DVS}: {d}"
        info[f"{t}@yb"] = f"Pengali nilai-y tabel {t} untuk DVS >= {YSPLIT_DVS}: {d}"
    return info


CROP_PARAM_INFO.update(table_param_info())
CROP_PARAM_INFO.update(N_ASSIM_EXTRA)
CROP_PARAM_INFO.update(VIRTUAL_SCALARS)


def apply_table_modifiers(table: list, yscale: float = 1.0, xshift: float = 0.0, clip01: bool = False,
                          ya: float = 1.0, yb: float = 1.0, split: float = YSPLIT_DVS) -> list:
    """yscale: pengali seragam; ya/yb: pengali fase awal/akhir (transisi linear antara split-0.15 dan split+0.15)."""
    out = list(table)
    for i in range(0, len(out) - 1, 2):
        x = float(out[i])
        out[i] = x + float(xshift)
        if ya != 1.0 or yb != 1.0:
            w = min(max((x - (split - 0.15)) / 0.30, 0.0), 1.0)      # 0 di fase awal, 1 di fase akhir
            f = (1 - w) * float(ya) + w * float(yb)
        else:
            f = 1.0
        y = float(out[i + 1]) * float(yscale) * f
        out[i + 1] = min(max(y, 0.0), 1.0) if clip01 else y
    return out


def split_overrides(overrides: dict) -> tuple[dict, dict[str, dict]]:
    """Pisahkan override skalar dan pengubah tabel {tabel: {"y": f, "x": s}}."""
    scalars, tables = {}, {}
    for k, v in overrides.items():
        if "@" in k:
            base, kind = k.split("@", 1)
            tables.setdefault(base, {})[kind] = float(v)
        else:
            scalars[k] = v
    return scalars, tables


@dataclass
class SimulationResult:
    daily: pd.DataFrame
    summary: dict
    config: SimulationConfig
    overrides: dict = field(default_factory=dict)
    runtime_s: float = 0.0

    @property
    def yield_kg_ha(self) -> float | None:
        v = self.summary.get("TWSO")
        return None if v is None else float(v)


def get_model_class(name: str):
    if name in EXTENSION_MODELS:
        from . import wofost81_nleaf
        return getattr(wofost81_nleaf, name)
    from pcse import models
    return getattr(models, name)


def list_crops() -> dict[str, list[str]]:
    from pcse.input import YAMLCropDataProvider
    prov = YAMLCropDataProvider()
    return {crop: list(vars_) for crop, vars_ in sorted(prov.get_crops_varieties().items())}


def scalar_crop_params(model_name: str, crop: str, variety: str) -> dict[str, float]:
    """Parameter tanaman skalar (bukan tabel) untuk tanaman/varietas terpilih."""
    cls = get_model_class(model_name)
    prov = crop_provider_for(cls)
    prov.set_active_crop(crop, variety)
    out = {}
    for k, v in prov.items():
        if isinstance(v, bool):
            continue
        if isinstance(v, (int, float)):
            out[k] = float(v)
    if is_n_model(model_name):
        out.update(n_assim_defaults(prov, model_name))
    vs = virtual_scalar_defaults(prov, model_name)   # PART_DELAY berlaku untuk semua model; RGRLAI_MIN_FR khusus N
    if vs:
        out.pop("RGRLAI_MIN", None)                  # RGRLAI_MIN diganti rasio agar ikut RGRLAI yang dikalibrasi
        out.update(vs)
    return dict(sorted(out.items()))


def analysis_crop_params(model_name: str, crop: str, variety: str) -> dict[str, float]:
    """Parameter skalar + parameter virtual tabel (NAME@y = 1.0, NAME@x = 0.0) yang ada pada tanaman ini."""
    prov = crop_provider_for(get_model_class(model_name))
    prov.set_active_crop(crop, variety)
    out = scalar_crop_params(model_name, crop, variety)
    for t in TABLE_YSCALE:
        if t in prov and isinstance(prov[t], (list, tuple)):
            out[f"{t}@y"] = 1.0
    for t in TABLE_XSHIFT:
        if t in prov and isinstance(prov[t], (list, tuple)):
            out[f"{t}@x"] = 0.0
    for t in TABLE_YSPLIT:
        if t in prov and isinstance(prov[t], (list, tuple)):
            out[f"{t}@ya"] = 1.0
            out[f"{t}@yb"] = 1.0
    return out


def _make_site81_wide():
    """Penyedia situs WOFOST 8.1 dengan rentang NSOILBASE diperlebar (0-400 kg N/ha).
    Batas 0-100 di PCSE 6.0.13 hanyalah validasi input, bukan batas fisiologis; pasokan N tanah asli padi sawah
    irigasi Asia dapat melebihi 100 kg N/ha per musim (Dobermann et al. 2003), dan batas 100 memotong posterior."""
    from pcse.input import WOFOST81SiteDataProvider_Classic as _B
    d = dict(_B._defaults); d["NSOILBASE"] = (0, (0, 400), float)
    return type("WOFOST81SiteDataProvider_ClassicWide", (_B,), {"_defaults": d})


_Site81Wide = _make_site81_wide()


class SimulationRunner:
    """Membungkus PCSE agar mudah dijalankan berulang (batch/sensitivitas/kalibrasi)."""

    def __init__(self, cfg: SimulationConfig, wdp):
        self.cfg = cfg
        self.wdp = wdp
        self.model_cls = get_model_class(cfg.model_name)
        self.crop_provider = crop_provider_for(self.model_cls)
        self.crop_provider.set_active_crop(cfg.crop_name, cfg.variety_name)

    # -- parameter --------------------------------------------------------
    def _site_provider(self):
        from pcse.input import WOFOST72SiteDataProvider, WOFOST73SiteDataProvider, WOFOST81SiteDataProvider_Classic
        name = self.cfg.model_name
        if name.startswith("Wofost81"):
            cls = _Site81Wide
        elif name.startswith("Wofost73"):
            cls = WOFOST73SiteDataProvider
        else:
            cls = WOFOST72SiteDataProvider
        allowed = set(cls._defaults.keys())
        kwargs = {k: v for k, v in self.cfg.site.items() if k in allowed}
        if cls is _Site81Wide:
            for k in ("WAV", "NAVAILI", "CO2"):          # wajib untuk penyedia 8.1
                kwargs.setdefault(k, {"WAV": 10.0, "NAVAILI": 20.0, "CO2": 400.0}[k])
        if "IFUNRN" in kwargs:
            kwargs["IFUNRN"] = int(kwargs["IFUNRN"])
        return cls(**kwargs)

    def build_params(self, overrides: dict | None = None):
        from pcse.base import ParameterProvider
        soil = {k: float(v) for k, v in self.cfg.soil.items()}
        params = ParameterProvider(cropdata=self.crop_provider, soildata=soil, sitedata=self._site_provider())
        merged = dict(self.cfg.crop_overrides)
        if overrides:
            merged.update(overrides)
        scalars, tables = split_overrides(merged)
        if not is_n_model(self.cfg.model_name):
            # proyek WOFOST 8.1 yang dijalankan dengan model tanpa neraca N: parameter khusus N tidak berlaku -> abaikan
            dropped = [k for k in list(scalars) if k in N_ONLY_PARAMS and k not in self.crop_provider]
            dropped += [t for t in list(tables) if t in N_ONLY_PARAMS and t not in self.crop_provider]
            for k in dropped:
                scalars.pop(k, None); tables.pop(k, None)
            if dropped:
                import logging
                logging.getLogger(__name__).warning("Parameter khusus N diabaikan untuk %s: %s", self.cfg.model_name, sorted(dropped))
        vdef = virtual_scalar_defaults(self.crop_provider, self.cfg.model_name)
        vvals = {k: float(scalars.pop(k, vdef.get(k, 0.0))) for k in VIRTUAL_SCALARS if k in scalars or k in vdef}
        if is_n_model(self.cfg.model_name):
            for k, v in n_assim_defaults(self.crop_provider, self.cfg.model_name).items():
                scalars.setdefault(k, v)
            if "AMAX_REF" not in merged and "AMAXTB" in tables and "AMAXTB" in self.crop_provider:
                # konsistensi dengan kalibrasi model potensial: WOFOST 8.1 tidak memakai AMAXTB, hanya AMAX_REF;
                # tanpa ini pengali AMAXTB@y hasil kalibrasi 7.2 hilang diam-diam di 8.1.
                m = tables["AMAXTB"]
                tab = apply_table_modifiers(list(self.crop_provider["AMAXTB"]), m.get("y", 1.0), m.get("x", 0.0),
                                            ya=m.get("ya", 1.0), yb=m.get("yb", 1.0))
                scalars["AMAX_REF"] = float(max(tab[1::2]))
            if "RGRLAI_MIN_FR" in vvals and "RGRLAI_MIN" not in scalars:
                rgr = float(scalars.get("RGRLAI", self.crop_provider["RGRLAI"]))
                scalars["RGRLAI_MIN"] = vvals["RGRLAI_MIN_FR"] * rgr
        for k, v in scalars.items():
            params.set_override(k, v, check=k not in N_ASSIM_EXTRA)
        for t, mods in tables.items():
            if t not in self.crop_provider:
                raise KeyError(f"Tabel {t} tidak ada pada tanaman {self.cfg.crop_name}.")
            new = apply_table_modifiers(list(self.crop_provider[t]), mods.get("y", 1.0), mods.get("x", 0.0),
                                        clip01=t in TABLE_CLIP01, ya=mods.get("ya", 1.0), yb=mods.get("yb", 1.0))
            params.set_override(t, new, check=True)
        part_delay = vvals.get("PART_DELAY", 0.0)
        if part_delay != 0.0:
            for t in POSTANTH_TABLES:
                if t not in self.crop_provider:
                    continue
                base = list(params[t]) if t in tables else list(self.crop_provider[t])
                params.set_override(t, shift_postanthesis_partitioning(base, part_delay), check=True)
        return params

    # -- run --------------------------------------------------------------
    def run(self, overrides: dict | None = None,
            crop_start_date: dt.date | None = None,
            crop_end_date: dt.date | None = None) -> SimulationResult:
        t0 = time.perf_counter()
        params = self.build_params(overrides)
        if self.cfg.crop_start_type == "sowing" and float(params.get("TSUMEM", 1.0) or 0.0) <= 0.0:
            raise ValueError(
                f"Varietas {self.cfg.variety_name} memiliki TSUMEM = 0 (tanaman pindah tanam). "
                "Gunakan tipe awal 'emergence', atau isi TSUMEM > 0 pada override parameter.")
        start = crop_start_date or self.cfg.crop_start_date
        shock = None
        if self.cfg.transplant_shock and self.cfg.crop_start_type == "emergence":
            shock = self.transplant_shock_info(start)
            # penundaan perkembangan: TSUM1 efektif bertambah SHCKD x TSTR (DVS terus dihitung, target lebih jauh)
            params.set_override("TSUM1", float(params["TSUM1"]) + shock["delay_dev_tt"], check=True)
        agro = self.cfg.to_agromanagement(crop_start_date, crop_end_date)
        model = self.model_cls(params, self.wdp, agro)
        if shock is None:
            model.run_till_terminate()
        else:
            # penundaan pertumbuhan daun: LAI ditahan pada nilai awal selama SHCKL x TSTR (jumlah suhu efektif)
            lai0 = model.get_variable("LAI")
            tt = 0.0
            while not model.flag_terminate and tt < shock["delay_leaf_tt"]:
                d = model.day
                model.run(1)
                tt += self._eff_temp(d)
                cur = model.get_variable("LAI")
                if lai0 is not None and cur is not None and cur > lai0:
                    model.set_variable("LAI", float(lai0))
            model.run_till_terminate()
        daily = pd.DataFrame(model.get_output())
        if "day" in daily.columns:
            daily["day"] = pd.to_datetime(daily["day"])
            daily = daily.set_index("day")
        summ_list = model.get_summary_output()
        summary = dict(summ_list[0]) if summ_list else {}
        if summary.get("DOE") and summary.get("DOM"):
            summary["DURASI_HARI"] = (summary["DOM"] - summary["DOE"]).days
        return SimulationResult(daily=daily, summary=summary, config=self.cfg,
                                overrides=dict(overrides or {}), runtime_s=time.perf_counter() - t0)

    def base_value(self, name: str) -> float:
        """Nilai dasar parameter (termasuk virtual) sesudah override konfigurasi."""
        merged = dict(self.cfg.crop_overrides)
        if name in merged:
            return float(merged[name])
        if "@" in name:
            return 0.0 if name.endswith("@x") else 1.0
        vdef = virtual_scalar_defaults(self.crop_provider, self.cfg.model_name)
        if name in vdef:
            return float(vdef[name])
        return float(self.build_params()[name])

    def _eff_temp(self, day: dt.date, tbase: float = 8.0, topt: float = 30.0) -> float:
        """Suhu efektif harian (C.d) ala ORYZA/DTSMTB padi: linear Tbase..Topt, dibatasi pada Topt."""
        try:
            w = self.wdp(day)
            t = 0.5 * (float(w.TMIN) + float(w.TMAX))
        except Exception:  # noqa: BLE001
            return 0.0
        return max(0.0, min(t, topt) - tbase)

    def transplant_shock_info(self, transplant_date: dt.date) -> dict:
        """TSTR (jumlah suhu persemaian) dan lama penundaan daun/perkembangan dalam C.d dan perkiraan hari."""
        cfg = self.cfg
        sow = transplant_date - dt.timedelta(days=int(cfg.seedling_age_days))
        tstr = sum(self._eff_temp(sow + dt.timedelta(days=i)) for i in range(int(cfg.seedling_age_days)))
        mean_tt = tstr / max(int(cfg.seedling_age_days), 1)
        dl, dd = float(cfg.shckl) * tstr, float(cfg.shckd) * tstr
        return {"sowing_date": sow, "TSTR": tstr, "delay_leaf_tt": dl, "delay_dev_tt": dd,
                "delay_leaf_days": dl / mean_tt if mean_tt else 0.0, "delay_dev_days": dd / mean_tt if mean_tt else 0.0}

    @staticmethod
    def summary_value(result: SimulationResult, target: str) -> float:
        v = result.summary.get(target)
        if v is None:
            return float("nan")
        if isinstance(v, dt.date):
            return float(v.timetuple().tm_yday)
        return float(v)


def run_sowing_batch(runner: SimulationRunner, sowing_dates: list[dt.date], duration_days: int,
                     progress: Callable[[int, int, str], None] | None = None,
                     cancelled: Callable[[], bool] | None = None) -> pd.DataFrame:
    """Jalankan simulasi untuk banyak tanggal tanam. Kembalikan tabel ringkasan."""
    rows = []
    n = len(sowing_dates)
    for i, d in enumerate(sowing_dates, 1):
        if cancelled and cancelled():
            break
        end = d + dt.timedelta(days=duration_days)
        row = {"tanggal_tanam": d, "tahun": d.year, "DOY": d.timetuple().tm_yday}
        try:
            res = runner.run(crop_start_date=d, crop_end_date=end)
            s = res.summary
            row.update({
                "TWSO": s.get("TWSO"), "TAGP": s.get("TAGP"), "LAIMAX": s.get("LAIMAX"),
                "CTRAT": s.get("CTRAT"), "DOE": s.get("DOE"), "DOA": s.get("DOA"), "DOM": s.get("DOM"),
                "DURASI_HARI": s.get("DURASI_HARI"), "status": "OK",
            })
        except Exception as e:  # noqa: BLE001
            row.update({"status": f"GAGAL: {type(e).__name__}: {e}"[:200]})
        rows.append(row)
        if progress:
            progress(i, n, f"Tanggal tanam {d.isoformat()}")
    return pd.DataFrame(rows)
