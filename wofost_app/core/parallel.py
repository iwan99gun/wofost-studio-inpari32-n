"""Evaluasi paralel WOFOST dengan pool proses (untuk Sobol / eFAST / Morris / MCMC).

Setiap proses anak membangun SimulationRunner sendiri dari SimulationConfig (dict) lewat initializer,
sehingga tidak ada objek PCSE yang perlu di-pickle per tugas. Cocok untuk Windows (start method spawn).
"""
from __future__ import annotations

import os
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from typing import Callable, Iterable

import numpy as np

_RUNNER = None
_LL = None


def default_workers() -> int:
    return max(1, (os.cpu_count() or 2) - 1)


# ----------------------------------------------------------------------------- initializer / tugas
def _init_worker(cfg_dict: dict, ll_state: dict | None = None) -> None:
    global _RUNNER, _LL
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    from .config import SimulationConfig
    from .simulation import SimulationRunner
    from .weather import build_weather_provider
    cfg = SimulationConfig.from_dict(cfg_dict)
    _RUNNER = SimulationRunner(cfg, build_weather_provider(cfg.weather))
    _LL = ll_state


def _task_summary(args) -> float:
    overrides, target = args
    try:
        res = _RUNNER.run(overrides)
        return float(_RUNNER.summary_value(res, target))
    except Exception:  # noqa: BLE001
        return float("nan")


def _task_loglike(x) -> float:
    from .bayesian import log_likelihood_from_state
    return log_likelihood_from_state(_RUNNER, _LL, np.asarray(x, float))


# ----------------------------------------------------------------------------- evaluator
class PoolEvaluator:
    """Context manager pool proses. Menyediakan `map_summary` dan antarmuka `map` untuk emcee."""

    def __init__(self, cfg, n_workers: int, ll_state: dict | None = None):
        import multiprocessing as mp
        self.cfg_dict = cfg.to_dict()
        self.n_workers = max(1, int(n_workers))
        self.ll_state = ll_state
        self._ctx = mp.get_context("spawn")
        self._ex: ProcessPoolExecutor | None = None

    def __enter__(self):
        self._ex = ProcessPoolExecutor(max_workers=self.n_workers, mp_context=self._ctx,
                                       initializer=_init_worker, initargs=(self.cfg_dict, self.ll_state))
        return self

    def __exit__(self, *exc):
        if self._ex is not None:
            self._ex.shutdown(wait=False, cancel_futures=True)
            self._ex = None

    def map_summary(self, overrides_list: list[dict], target: str,
                    progress: Callable | None = None, cancelled: Callable | None = None) -> tuple[np.ndarray, int]:
        assert self._ex is not None
        futures = {self._ex.submit(_task_summary, (ov, target)): i for i, ov in enumerate(overrides_list)}
        Y = np.full(len(overrides_list), np.nan)
        done_n = 0
        pending = set(futures)
        while pending:
            if cancelled and cancelled():
                self._ex.shutdown(wait=False, cancel_futures=True)
                raise InterruptedError("Dibatalkan oleh pengguna.")
            finished, pending = wait(pending, timeout=0.5, return_when=FIRST_COMPLETED)
            for f in finished:
                Y[futures[f]] = f.result()
                done_n += 1
            if finished and progress:
                progress(done_n, len(overrides_list), f"Evaluasi paralel {done_n}/{len(overrides_list)} ({self.n_workers} proses)")
        n_failed = int(np.isnan(Y).sum())
        return Y, n_failed

    # antarmuka pool untuk emcee: pool.map(fn, iterable)
    def map(self, fn, iterable: Iterable):
        assert self._ex is not None
        return list(self._ex.map(fn, iterable))
