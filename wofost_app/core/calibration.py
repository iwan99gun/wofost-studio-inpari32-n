"""Kalibrasi parameter tanaman terhadap data observasi (scipy.optimize)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd

from .simulation import SimulationRunner, SimulationResult


def load_observations(path: str) -> pd.DataFrame:
    """Baca CSV/Excel observasi.

    Format lebar : kolom `day` + satu kolom per variabel (LAI, TWSO, TAGP, SM, ...)
    Format panjang: kolom `day`, `variable`, `value`
    Hasil: DataFrame lebar, indeks tanggal (datetime), kolom = variabel.
    """
    path = str(path)
    if path.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)
    cols = {c.lower(): c for c in df.columns}
    if "day" not in cols:
        raise ValueError("Kolom 'day' (tanggal) tidak ditemukan pada file observasi.")
    df = df.rename(columns={cols["day"]: "day"})
    df["day"] = pd.to_datetime(df["day"])
    if "variable" in cols and "value" in cols:
        df = df.rename(columns={cols["variable"]: "variable", cols["value"]: "value"})
        df = df.pivot_table(index="day", columns="variable", values="value", aggfunc="mean")
    else:
        df = df.set_index("day")
    df = df.apply(pd.to_numeric, errors="coerce").sort_index()
    df = df.dropna(axis=1, how="all")
    return df


@dataclass
class CalibrationResult:
    params: dict[str, float]
    initial: dict[str, float]
    objective: float
    n_evals: int
    metrics: pd.DataFrame            # per variabel: n, RMSE, nRMSE, bias, R2
    simulated: SimulationResult
    observed: pd.DataFrame
    history: list[float] = field(default_factory=list)
    message: str = ""


TERMINAL_VARS = {"TWSO", "TAGP", "TWLV", "TWST", "TWRT", "DVS"}


def _match(sim: pd.DataFrame, obs: pd.DataFrame, variables: list[str]) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    out = {}
    for v in variables:
        if v not in sim.columns or v not in obs.columns:
            continue
        o = obs[v].dropna()
        s = sim[v].reindex(o.index)  # cocokkan tanggal persis
        # observasi setelah simulasi berakhir (masak lebih awal dari tanggal sampel): pakai nilai terminal
        # untuk variabel kumulatif (TWSO, TAGP, TWLV, TWST, DVS) selama selisih <= 45 hari
        if v in TERMINAL_VARS and len(sim.index):
            last_day = sim.index.max()
            late = [d for d in o.index if d > last_day and (d - last_day).days <= 45]
            for d in late:
                s.loc[d] = float(sim[v].iloc[-1])
        mask = s.notna().values
        if mask.sum() == 0:
            continue
        out[v] = (o.values[mask].astype(float), s.values[mask].astype(float))
    return out


def compute_metrics(sim: pd.DataFrame, obs: pd.DataFrame, variables: list[str]) -> pd.DataFrame:
    rows = []
    for v, (o, s) in _match(sim, obs, variables).items():
        err = s - o
        rmse = float(np.sqrt(np.mean(err ** 2)))
        mean_o = float(np.mean(o))
        ss_res = float(np.sum(err ** 2))
        ss_tot = float(np.sum((o - o.mean()) ** 2))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
        rows.append({"variabel": v, "n": len(o), "RMSE": rmse,
                     "nRMSE_%": 100 * rmse / mean_o if mean_o else np.nan,
                     "bias": float(np.mean(err)), "R2": r2})
    return pd.DataFrame(rows).set_index("variabel") if rows else pd.DataFrame()


def calibrate(runner: SimulationRunner, obs: pd.DataFrame, variables: list[str],
              names: list[str], x0: list[float], bounds: list[tuple[float, float]],
              method: str = "least_squares", max_evals: int = 200,
              progress: Callable | None = None, cancelled: Callable | None = None) -> CalibrationResult:
    """Kalibrasi `names` supaya simulasi mendekati observasi pada `variables`.

    Residual dinormalisasi dengan simpangan baku observasi per variabel agar
    variabel dengan satuan berbeda (LAI vs kg/ha) berbobot setara.
    """
    from scipy import optimize

    obs = obs.copy()
    scales: dict[str, float] = {}
    for v in variables:
        if v in obs.columns:
            series = obs[v].dropna()
            sd = float(series.std()) if len(series) > 1 else 0.0
            scales[v] = sd if np.isfinite(sd) and sd > 0 else max(abs(float(series.mean())), 1.0)
    variables = [v for v in variables if v in scales]
    if not variables:
        raise ValueError("Tidak ada variabel observasi yang cocok dengan keluaran model.")
    n_obs_total = sum(len(obs[v].dropna()) for v in variables)

    history: list[float] = []
    n_evals = 0
    lo = np.array([b[0] for b in bounds], float)
    hi = np.array([b[1] for b in bounds], float)

    def residuals(x: np.ndarray) -> np.ndarray:
        nonlocal n_evals
        if cancelled and cancelled():
            raise InterruptedError("Dibatalkan oleh pengguna.")
        x = np.clip(x, lo, hi)
        overrides = {n: float(v) for n, v in zip(names, x)}
        try:
            res = runner.run(overrides)
        except Exception:  # noqa: BLE001
            return np.full(n_obs_total, 1e3)
        parts = []
        for v, (o, s) in _match(res.daily, obs, variables).items():
            parts.append((s - o) / scales[v])
        r = np.concatenate(parts) if parts else np.full(n_obs_total, 1e3)
        if len(r) != n_obs_total:  # jaga panjang residual tetap konstan untuk least_squares
            r = np.resize(r, n_obs_total)
        n_evals += 1
        obj = float(np.sum(r ** 2))
        history.append(obj)
        if progress:
            progress(min(n_evals, max_evals), max_evals, f"Evaluasi {n_evals}: SSE ternormalisasi = {obj:.4g}")
        return r

    x0a = np.clip(np.array(x0, float), lo, hi)
    if method == "least_squares":
        sol = optimize.least_squares(residuals, x0a, bounds=(lo, hi), max_nfev=max_evals, diff_step=0.02)
        x_best, msg = sol.x, sol.message
    else:  # Nelder-Mead
        sol = optimize.minimize(lambda x: float(np.sum(residuals(x) ** 2)), x0a, method="Nelder-Mead",
                                bounds=list(zip(lo, hi)),
                                options={"maxfev": max_evals, "xatol": 1e-3, "fatol": 1e-4})
        x_best, msg = sol.x, str(sol.message)
    x_best = np.clip(x_best, lo, hi)
    best = {n: float(v) for n, v in zip(names, x_best)}
    final = runner.run(best)
    metrics = compute_metrics(final.daily, obs, variables)
    obj = float(np.sum(residuals(x_best) ** 2))
    return CalibrationResult(params=best, initial={n: float(v) for n, v in zip(names, x0)}, objective=obj,
                             n_evals=n_evals, metrics=metrics, simulated=final, observed=obs,
                             history=history, message=msg)
