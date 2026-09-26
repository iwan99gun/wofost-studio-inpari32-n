"""Struktur konfigurasi simulasi (dapat disimpan/dimuat sebagai JSON)."""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Deskripsi parameter (dipakai untuk tooltip di UI)
# ---------------------------------------------------------------------------
SOIL_PARAM_INFO = {
    "SMW":    ("Kadar air titik layu permanen [cm3/cm3]", 0.0, 0.6),
    "SMFCF":  ("Kadar air kapasitas lapang [cm3/cm3]", 0.0, 0.7),
    "SM0":    ("Kadar air jenuh / porositas [cm3/cm3]", 0.0, 0.9),
    "CRAIRC": ("Kandungan udara kritis untuk aerasi akar [cm3/cm3]", 0.0, 0.3),
    "RDMSOL": ("Kedalaman perakaran maksimum yang diizinkan tanah [cm]", 10.0, 300.0),
    "K0":     ("Konduktivitas hidrolik jenuh [cm/hari]", 0.0, 500.0),
    "SOPE":   ("Laju perkolasi maksimum zona akar [cm/hari]", 0.0, 100.0),
    "KSUB":   ("Laju perkolasi maksimum sub-tanah [cm/hari]", 0.0, 100.0),
}

SITE_PARAM_INFO = {
    "WAV":    ("Jumlah air awal dalam profil tanah [cm]", 0.0, 100.0),
    "SMLIM":  ("Kadar air maksimum awal di zona akar [cm3/cm3]", 0.0, 1.0),
    "SSMAX":  ("Kedalaman maksimum genangan air di permukaan [cm]", 0.0, 100.0),
    "SSI":    ("Genangan permukaan awal [cm]", 0.0, 100.0),
    "NOTINF": ("Fraksi hujan yang tidak terinfiltrasi [0-1]", 0.0, 1.0),
    "IFUNRN": ("Fraksi non-infiltrasi tergantung besar hujan (0/1)", 0, 1),
    "CO2":    ("Konsentrasi CO2 atmosfer [ppm] (WOFOST 7.3+)", 200.0, 1000.0),
    # Hanya dipakai model WOFOST 8.1 terbatas N (neraca N klasik, pcse.soil.n_soil_dynamics)
    "NAVAILI":      ("N mineral tersedia di kolam tanah saat awal [kg N/ha] (WOFOST 8.1)", 0.0, 250.0),
    "NSOILBASE":    ("Cadangan N tanah yang termineralisasi selama musim [kg N/ha] (WOFOST 8.1)", 0.0, 100.0),
    "NSOILBASE_FR": ("Fraksi NSOILBASE yang tersedia per hari [1/hari] (WOFOST 8.1)", 0.0, 1.0),
    "BG_N_SUPPLY":  ("Pasokan N latar (deposisi, fiksasi bebas) [kg N/ha/hari] (WOFOST 8.1)", 0.0, 0.1),
}
N_SITE_PARAMS = ("NAVAILI", "NSOILBASE", "NSOILBASE_FR", "BG_N_SUPPLY")

SOIL_PRESETS: dict[str, dict[str, float]] = {
    "Lempung (default PCSE)": dict(SMW=0.10, SMFCF=0.30, SM0=0.40, CRAIRC=0.06, RDMSOL=120, K0=10.0, SOPE=10.0, KSUB=10.0),
    "Pasir":                  dict(SMW=0.04, SMFCF=0.14, SM0=0.38, CRAIRC=0.09, RDMSOL=100, K0=50.0, SOPE=25.0, KSUB=25.0),
    "Lempung berpasir":       dict(SMW=0.08, SMFCF=0.22, SM0=0.40, CRAIRC=0.07, RDMSOL=120, K0=25.0, SOPE=15.0, KSUB=15.0),
    "Lempung liat":           dict(SMW=0.18, SMFCF=0.36, SM0=0.46, CRAIRC=0.05, RDMSOL=120, K0=5.0, SOPE=6.0, KSUB=6.0),
    "Liat (sawah tropis)":    dict(SMW=0.22, SMFCF=0.42, SM0=0.52, CRAIRC=0.04, RDMSOL=100, K0=2.0, SOPE=3.0, KSUB=3.0),
}

CROP_START_TYPES = ["sowing", "emergence"]
CROP_END_TYPES = ["maturity", "harvest", "earliest"]


def _merge_same_day(items: list[tuple], amount_key: str, eff_key: str) -> list[dict]:
    """PCSE menolak >1 kejadian per hari dalam satu tabel: gabungkan (jumlah dijumlahkan, efisiensi rata-rata tertimbang)."""
    acc: dict = {}
    for day, amt, eff in items:
        a0, w0 = acc.get(day, (0.0, 0.0))
        acc[day] = (a0 + amt, w0 + amt * eff)
    return [{day: {amount_key: a, eff_key: (w / a if a > 0 else 0.0)}} for day, (a, w) in sorted(acc.items())]


@dataclass
class WeatherConfig:
    source: str = "openmeteo"          # openmeteo | nasapower | csv | excel | cabo
    latitude: float = -6.90
    longitude: float = 107.60
    path: str = ""                     # file CSV/Excel, atau folder CABO
    station: str = ""                  # nama stasiun CABO (mis. "NL1")
    et_model: str = "PM"               # PM | P
    timezone: str = "Asia/Jakarta"     # hanya Open-Meteo

    def describe(self) -> str:
        if self.source in ("openmeteo", "nasapower"):
            nm = "Open-Meteo" if self.source == "openmeteo" else "NASA POWER"
            return f"{nm} @ ({self.latitude:.3f}, {self.longitude:.3f})"
        if self.source == "cabo":
            return f"CABO {self.station} di {self.path}"
        return f"{self.source.upper()}: {self.path}"


