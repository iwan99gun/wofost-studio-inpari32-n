"""Asimilasi data dengan Ensemble Kalman Filter (EnKF) ke dalam PCSE-WOFOST.

Ansambel dibentuk dari perturbasi parameter tanaman (mis. TSUM1, SPAN, TDWI). Pada setiap tanggal
observasi, variabel state (LAI atau SM) setiap anggota diperbarui dengan analisis Kalman dan
dimasukkan kembali ke model lewat `set_variable`, lalu simulasi dilanjutkan (Evensen 2003; skema
observasi terperturbasi Burgers et al. 1998).
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd

from .simulation import SimulationResult, SimulationRunner

ASSIMILABLE = {"LAI": "Indeks luas daun (set_variable LAI)", "SM": "Kadar air zona akar (set_variable SM)"}


@dataclass
class EnKFResult:
    assim_var: str
    obs: pd.DataFrame
    members: pd.DataFrame            # perturbasi parameter per anggota
    daily_assim: dict[str, pd.DataFrame]     # var -> (day x member)
    daily_open: dict[str, pd.DataFrame]
    summary_assim: pd.DataFrame      # per anggota
    summary_open: pd.DataFrame
    updates: pd.DataFrame            # per tanggal observasi
    baseline: SimulationResult       # run deterministik tanpa perturbasi
    n_runs: int = 0
    message: str = ""

    def band(self, var: str, assim: bool = True) -> pd.DataFrame:
        d = (self.daily_assim if assim else self.daily_open).get(var)
        if d is None:
            return pd.DataFrame()
        return pd.DataFrame({"q05": d.quantile(0.05, axis=1), "mean": d.mean(axis=1),
                             "q95": d.quantile(0.95, axis=1)})


def _perturbed_params(rng: np.random.Generator, base: dict[str, float], perturb: dict[str, float],
                      n: int) -> list[dict[str, float]]:
    """perturb: nama -> simpangan baku relatif (0.1 = 10 %). Distribusi lognormal agar tetap positif."""
    out = []
    for _ in range(n):
        d = {}
        for name, rel in perturb.items():
            mu = float(base[name])
            if name.endswith("@x"):                      # geseran suhu: normal aditif, SD dalam C
                d[name] = float(mu + rng.normal(0.0, rel * 10.0))   # "SD %" x 10 = SD [C] (mis. 10 % -> 1 C)
                continue
            if rel <= 0 or mu == 0:
                d[name] = mu
                continue
            s = np.sqrt(np.log(1 + rel ** 2))
            d[name] = float(mu * np.exp(rng.normal(-0.5 * s * s, s)))
        out.append(d)
    return out


def _to_space(pert: list[dict]) -> tuple[list[str], np.ndarray]:
    """Parameter -> ruang transformasi (log untuk parameter positif, linear untuk @x)."""
    names = list(pert[0].keys())
    Z = np.array([[np.log(p[n]) if (not n.endswith("@x") and p[n] > 0) else p[n] for n in names] for p in pert], float)
    return names, Z


def _from_space(names: list[str], Z: np.ndarray) -> list[dict]:
    return [{n: (float(np.exp(z)) if not n.endswith("@x") else float(z)) for n, z in zip(names, row)} for row in Z]


def ensemble_smoother_update(pert: list[dict], Hx: np.ndarray, y: np.ndarray, r_sd: np.ndarray,
                             rng: np.random.Generator, n_iter: int = 1, it: int = 0) -> list[dict]:
    """Satu langkah ES-MDA (Emerick & Reynolds 2013) pada parameter ansambel.
    Hx: (N x nobs) prediksi observasi tiap anggota; y: observasi; r_sd: SD observasi; R diinflasi n_iter kali."""
    names, Z = _to_space(pert)
    N = Z.shape[0]
    alpha = float(n_iter)
    R = np.diag((r_sd ** 2) * alpha)
    Zm = Z - Z.mean(axis=0)
    Hm = Hx - Hx.mean(axis=0)
    Czy = Zm.T @ Hm / (N - 1)                 # p x nobs
    Cyy = Hm.T @ Hm / (N - 1)                 # nobs x nobs
    K = Czy @ np.linalg.pinv(Cyy + R)
    Yp = y[None, :] + rng.normal(0.0, 1.0, size=Hx.shape) * (r_sd * np.sqrt(alpha))[None, :]
    Za = Z + (Yp - Hx) @ K.T
    return _from_space(names, Za)


def _collect(models, assim_var: str) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    per_var: dict[str, list[pd.Series]] = {}
    summaries = []
    for i, m in enumerate(models):
        df = pd.DataFrame(m.get_output())
        if df.empty:
            continue
        df["day"] = pd.to_datetime(df["day"])
        df = df.set_index("day")
        for c in df.columns:
            per_var.setdefault(c, []).append(df[c].rename(i))
        s = m.get_summary_output()
        summaries.append(dict(s[0]) if s else {})
    daily = {v: pd.concat(cols, axis=1) for v, cols in per_var.items()}
    summ = pd.DataFrame(summaries)
    summ.index.name = "anggota"
    return daily, summ


def run_enkf(runner: SimulationRunner, obs: pd.DataFrame, assim_var: str = "LAI",
             perturb: dict[str, float] | None = None, n_members: int = 30, obs_rel_error: float = 0.10,
             obs_abs_floor: float = 0.0, inflation: float = 1.0,
             progress: Callable | None = None, cancelled: Callable | None = None,
             seed: int = 42, update_params: bool = False, n_smoother_iter: int = 2) -> EnKFResult:
    """update_params=True: langkah 1 perbarui parameter ansambel dengan ES-MDA memakai semua observasi
    (inferensi gabungan parameter + state, cf. Song et al. 2024), langkah 2 EnKF pada state."""
    if assim_var not in ASSIMILABLE:
        raise ValueError(f"Variabel {assim_var} tidak dapat diasimilasi (pilih {list(ASSIMILABLE)}).")
    if assim_var not in obs.columns:
        raise ValueError(f"Kolom {assim_var} tidak ada pada observasi.")
    perturb = perturb or {"TDWI": 0.20, "SPAN": 0.10, "TSUM1": 0.05}
    rng = np.random.default_rng(seed)
    cfg = runner.cfg
    base_vals = {k: runner.base_value(k) for k in perturb}
    pert = _perturbed_params(rng, base_vals, perturb, n_members)
    members = pd.DataFrame(pert)
    members.index.name = "anggota"

    obs_series = obs[assim_var].dropna()
    obs_series = obs_series[(obs_series.index.date >= cfg.crop_start_date) & (obs_series.index.date <= cfg.crop_end_date)]
    obs_dates = [d.date() for d in obs_series.index]
    if not obs_dates:
        raise ValueError("Tidak ada observasi di dalam periode simulasi.")

    agro = cfg.to_agromanagement()
    total = (2 + (n_smoother_iter if update_params else 0)) * n_members
    done = 0
    prior_members = members.copy()

    def tick(msg):
        nonlocal done
        done += 1
        if progress:
            progress(done, total, msg)

    # --- ansambel open-loop (tanpa asimilasi) --------------------------------------------
    open_models = []
    for i, p in enumerate(pert):
        if cancelled and cancelled():
            raise InterruptedError("Dibatalkan oleh pengguna.")
        m = runner.model_cls(runner.build_params(p), runner.wdp, agro)
        m.run_till_terminate()
        open_models.append(m)
        tick(f"Open-loop anggota {i + 1}/{n_members}")
    daily_open, summ_open = _collect(open_models, assim_var)

    # --- langkah 1 (opsional): pembaruan parameter dengan ensemble smoother (ES-MDA) ------------------
    smoother_log = []
    if update_params:
        y_all = obs_series.values.astype(float)
        r_all = np.maximum(obs_rel_error * np.abs(y_all), max(obs_abs_floor, 1e-6))
        cur = list(pert)
        cur_daily = daily_open
        for it in range(int(n_smoother_iter)):
            if cancelled and cancelled():
                raise InterruptedError("Dibatalkan oleh pengguna.")
            dv = cur_daily.get(assim_var)
            ts = [pd.Timestamp(d) for d in obs_dates]
            ok_idx = [i for i, t in enumerate(ts) if dv is not None and t in dv.index]
            if len(ok_idx) < 1:
                break
            Hx = dv.loc[[ts[i] for i in ok_idx]].values.T          # N x nobs
            Hx = np.nan_to_num(Hx, nan=0.0)
            cur = ensemble_smoother_update(cur, Hx, y_all[ok_idx], r_all[ok_idx], rng, n_smoother_iter, it)
            # jalankan ulang ansambel dengan parameter baru untuk iterasi berikutnya / EnKF
            new_models = []
            for i, p in enumerate(cur):
                if cancelled and cancelled():
                    raise InterruptedError("Dibatalkan oleh pengguna.")
                m = runner.model_cls(runner.build_params(p), runner.wdp, agro)
                m.run_till_terminate()
                new_models.append(m)
                tick(f"ES-MDA iterasi {it + 1}/{n_smoother_iter}, anggota {i + 1}/{n_members}")
            cur_daily, _ = _collect(new_models, assim_var)
            rmse = float(np.sqrt(np.mean((cur_daily[assim_var].loc[[ts[i] for i in ok_idx]].mean(axis=1).values - y_all[ok_idx]) ** 2)))
            smoother_log.append({"iterasi": it + 1, "RMSE_rata_ansambel": rmse})
        pert = cur
        members = pd.DataFrame(pert)
        members.index.name = "anggota"

    # --- ansambel dengan asimilasi ----------------------------------------------------------
    models = [runner.model_cls(runner.build_params(p), runner.wdp, agro) for p in pert]
    updates = []
    for d, y in zip(obs_dates, obs_series.values.astype(float)):
        if cancelled and cancelled():
            raise InterruptedError("Dibatalkan oleh pengguna.")
        for m in models:
            if not m.flag_terminate and m.day < d:
                m.run_till(d)
        xf = np.array([np.nan if m.flag_terminate else (m.get_variable(assim_var) or np.nan) for m in models], float)
        valid = np.isfinite(xf) & (xf > 1e-3)
        if valid.sum() < 2:
            updates.append({"tanggal": d, "observasi": y, "forecast_mean": np.nanmean(xf) if np.isfinite(xf).any() else np.nan,
                            "analysis_mean": np.nan, "K": np.nan, "n_valid": int(valid.sum()), "status": "dilewati"})
            continue
        r_sd = max(obs_rel_error * abs(y), obs_abs_floor, 1e-6)
        R = r_sd ** 2
        xv = xf[valid]
        xmean = xv.mean()
        P = float(np.var(xv, ddof=1)) * inflation
        K = P / (P + R)
        y_pert = y + rng.normal(0.0, r_sd, size=valid.sum())
        xa = xv + K * (y_pert - xv)
        xa = np.maximum(xa, 1e-3)
        for m, new in zip([mm for mm, ok in zip(models, valid) if ok], xa):
            m.set_variable(assim_var, float(new))
        innov = y - xmean
        updates.append({"tanggal": d, "observasi": y, "forecast_mean": xmean, "forecast_sd": float(np.sqrt(P / inflation)),
                        "analysis_mean": float(xa.mean()), "analysis_sd": float(xa.std(ddof=1)), "K": float(K),
                        "inovasi": float(innov), "inovasi_ternormalisasi": float(innov / np.sqrt(P + R)),
                        "n_valid": int(valid.sum()), "status": "OK"})
        if progress:
            progress(done, total, f"Asimilasi {assim_var} pada {d}: K = {K:.2f}")
    for i, m in enumerate(models):
        if cancelled and cancelled():
            raise InterruptedError("Dibatalkan oleh pengguna.")
        if not m.flag_terminate:
            m.run_till_terminate()
        tick(f"Selesai anggota {i + 1}/{n_members}")
    daily_assim, summ_assim = _collect(models, assim_var)
    baseline = runner.run()
    upd = pd.DataFrame(updates)
    n_ok = int((upd["status"] == "OK").sum()) if not upd.empty else 0
    msg = (f"{n_members} anggota, {n_ok}/{len(upd)} observasi diasimilasi. "
           f"TWSO open-loop {summ_open['TWSO'].mean():.0f} +/- {summ_open['TWSO'].std():.0f}; "
           f"dengan asimilasi {summ_assim['TWSO'].mean():.0f} +/- {summ_assim['TWSO'].std():.0f} kg/ha.")
    if n_ok:
        z = upd.loc[upd["status"] == "OK", "inovasi_ternormalisasi"]
        msg += (f" Inovasi ternormalisasi: rata-rata {z.mean():+.2f}, SD {z.std(ddof=0):.2f} "
                f"(ideal ~0 dan ~1; SD > 1 berarti kovarians forecast/observasi terlalu kecil, naikkan inflasi).")
    if update_params:
        stats = pd.DataFrame({"prior_mean": prior_members.mean(), "prior_sd": prior_members.std(),
                              "posterior_mean": members.mean(), "posterior_sd": members.std()})
        members = pd.concat([prior_members.add_prefix("prior_"), members.add_prefix("posterior_")], axis=1)
        msg += " Parameter diperbarui ES-MDA: " + "; ".join(
            f"{n} {stats.loc[n, 'prior_mean']:.4g}->{stats.loc[n, 'posterior_mean']:.4g}" for n in stats.index)
        if smoother_log:
            msg += " RMSE rata-rata ansambel per iterasi: " + ", ".join(f"{d['RMSE_rata_ansambel']:.3g}" for d in smoother_log)
    return EnKFResult(assim_var=assim_var, obs=obs, members=members, daily_assim=daily_assim, daily_open=daily_open,
                      summary_assim=summ_assim, summary_open=summ_open, updates=upd, baseline=baseline,
                      n_runs=total, message=msg)
