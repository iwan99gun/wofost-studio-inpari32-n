"""Pembuatan penyedia data cuaca PCSE dari berbagai sumber."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import WeatherConfig

WEATHER_SOURCES = {
    "openmeteo": "Open-Meteo (daring, 1951-sekarang)",
    "nasapower": "NASA POWER (daring, 1984-sekarang)",
    "csv": "File CSV format PCSE",
    "excel": "File Excel format PCSE",
    "cabo": "Folder file CABO (stasiun.tahun)",
}


def _openmeteo_clip_rain():
    """Subkelas OpenMeteo yang memangkas hujan harian ke batas validasi PCSE (25 cm/hari).
    Hujan ekstrem tropis (>250 mm/hari) kadang muncul di arsip Open-Meteo dan membuat
    WeatherDataContainer menolak seluruh unduhan; untuk sawah beririgasi pengaruh
    pemangkasan pada neraca air praktis nol (limpasan)."""
    import logging
    from pcse import input as pin
    from pcse.base import WeatherDataContainer

    class OpenMeteoClipRain(pin.OpenMeteoWeatherDataProvider):
        def _make_WeatherDataContainers(self, recs):
            for rec in recs:
                if rec.get("RAIN") is not None and rec["RAIN"] > 25.0:
                    logging.getLogger(__name__).warning(
                        "RAIN %.1f cm pada %s dipangkas ke 25 cm (batas PCSE)", rec["RAIN"], rec.get("DAY"))
                    rec["RAIN"] = 25.0
                wdc = WeatherDataContainer(**rec)
                self._store_WeatherDataContainer(wdc, wdc.DAY)

    return OpenMeteoClipRain


def build_weather_provider(cfg: WeatherConfig, force_update: bool = False):
    """Kembalikan objek WeatherDataProvider PCSE sesuai konfigurasi."""
    from pcse import input as pin

    if cfg.source in ("openmeteo", "nasapower"):
        import time
        last = None
        for attempt in range(4):   # layanan daring kadang time-out; coba ulang dengan jeda
            try:
                if cfg.source == "openmeteo":
                    return _openmeteo_clip_rain()(
                        latitude=float(cfg.latitude), longitude=float(cfg.longitude),
                        timezone=cfg.timezone or "UTC", ETmodel=cfg.et_model, force_update=force_update)
                return pin.NASAPowerWeatherDataProvider(
                    latitude=float(cfg.latitude), longitude=float(cfg.longitude),
                    ETmodel=cfg.et_model, force_update=force_update)
            except Exception as e:  # noqa: BLE001
                last = e
                time.sleep(3 * (attempt + 1))
        raise RuntimeError(f"Gagal mengunduh cuaca {cfg.describe()} setelah 4 percobaan: {type(last).__name__}: {last}")
    if cfg.source == "csv":
        if not Path(cfg.path).is_file():
            raise FileNotFoundError(f"File CSV cuaca tidak ditemukan: {cfg.path}")
        return pin.CSVWeatherDataProvider(cfg.path, ETmodel=cfg.et_model, force_reload=force_update)
    if cfg.source == "excel":
        if not Path(cfg.path).is_file():
            raise FileNotFoundError(f"File Excel cuaca tidak ditemukan: {cfg.path}")
        return pin.ExcelWeatherDataProvider(cfg.path, force_reload=force_update)
    if cfg.source == "cabo":
        if not Path(cfg.path).is_dir():
            raise FileNotFoundError(f"Folder CABO tidak ditemukan: {cfg.path}")
        if not cfg.station:
            raise ValueError("Nama stasiun CABO harus diisi (mis. NL1).")
        return pin.CABOWeatherDataProvider(cfg.station, fpath=cfg.path, ETmodel=cfg.et_model)
    raise ValueError(f"Sumber cuaca tidak dikenal: {cfg.source}")


def weather_summary(wdp) -> dict:
    return {
        "Lintang": round(float(wdp.latitude), 4),
        "Bujur": round(float(wdp.longitude), 4),
        "Elevasi [m]": float(wdp.elevation) if wdp.elevation is not None else None,
        "Tanggal awal": wdp.first_date,
        "Tanggal akhir": wdp.last_date,
        "Hari hilang": int(wdp.missing),
        "Deskripsi": str(getattr(wdp, "description", "") or ""),
    }


def weather_to_dataframe(wdp) -> pd.DataFrame:
    """Ekspor semua rekaman cuaca harian ke DataFrame (indeks tanggal)."""
    recs = wdp.export()
    df = pd.DataFrame(recs)
    if "DAY" in df.columns:
        df["DAY"] = pd.to_datetime(df["DAY"])
        df = df.sort_values("DAY").set_index("DAY")
    return df


def export_weather_csv_pcse(wdp, path: str | Path) -> None:
    """Simpan data cuaca ke CSV berformat PCSE agar dapat dimuat ulang tanpa internet."""
    df = weather_to_dataframe(wdp)
    cols = ["IRRAD", "TMIN", "TMAX", "VAP", "WIND", "RAIN", "SNOWDEPTH"]
    for c in cols:
        if c not in df.columns:
            df[c] = float("nan")
    out = df[cols].copy()
    # Internal PCSE: IRRAD J/m2/hari, VAP hPa, RAIN cm. CSV PCSE: kJ/m2/hari, kPa, mm.
    out["IRRAD"] = out["IRRAD"] / 1000.0
    out["VAP"] = out["VAP"] / 10.0
    out["RAIN"] = out["RAIN"] * 10.0
    out.insert(0, "DAY", [d.strftime("%Y%m%d") for d in out.index])
    header = (
        "## Site Characteristics\n"
        "Country     = 'Unknown'\n"
        "Station     = 'Export WOFOST Studio'\n"
        "Description = 'Diekspor dari WOFOST Studio'\n"
        "Source      = 'PCSE weather provider'\n"
        "Contact     = 'none'\n"
        f"Longitude = {float(wdp.longitude)}; Latitude = {float(wdp.latitude)}; "
        f"Elevation = {float(wdp.elevation or 0.0)}; AngstromA = 0.25; AngstromB = 0.45; HasSunshine = False\n"
        "## Daily weather observations (missing values are NaN)\n"
    )
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(header)
        out.to_csv(f, index=False, na_rep="NaN", lineterminator="\n")


def available_years(wdp) -> list[int]:
    return list(range(wdp.first_date.year, wdp.last_date.year + 1))
