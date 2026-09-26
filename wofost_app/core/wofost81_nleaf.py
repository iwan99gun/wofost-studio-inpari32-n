"""Ekstensi WOFOST 8.1: efek cekaman N pada luas daun spesifik (SLA) dan partisi ke daun, tipe LINTUL3.

Latar belakang
--------------
WOFOST 8.1 (PCSE 6.0.13) menerapkan cekaman N pada tajuk hanya lewat (i) AMAX yang bergantung N daun spesifik,
(ii) RGRLAI pada fase juvenil (hanya bila DVS < 0,2 dan LAI < 0,75) dan (iii) percepatan senesens (NSLLV_TB).
Untuk padi Inpari-32 di KP Sukamandi (Sujinah et al. 2020) luas daun saat berbunga turun 36 % pada 23 vs 115 kg N/ha
sedangkan biomasa hanya turun 18 %: luas daun merespons N lebih kuat daripada biomasa. Pola ini tidak bisa dihasilkan
WOFOST 8.1 karena SLA dan fraksi daun di sana tidak bergantung N.

LINTUL3 (Shibu et al. 2010, Eur. J. Agron. 32:255-271; model N-terbatas yang dikembangkan untuk padi dan juga ada di PCSE,
`pcse.crop.lintul3`) memodelkan dua jalur tambahan:
    SLA = SLA_pot * exp(-NSLA  * (1 - NNI))
    FL  = FL_pot  * exp(-NPART * (1 - NNI)),  sisa fraksi dibagikan proporsional ke batang dan organ simpan
    GLAIEX = GLAIEX_pot * exp(-NLAI * (1 - NNI)) setelah fase juvenil (LINTUL3 menerapkannya pada fase juvenil;
             di WOFOST ekspansi terbatas-sink berlanjut sampai LAIEXP = 6 sehingga faktor diperluas ke seluruh fase itu)
dengan koefisien bawaan PCSE NSLA = NPART = NLAI = 1,0. Modul ini menambahkan kedua jalur itu ke WOFOST 8.1 tanpa mengubah
jalur lainnya (AMAX(SLN), RGRLAI juvenil, NSLLV_TB tetap berlaku), sehingga NSLA = NPART = NLAI = 0 identik dengan WOFOST 8.1.

NNI dihitung dengan definisi WOFOST 8.0 (`pcse.crop.nutrients.npk_stress`): konsentrasi N biomassa vegetatif
(daun + batang) relatif terhadap konsentrasi kritis (NCRIT_FR x maksimum) dan residu.
"""
from __future__ import annotations

from math import exp
from pathlib import Path

from pcse.base import ParamTemplate
from pcse.crop import wofost81 as _w81
from pcse.crop.leaf_dynamics import WOFOST_Leaf_Dynamics_N
from pcse.crop.partitioning import DVS_Partitioning_N, PartioningFactors
from pcse.decorators import prepare_rates, prepare_states
from pcse.engine import Engine
from pcse.traitlets import Float
from pcse.util import AfgenTrait, limit

CONF_PATH = Path(__file__).resolve().parent / "conf" / "Wofost81_NWLP_CWB_CNB_NLV.conf"
NLEAF_DEFAULTS = {"NSLA": 1.0, "NPART": 1.0, "NLAI": 1.0}     # koefisien bawaan LINTUL3 di PCSE


class _NNIParams(ParamTemplate):
    NMAXLV_TB = AfgenTrait()
    NMAXST_FR = Float(-99.)
    NCRIT_FR = Float(-99.)
    NRESIDLV = Float(-99.)
    NRESIDST = Float(-99.)


def nitrogen_nutrition_index(k, p) -> float:
    """NNI tipe WOFOST 8.0 dari variabel kiosk (WLV, WST, NamountLV, NamountST, DVS). 1 = tanpa cekaman."""
    try:
        wlv, wst = float(k.WLV), float(k.WST)
        nlv, nst = float(k.NamountLV), float(k.NamountST)
        dvs = float(k.DVS)
    except (AttributeError, KeyError, TypeError):
        return 1.0
    vbm = wlv + wst
    if vbm <= 0.0:
        return 1.0
    nmaxlv = p.NMAXLV_TB(dvs)
    nmaxst = p.NMAXST_FR * nmaxlv
    ncrit = (p.NCRIT_FR * nmaxlv * wlv + p.NCRIT_FR * nmaxst * wst) / vbm
    nres = (p.NRESIDLV * wlv + p.NRESIDST * wst) / vbm
    nconc = (nlv + nst) / vbm
    if ncrit - nres <= 0.0:
        return 1.0
    return limit(0.001, 1.0, (nconc - nres) / (ncrit - nres))


