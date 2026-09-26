"""Skenario iklim: perturbasi cuaca (gelombang panas, hujan, radiasi, CO2) dan analisis kerentanan hasil.

Catatan ilmiah: WOFOST 7.2/7.3 merespons suhu lewat fenologi (TSUM), fotosintesis maksimum (AMAXTB/TMPFTB),
respirasi (Q10) dan evapotranspirasi; belum ada modul sterilitas bunga akibat panas ekstrem. Interpretasikan
hasil skenario heatwave sebagai batas bawah dampak (lihat Zheng et al. 2025, WOFOST-EW).
"""
from __future__ import annotations

import copy
import datetime as dt
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd

from .config import SimulationConfig
from .simulation import SimulationResult, SimulationRunner


@dataclass
class ClimateScenario:
    name: str
    start: dt.date | None = None        # None = seluruh musim
    end: dt.date | None = None
    d_tmax: float = 0.0                 # perubahan TMAX [C]
    d_tmin: float = 0.0                 # perubahan TMIN [C]
    rain_factor: float = 1.0            # pengali hujan
    irrad_factor: float = 1.0           # pengali radiasi
    co2: float | None = None            # ppm, hanya WOFOST 7.3

    def is_baseline(self) -> bool:
        return (self.d_tmax == 0 and self.d_tmin == 0 and self.rain_factor == 1 and self.irrad_factor == 1
                and self.co2 is None)

    def in_window(self, day: dt.date) -> bool:
        if self.start and day < self.start:
            return False
        if self.end and day > self.end:
            return False
        return True


class PerturbedWeatherDataProvider:
    """Pembungkus WeatherDataProvider PCSE yang memodifikasi rekaman harian di jendela skenario."""

    def __init__(self, base, scenario: ClimateScenario):
        from pcse.base import WeatherDataContainer, WeatherDataProvider
        from pcse.util import reference_ET

        class _Provider(WeatherDataProvider):
            pass

        self._p = _Provider()
        p = self._p
        for attr in ("latitude", "longitude", "elevation", "angstA", "angstB", "ETmodel", "description"):
            if hasattr(base, attr):
                setattr(p, attr, getattr(base, attr))
        angsta = float(getattr(base, "angstA", -0.18) or -0.18)
        angstb = float(getattr(base, "angstB", -0.55) or -0.55)
        etmodel = getattr(base, "ETmodel", "PM") or "PM"
        for rec in base.export():
            rec = dict(rec)
            day = rec["DAY"]
            if scenario.in_window(day) and not scenario.is_baseline():
                rec["TMAX"] = rec["TMAX"] + scenario.d_tmax
                rec["TMIN"] = min(rec["TMIN"] + scenario.d_tmin, rec["TMAX"])
                rec["RAIN"] = rec["RAIN"] * scenario.rain_factor
                rec["IRRAD"] = rec["IRRAD"] * scenario.irrad_factor
                if "TEMP" in rec:
                    rec["TEMP"] = (rec["TMIN"] + rec["TMAX"]) / 2.0
                try:
                    e0, es0, et0 = reference_ET(day, p.latitude, p.elevation, rec["TMIN"], rec["TMAX"], rec["IRRAD"],
                                                rec["VAP"], rec["WIND"], angsta, angstb, ETMODEL=etmodel)
                    rec["E0"], rec["ES0"], rec["ET0"] = e0 / 10.0, es0 / 10.0, et0 / 10.0
                except Exception:  # noqa: BLE001
                    pass
            wdc = WeatherDataContainer(**rec)
            p._store_WeatherDataContainer(wdc, day)

    @property
    def provider(self):
        return self._p


def heat_sterility_factor(wdp, anthesis: dt.date, days_before: int = 5, days_after: int = 5,
                          a: float = 0.853, t50: float = 36.6) -> tuple[float, float]:
    """Fraksi spikelet steril empiris tipe Horie (Horie 1993; Yoshida & Horie 2009), dipakai di ORYZA v3,
    APSIM-Oryza, SIMRIW: seed-setting rate SR = 1/(1+exp(a*(Tm,a - T50))), sterilitas = 1 - SR, dengan Tm,a =
    rata-rata Tmax harian pada jendela pembungaan, a = 0.853, T50 = 36.6 C (T50 bervariasi 34.9-43.2 C antar
    varietas; Sun et al. 2025, Eur. J. Agron.). Mengembalikan (sterilitas, Tm,a). Tidak ada di WOFOST; pasca-proses."""
    temps = []
    d = anthesis - dt.timedelta(days=days_before)
    while d <= anthesis + dt.timedelta(days=days_after):
        try:
            temps.append(float(wdp(d).TMAX))
        except Exception:  # noqa: BLE001
            pass
        d += dt.timedelta(days=1)
    if not temps:
        return 0.0, float("nan")
    tm = float(np.mean(temps))
    ster = 1.0 / (1.0 + np.exp(-a * (tm - t50)))
    return float(ster), tm


@dataclass
class ScenarioRun:
    scenario: ClimateScenario
    result: SimulationResult | None
    error: str = ""


@dataclass
class ScenarioSet:
    baseline: SimulationResult
    runs: list[ScenarioRun]
    table: pd.DataFrame
    weather: dict[str, pd.DataFrame] = field(default_factory=dict)   # nama -> TMAX/TMIN/RAIN harian


