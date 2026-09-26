"""Kalibrasi Bayesian dengan MCMC (emcee, affine-invariant ensemble sampler).

Model kesalahan: observasi ~ N(simulasi, sigma_i^2) dengan sigma_i = max(rel_error*|o_i|, floor_v),
prior seragam di dalam batas parameter. Hasil: rantai posterior, MAP, median, interval kredibel 95 %,
dan pita prediktif posterior untuk variabel observasi.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd

from .calibration import _match, compute_metrics
from .simulation import SimulationResult, SimulationRunner


@dataclass
class MCMCResult:
    names: list[str]
    chain: np.ndarray                 # (n_steps, n_walkers, D)
    log_prob: np.ndarray              # (n_steps, n_walkers)
    flat: np.ndarray                  # sampel pasca burn-in (n, D)
    flat_logp: np.ndarray
    summary: pd.DataFrame             # per parameter: awal, MAP, median, q2.5, q97.5, sd
    map_params: dict[str, float]
    median_params: dict[str, float]
    acceptance: float
    n_evals: int
    burn: int
    simulated: SimulationResult       # simulasi dengan MAP
    observed: pd.DataFrame
    metrics: pd.DataFrame
    predictive: dict[str, pd.DataFrame] = field(default_factory=dict)  # var -> DataFrame(q05, q50, q95)
    message: str = ""


def log_likelihood_from_state(runner: SimulationRunner, st: dict, x: np.ndarray) -> float:
    """Log-likelihood Gaussian (dipakai serial maupun di proses anak). st: names, variables, obs, sig, lo, hi."""
    if np.any(x < st["lo"]) or np.any(x > st["hi"]):
        return -np.inf
    try:
        res = runner.run({n: float(v) for n, v in zip(st["names"], x)})
    except Exception:  # noqa: BLE001
        return -np.inf
    matched = _match(res.daily, st["obs"], st["variables"])
    if not matched:
        return -np.inf
    ll = 0.0
    for v, (o, s) in matched.items():
        sv = st["sig"][v]
        sv = sv[: len(o)] if len(sv) >= len(o) else np.full(len(o), sv.mean())
        ll += -0.5 * float(np.sum(((s - o) / sv) ** 2 + np.log(2 * np.pi * sv ** 2)))
    return ll


def calibrate_mcmc(runner: SimulationRunner, obs: pd.DataFrame, variables: list[str],
                   names: list[str], x0: list[float], bounds: list[tuple[float, float]],
                   n_walkers: int = 12, n_steps: int = 100, burn_frac: float = 0.3,
                   rel_error: float = 0.10, n_predictive: int = 40,
                   progress: Callable | None = None, cancelled: Callable | None = None,
                   seed: int = 42, n_workers: int = 1) -> MCMCResult:
    import emcee

    D = len(names)
    n_walkers = max(int(n_walkers), 2 * D + 2)
    if n_walkers % 2:
        n_walkers += 1
    lo = np.array([b[0] for b in bounds], float)
    hi = np.array([b[1] for b in bounds], float)
    variables = [v for v in variables if v in obs.columns]
    if not variables:
        raise ValueError("Tidak ada variabel observasi yang cocok dengan keluaran model.")

    # sigma per titik observasi
    sig = {}
    for v in variables:
        o = obs[v].dropna()
        floor = 0.05 * float(np.mean(np.abs(o))) if len(o) else 1.0
        sig[v] = np.maximum(rel_error * np.abs(o.values.astype(float)), max(floor, 1e-9))
    n_obs = sum(len(obs[v].dropna()) for v in variables)
    total_evals = n_walkers * n_steps
    n_evals = 0
    rng = np.random.default_rng(seed)

    st = {"names": names, "variables": variables, "obs": obs, "sig": sig, "lo": lo, "hi": hi}

    def log_prob(x: np.ndarray) -> float:
        nonlocal n_evals
        if cancelled and cancelled():
            raise InterruptedError("Dibatalkan oleh pengguna.")
        n_evals += 1
        if progress and (n_evals % 5 == 0 or n_evals == 1):
            progress(min(n_evals, total_evals), total_evals, f"MCMC evaluasi {n_evals}/{total_evals}")
        return log_likelihood_from_state(runner, st, x)

    x0a = np.clip(np.array(x0, float), lo, hi)
    spread = 0.02 * (hi - lo)
    p0 = x0a + spread * rng.standard_normal((n_walkers, D))
    p0 = np.clip(p0, lo + 1e-9 * (hi - lo), hi - 1e-9 * (hi - lo))

    if n_workers > 1:
        from .parallel import PoolEvaluator, _task_loglike
        with PoolEvaluator(runner.cfg, n_workers, ll_state=st) as pool:
            sampler = emcee.EnsembleSampler(n_walkers, D, _task_loglike, pool=pool)
            state = p0
            for step in range(int(n_steps)):
                if cancelled and cancelled():
                    raise InterruptedError("Dibatalkan oleh pengguna.")
                state = sampler.run_mcmc(state, 1, progress=False, skip_initial_state_check=True)
                n_evals += n_walkers
                if progress:
                    progress(n_evals, total_evals, f"MCMC langkah {step + 1}/{n_steps} ({n_workers} proses)")
    else:
        sampler = emcee.EnsembleSampler(n_walkers, D, log_prob)
        state = p0
        for _ in range(int(n_steps)):
            state = sampler.run_mcmc(state, 1, progress=False, skip_initial_state_check=True)
    chain = sampler.get_chain()          # (n_steps, n_walkers, D)
    logp = sampler.get_log_prob()        # (n_steps, n_walkers)
    burn = int(burn_frac * n_steps)
    flat = sampler.get_chain(discard=burn, flat=True)
    flat_logp = sampler.get_log_prob(discard=burn, flat=True)
    finite = np.isfinite(flat_logp)
    flat, flat_logp = flat[finite], flat_logp[finite]
    if len(flat) == 0:
        raise RuntimeError("Semua sampel posterior bernilai -inf; periksa batas parameter/observasi.")
    x_map = flat[np.argmax(flat_logp)]
    x_med = np.median(flat, axis=0)
    q025, q975 = np.percentile(flat, [2.5, 97.5], axis=0)
    summary = pd.DataFrame({"awal": x0a, "MAP": x_map, "median": x_med, "q2.5": q025, "q97.5": q975,
                            "sd": flat.std(axis=0)}, index=names)
    map_params = {n: float(v) for n, v in zip(names, x_map)}
    median_params = {n: float(v) for n, v in zip(names, x_med)}
    final = runner.run(map_params)
    metrics = compute_metrics(final.daily, obs, variables)

    # pita prediktif posterior
    predictive: dict[str, pd.DataFrame] = {}
    if n_predictive > 0:
        idx = rng.choice(len(flat), size=min(n_predictive, len(flat)), replace=False)
        runs = []
        for k, i in enumerate(idx, 1):
            if cancelled and cancelled():
                break
            try:
                runs.append(runner.run({n: float(v) for n, v in zip(names, flat[i])}).daily)
            except Exception:  # noqa: BLE001
                continue
            if progress:
                progress(k, len(idx), f"Pita prediktif {k}/{len(idx)}")
        for v in variables:
            cols = [r[v] for r in runs if v in r.columns]
            if cols:
                m = pd.concat(cols, axis=1)
                predictive[v] = pd.DataFrame({"q05": m.quantile(0.05, axis=1), "q50": m.quantile(0.5, axis=1),
                                              "q95": m.quantile(0.95, axis=1)})
    return MCMCResult(names=names, chain=chain, log_prob=logp, flat=flat, flat_logp=flat_logp, summary=summary,
                      map_params=map_params, median_params=median_params,
                      acceptance=float(np.mean(sampler.acceptance_fraction)), n_evals=n_evals, burn=burn,
                      simulated=final, observed=obs, metrics=metrics, predictive=predictive,
                      message=f"{n_walkers} walker x {n_steps} langkah, burn-in {burn}, "
                              f"penerimaan rata-rata {np.mean(sampler.acceptance_fraction):.2f}")