class DVS_Partitioning_N_Leaf(DVS_Partitioning_N):
    """Partisi WOFOST 8.1 + reduksi fraksi daun FL = FL_pot exp(-NPART (1-NNI)) (LINTUL3)."""

    class Parameters(DVS_Partitioning_N.Parameters):
        NPART = Float(-99.)
        NMAXLV_TB = AfgenTrait()
        NMAXST_FR = Float(-99.)
        NCRIT_FR = Float(-99.)
        NRESIDLV = Float(-99.)
        NRESIDST = Float(-99.)

    def calc_rates(self, day, drv):
        # NNI harus dihitung di tahap laju: saat tahap integrasi PCSE mengosongkan state (WLV, WST, ...) dari kiosk
        # sampai tiap komponen memperbaruinya, sehingga NNI tidak bisa dihitung di integrate().
        self._nni = nitrogen_nutrition_index(self.kiosk, self.params)
        return super().calc_rates(day, drv)

    @prepare_states
    def integrate(self, day, delt=1.0):
        p, s, k = self.params, self.states, self.kiosk
        FRTMOD = max(1., 1. / (k.RFTRA + 0.5))
        s.FR = min(0.6, p.FRTB(k.DVS) * FRTMOD)
        FL, FS, FO = p.FLTB(k.DVS), p.FSTB(k.DVS), p.FOTB(k.DVS)
        if p.NPART > 0.0 and FL > 0.0:
            nni = getattr(self, "_nni", 1.0)
            if nni < 1.0:
                FLN = FL * exp(-p.NPART * (1.0 - nni))
                rest = FS + FO
                if rest > 0.0:                     # sisa fraksi daun dibagi proporsional ke batang & organ simpan
                    FS += (FL - FLN) * FS / rest
                    FO += (FL - FLN) * FO / rest
                else:
                    FS += FL - FLN
                FL = FLN
        s.FL, s.FS, s.FO = FL, FS, FO
        s.PF = PartioningFactors(s.FR, s.FL, s.FS, s.FO)
        self._check_partitioning()


class WOFOST_Leaf_Dynamics_N_SLA(WOFOST_Leaf_Dynamics_N):
    """Dinamika daun WOFOST 8.1 + SLA = SLATB(DVS) exp(-NSLA (1-NNI)) untuk daun baru (LINTUL3)."""

    class Parameters(WOFOST_Leaf_Dynamics_N.Parameters):
        NSLA = Float(-99.)
        NLAI = Float(-99.)
        NMAXLV_TB = AfgenTrait()
        NMAXST_FR = Float(-99.)
        NCRIT_FR = Float(-99.)
        NRESIDLV = Float(-99.)
        NRESIDST = Float(-99.)

    @prepare_rates
    def calc_rates(self, day, drv):
        # salinan WOFOST_Leaf_Dynamics_N.calc_rates (PCSE 6.0.13) dengan satu perubahan: faktor N pada SLAT
        r, s, p, k = self.rates, self.states, self.params, self.kiosk
        r.GRLV = k.ADMI * k.FL
        r.DSLV1 = s.WLV * (1. - k.RFTRA) * p.PERDL
        LAICR = 3.2 / p.KDIFTB(k.DVS)
        r.DSLV2 = s.WLV * limit(0., 0.03, 0.03 * (s.LAI - LAICR) / LAICR)
        r.DSLV3 = s.WLV * k.RF_FROST if "RF_FROST" in k else 0.
        DALV = 0.0
        for lv, lvage in zip(s.LV, s.LVAGE):
            if lvage > p.SPAN:
                DALV += lv
        r.DALV = DALV
        r.DSLV = max(r.DSLV1, r.DSLV2, r.DSLV3)
        r.DALV = min(DALV * k.NSLLV, k.WLV)
        r.DRLV = max(r.DSLV, r.DALV)
        r.FYSAGE = max(0., (drv.TEMP - p.TBASE) / (35. - p.TBASE))
        nni = nitrogen_nutrition_index(k, p) if (p.NSLA > 0.0 or p.NLAI > 0.0) else 1.0
        fN = exp(-p.NSLA * (1.0 - nni)) if p.NSLA > 0.0 else 1.0
        r.SLAT = p.SLATB(k.DVS) * fN
        if s.LAIEXP < 6.:
            DTEFF = max(0., drv.TEMP - p.TBASE)
            if k.DVS < 0.2 and s.LAI < 0.75:
                factor = k.RFTRA * k.RFRGRL            # jalur asli WOFOST 8.1 (fase juvenil)
            else:
                # EKSTENSI: WOFOST 8.1 tidak menerapkan cekaman N pada ekspansi daun terbatas-sink setelah fase juvenil,
                # padahal NNI padi 23 kg N/ha sudah < 1 sejak ~21 HST. Faktor LINTUL3 exp(-NLAI(1-NNI)) diterapkan
                # sepanjang fase eksponensial (LAIEXP < 6). NLAI = 0 -> identik dengan WOFOST 8.1.
                factor = exp(-p.NLAI * (1.0 - nni)) if p.NLAI > 0.0 else 1.

            r.GLAIEX = s.LAIEXP * p.RGRLAI * DTEFF * factor
            r.GLASOL = r.GRLV * r.SLAT
            GLA = min(r.GLAIEX, r.GLASOL)
            if r.GRLV > 0.:
                r.SLAT = GLA / r.GRLV