@dataclass
class IrrigationEvent:
    day: dt.date
    amount_cm: float = 2.0
    efficiency: float = 0.7


@dataclass
class FertilizerEvent:
    """Pemupukan N (sinyal PCSE `apply_n`): N_amount [kg N/ha] x N_recovery = N yang masuk kolam tersedia."""
    day: dt.date
    n_kg_ha: float = 40.0
    recovery: float = 0.5


@dataclass
class SimulationConfig:
    model_name: str = "Wofost72_WLP_FD"
    crop_name: str = "rice"
    variety_name: str = "Rice_IR72"
    crop_start_date: dt.date = field(default_factory=lambda: dt.date(2022, 11, 15))
    crop_start_type: str = "emergence"
    crop_end_date: dt.date = field(default_factory=lambda: dt.date(2023, 4, 30))
    crop_end_type: str = "maturity"
    max_duration: int = 300
    soil: dict[str, float] = field(default_factory=lambda: dict(SOIL_PRESETS["Lempung (default PCSE)"]))
    site: dict[str, float] = field(default_factory=lambda: dict(WAV=10.0, SMLIM=0.4, SSMAX=0.0, SSI=0.0, NOTINF=0.0, IFUNRN=0, CO2=400.0,
                                                                 NAVAILI=20.0, NSOILBASE=30.0, NSOILBASE_FR=0.025, BG_N_SUPPLY=0.0))
    crop_overrides: dict[str, float] = field(default_factory=dict)
    irrigation: list[IrrigationEvent] = field(default_factory=list)
    fertilization: list[FertilizerEvent] = field(default_factory=list)   # hanya berpengaruh pada model terbatas N
    weather: WeatherConfig = field(default_factory=WeatherConfig)
    # Syok tanam pindah (emulasi ORYZA2000, Bouman et al. 2001): pertumbuhan daun ditahan selama SHCKL x TSTR dan
    # perkembangan ditunda SHCKD x TSTR, dengan TSTR = jumlah suhu efektif di persemaian (umur bibit, Tbase 8, Topt 30).
    transplant_shock: bool = False
    seedling_age_days: int = 21
    shckl: float = 0.25
    shckd: float = 0.40

    # ---- agromanagement --------------------------------------------------
    def to_agromanagement(self, crop_start_date: dt.date | None = None,
                          crop_end_date: dt.date | None = None) -> list:
        """Bangun struktur agromanagement PCSE (list of dict)."""
        start = crop_start_date or self.crop_start_date
        end = crop_end_date or self.crop_end_date
        if end <= start:
            end = start + dt.timedelta(days=self.max_duration)
        campaign_start = start
        timed = []
        events = [ev for ev in self.irrigation if start <= ev.day <= end]
        if events:
            timed.append({
                "event_signal": "irrigate",
                "name": "Irrigation",
                "comment": "Irigasi terjadwal",
                "events_table": _merge_same_day([(ev.day, float(ev.amount_cm), float(ev.efficiency)) for ev in events],
                                                "amount", "efficiency"),
            })
        fert = [ev for ev in self.fertilization if start <= ev.day <= end and ev.n_kg_ha > 0]
        if fert and self.model_name.startswith("Wofost81") and "NWLP" in self.model_name:
            timed.append({
                "event_signal": "apply_n",
                "name": "N fertilization",
                "comment": "Pemupukan N terjadwal [kg N/ha]",
                "events_table": _merge_same_day([(ev.day, float(ev.n_kg_ha), float(ev.recovery)) for ev in fert],
                                                "N_amount", "N_recovery"),
            })
        timed = timed or None
        return [{
            campaign_start: {
                "CropCalendar": {
                    "crop_name": self.crop_name,
                    "variety_name": self.variety_name,
                    "crop_start_date": start,
                    "crop_start_type": self.crop_start_type,
                    "crop_end_date": end,
                    "crop_end_type": self.crop_end_type,
                    "max_duration": int(self.max_duration),
                },
                "TimedEvents": timed,
                "StateEvents": None,
            }
        }]

    # ---- (de)serialisasi ------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["crop_start_date"] = self.crop_start_date.isoformat()
        d["crop_end_date"] = self.crop_end_date.isoformat()
        d["irrigation"] = [dict(day=ev.day.isoformat(), amount_cm=ev.amount_cm, efficiency=ev.efficiency)
                           for ev in self.irrigation]
        d["fertilization"] = [dict(day=ev.day.isoformat(), n_kg_ha=ev.n_kg_ha, recovery=ev.recovery)
                              for ev in self.fertilization]
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SimulationConfig":
        d = dict(d)
        d["crop_start_date"] = dt.date.fromisoformat(d["crop_start_date"])
        d["crop_end_date"] = dt.date.fromisoformat(d["crop_end_date"])
        d["irrigation"] = [IrrigationEvent(dt.date.fromisoformat(e["day"]), float(e["amount_cm"]), float(e["efficiency"]))
                           for e in d.get("irrigation", [])]
        d["fertilization"] = [FertilizerEvent(dt.date.fromisoformat(e["day"]), float(e["n_kg_ha"]), float(e.get("recovery", 0.5)))
                              for e in d.get("fertilization", [])]
        d["weather"] = WeatherConfig(**d.get("weather", {}))
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "SimulationConfig":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