def _weather_frame(wdp, start: dt.date, end: dt.date) -> pd.DataFrame:
    rows = []
    d = start
    while d <= end:
        try:
            r = wdp(d)
            rows.append({"day": pd.Timestamp(d), "TMAX": r.TMAX, "TMIN": r.TMIN, "RAIN": r.RAIN * 10, "IRRAD": r.IRRAD / 1e6})
        except Exception:  # noqa: BLE001
            pass
        d += dt.timedelta(days=1)
    return pd.DataFrame(rows).set_index("day") if rows else pd.DataFrame()


def run_scenarios(cfg: SimulationConfig, wdp, scenarios: list[ClimateScenario],
                  progress: Callable | None = None, cancelled: Callable | None = None,
                  sterility: dict | None = None) -> ScenarioSet:
    """sterility: None atau dict(days_before, days_after, a, t50) untuk pasca-proses sterilitas panas."""
    base_runner = SimulationRunner(cfg, wdp)
    baseline = base_runner.run()

    def _ster(w, summ):
        if not sterility or not summ.get("DOA"):
            return {}
        s, tm = heat_sterility_factor(w, summ["DOA"], **sterility)
        return {"Tmax_bunga": tm, "sterilitas_%": 100 * s, "TWSO_sterilitas": summ.get("TWSO", np.nan) * (1 - s)}
    n = len(scenarios)
    runs: list[ScenarioRun] = []
    weather: dict[str, pd.DataFrame] = {"Baseline": _weather_frame(wdp, cfg.crop_start_date, cfg.crop_end_date)}
    base_ster = _ster(wdp, baseline.summary)
    rows = [{"skenario": "Baseline", **_summary_row(baseline.summary), "dTWSO_%": 0.0, "dTAGP_%": 0.0,
             "d_tmax": 0.0, "d_tmin": 0.0, "rain_factor": 1.0, "irrad_factor": 1.0, "co2": cfg.site.get("CO2"),
             "jendela": f"{cfg.crop_start_date}..{cfg.crop_end_date}", **base_ster, "status": "OK"}]
    for i, sc in enumerate(scenarios, 1):
        if cancelled and cancelled():
            raise InterruptedError("Dibatalkan oleh pengguna.")
        if progress:
            progress(i, n, f"Skenario {sc.name}")
        try:
            pw = PerturbedWeatherDataProvider(wdp, sc).provider
            cfg2 = copy.deepcopy(cfg)
            if sc.co2 is not None:
                cfg2.site["CO2"] = float(sc.co2)
            res = SimulationRunner(cfg2, pw).run()
            runs.append(ScenarioRun(sc, res))
            weather[sc.name] = _weather_frame(pw, cfg.crop_start_date, cfg.crop_end_date)
            s = res.summary
            st = _ster(pw, s)
            if st and base_ster:
                st["dTWSO_sterilitas_%"] = 100 * (st["TWSO_sterilitas"] - base_ster["TWSO_sterilitas"]) / base_ster["TWSO_sterilitas"]
            rows.append({"skenario": sc.name, **_summary_row(s),
                         "dTWSO_%": 100 * (s.get("TWSO", 0) - baseline.summary["TWSO"]) / baseline.summary["TWSO"],
                         "dTAGP_%": 100 * (s.get("TAGP", 0) - baseline.summary["TAGP"]) / baseline.summary["TAGP"],
                         "d_tmax": sc.d_tmax, "d_tmin": sc.d_tmin, "rain_factor": sc.rain_factor,
                         "irrad_factor": sc.irrad_factor, "co2": sc.co2,
                         "jendela": f"{sc.start or cfg.crop_start_date}..{sc.end or cfg.crop_end_date}", **st, "status": "OK"})
        except Exception as e:  # noqa: BLE001
            runs.append(ScenarioRun(sc, None, f"{type(e).__name__}: {e}"))
            rows.append({"skenario": sc.name, "status": f"GAGAL: {type(e).__name__}: {e}"[:200]})
    return ScenarioSet(baseline=baseline, runs=runs, table=pd.DataFrame(rows), weather=weather)


def _summary_row(s: dict) -> dict:
    return {k: s.get(k) for k in ("TWSO", "TAGP", "LAIMAX", "CTRAT", "DOA", "DOM", "DURASI_HARI")}


def heatwave_sweep(cfg: SimulationConfig, wdp, d_values: list[float], window_days_before: int = 7,
                   window_days_after: int = 7, relative_to: str = "DOA", d_tmin_ratio: float = 0.5,
                   fixed_start: dt.date | None = None, fixed_end: dt.date | None = None) -> list[ClimateScenario]:
    """Buat daftar skenario heatwave: +dT pada jendela di sekitar antesis (DOA) / masak (DOM) / tanggal tetap."""
    if fixed_start and fixed_end:
        start, end = fixed_start, fixed_end
    else:
        base = SimulationRunner(cfg, wdp).run()
        anchor = base.summary.get(relative_to) or base.summary.get("DOA")
        if anchor is None:
            raise ValueError("Tanggal antesis/masak baseline tidak tersedia untuk menentukan jendela heatwave.")
        start = anchor - dt.timedelta(days=window_days_before)
        end = anchor + dt.timedelta(days=window_days_after)
    return [ClimateScenario(name=f"sweep +{d:g}C", start=start, end=end, d_tmax=float(d), d_tmin=float(d) * d_tmin_ratio)
            for d in d_values]