class Wofost81NLeaf(_w81.Wofost81):
    """WOFOST 8.1 dengan komponen daun & partisi yang peka N (lihat docstring modul)."""

    def initialize(self, day, kiosk, parvalues):
        # salinan Wofost81.initialize (PCSE 6.0.13) dengan Partitioning dan Leaf_Dynamics diganti
        self.params = self.Parameters(parvalues)
        self.rates = self.RateVariables(kiosk, publish=["DMI", "ADMI", "REALLOC_LV", "REALLOC_ST", "REALLOC_SO"])
        self.kiosk = kiosk
        self.pheno = _w81.Phenology(day, kiosk, parvalues)
        self.part = DVS_Partitioning_N_Leaf(day, kiosk, parvalues)
        self.assim = _w81.Assimilation(day, kiosk, parvalues)
        self.mres = _w81.MaintenanceRespiration(day, kiosk, parvalues)
        self.evtra = _w81.Evapotranspiration(day, kiosk, parvalues)
        self.ro_dynamics = _w81.Root_Dynamics(day, kiosk, parvalues)
        self.st_dynamics = _w81.Stem_Dynamics(day, kiosk, parvalues)
        self.so_dynamics = _w81.Storage_Organ_Dynamics(day, kiosk, parvalues)
        self.lv_dynamics = WOFOST_Leaf_Dynamics_N_SLA(day, kiosk, parvalues)
        self.n_crop_dynamics = _w81.N_crop(day, kiosk, parvalues)
        self.n_stress = _w81.N_Stress(day, kiosk, parvalues)
        TAGP = self.kiosk.TWLV + self.kiosk.TWST + self.kiosk.TWSO
        self.states = self.StateVariables(kiosk, publish=["TAGP", "GASST", "MREST", "HI"],
                                          TAGP=TAGP, GASST=0.0, MREST=0.0, CEVST=0.0, CTRAT=0.0, HI=0.0,
                                          LV_REALLOCATED=0., ST_REALLOCATED=0., DOF=None, FINISH_TYPE=None)
        checksum = parvalues["TDWI"] - self.states.TAGP - self.kiosk["TWRT"]
        if abs(checksum) > 0.0001:
            raise _w81.exc.PartitioningError("Error in partitioning of initial biomass (TDWI)!")
        self._connect_signal(self._on_CROP_FINISH, signal=_w81.signals.crop_finish)


class Wofost81_NWLP_CWB_CNB_NLV(Engine):
    """WOFOST 8.1 terbatas N & air (neraca klasik) + efek N pada SLA dan partisi daun (tipe LINTUL3)."""
    config = str(CONF_PATH)
    __productionlevel__ = "NWLP"
    __cropmodel__ = "WOFOST"
    __cropmodelversion__ = "8.1"
    __waterbalance__ = "CWB"
    __nitrogenbalance__ = "CNB"
