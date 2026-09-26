"""Analisis sensitivitas global (Morris / Sobol) dengan SALib."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

from .simulation import SimulationRunner


@dataclass
class SensitivityResult:
    method: str
    target: str
    table: pd.DataFrame          # indeks = nama parameter
    samples: pd.DataFrame        # X dan Y per evaluasi
    n_failed: int


def _evaluate(runner: SimulationRunner, names: list[str], X: np.ndarray, target: str,
              progress, cancelled, n_workers: int = 1) -> tuple[np.ndarray, int]:
    if n_workers > 1:
        from .parallel import PoolEvaluator
        overrides = [{n: float(v) for n, v in zip(names, row)} for row in X]
        with PoolEvaluator(runner.cfg, n_workers) as pool:
            Y, n_failed = pool.map_summary(overrides, target, progress, cancelled)
        if np.isnan(Y).any():
            m = np.nanmean(Y)
            Y = np.where(np.isnan(Y), m if np.isfinite(m) else 0.0, Y)
        return Y, n_failed
    Y = np.full(len(X), np.nan)
    n_failed = 0
    for i, row in enumerate(X):
        if cancelled and cancelled():
            raise InterruptedError("Dibatalkan oleh pengguna.")
        overrides = {n: float(v) for n, v in zip(names, row)}
        try:
            res = runner.run(overrides)
            Y[i] = runner.summary_value(res, target)
        except Exception:  # noqa: BLE001
            n_failed += 1
        if progress:
            progress(i + 1, len(X), f"Evaluasi {i + 1}/{len(X)}")
    if np.isnan(Y).any():
        m = np.nanmean(Y)
        fill = m if np.isfinite(m) else 0.0
        Y = np.where(np.isnan(Y), fill, Y)
    return Y, n_failed


def run_morris(runner: SimulationRunner, names: list[str], bounds: list[tuple[float, float]],
               target: str, n_trajectories: int = 10, num_levels: int = 4,
               progress: Callable | None = None, cancelled: Callable | None = None,
               seed: int = 42, n_workers: int = 1) -> SensitivityResult:
    from SALib.sample import morris as morris_sample
    from SALib.analyze import morris as morris_analyze
    problem = {"num_vars": len(names), "names": names, "bounds": [list(b) for b in bounds]}
    X = morris_sample.sample(problem, N=n_trajectories, num_levels=num_levels, seed=seed)
    Y, n_failed = _evaluate(runner, names, X, target, progress, cancelled, n_workers)
    Si = morris_analyze.analyze(problem, X, Y, num_levels=num_levels, print_to_console=False, seed=seed)
    table = pd.DataFrame({"mu": Si["mu"], "mu_star": Si["mu_star"], "sigma": Si["sigma"],
                          "mu_star_conf": Si["mu_star_conf"]}, index=names)
    table = table.sort_values("mu_star", ascending=False)
    samples = pd.DataFrame(X, columns=names)
    samples[target] = Y
    return SensitivityResult("Morris", target, table, samples, n_failed)


def run_sobol(runner: SimulationRunner, names: list[str], bounds: list[tuple[float, float]],
              target: str, n_base: int = 64, progress: Callable | None = None,
              cancelled: Callable | None = None, seed: int = 42, n_workers: int = 1) -> SensitivityResult:
    from SALib.sample import sobol as sobol_sample
    from SALib.analyze import sobol as sobol_analyze
    problem = {"num_vars": len(names), "names": names, "bounds": [list(b) for b in bounds]}
    X = sobol_sample.sample(problem, N=n_base, calc_second_order=False, seed=seed)
    Y, n_failed = _evaluate(runner, names, X, target, progress, cancelled, n_workers)
    Si = sobol_analyze.analyze(problem, Y, calc_second_order=False, print_to_console=False, seed=seed)
    table = pd.DataFrame({"S1": Si["S1"], "S1_conf": Si["S1_conf"], "ST": Si["ST"], "ST_conf": Si["ST_conf"]},
                         index=names).sort_values("ST", ascending=False)
    samples = pd.DataFrame(X, columns=names)
    samples[target] = Y
    return SensitivityResult("Sobol", target, table, samples, n_failed)


def run_fast(runner: SimulationRunner, names: list[str], bounds: list[tuple[float, float]],
             target: str, n_base: int = 72, M: int = 4, progress: Callable | None = None,
             cancelled: Callable | None = None, seed: int = 42, n_workers: int = 1) -> SensitivityResult:
    """Extended FAST (eFAST, Saltelli et al. 1999): N per parameter harus > 4*M^2 (= 64 untuk M = 4)."""
    from SALib.sample import fast_sampler
    from SALib.analyze import fast as fast_analyze
    if n_base <= 4 * M * M:
        raise ValueError(f"eFAST membutuhkan N > 4*M^2 = {4 * M * M} (M = {M}).")
    problem = {"num_vars": len(names), "names": names, "bounds": [list(b) for b in bounds]}
    X = fast_sampler.sample(problem, N=n_base, M=M, seed=seed)
    Y, n_failed = _evaluate(runner, names, X, target, progress, cancelled, n_workers)
    Si = fast_analyze.analyze(problem, Y, M=M, print_to_console=False, seed=seed)
    table = pd.DataFrame({"S1": Si["S1"], "S1_conf": Si.get("S1_conf", np.nan), "ST": Si["ST"],
                          "ST_conf": Si.get("ST_conf", np.nan)}, index=names).sort_values("ST", ascending=False)
    samples = pd.DataFrame(X, columns=names)
    samples[target] = Y
    return SensitivityResult("eFAST", target, table, samples, n_failed)


def sample_count(method: str, n_params: int, n: int) -> int:
    if method == "Morris":
        return n * (n_params + 1)
    if method == "eFAST":
        return n * n_params
    # Sobol tanpa orde-2: N * (D + 2), N sebaiknya pangkat 2
    return n * (n_params + 2)
