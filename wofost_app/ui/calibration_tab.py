"""Tab Kalibrasi: cocokkan parameter tanaman dengan data observasi lapangan."""
from __future__ import annotations

import numpy as np
import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QSpinBox, QSplitter, QTableView, QTabWidget, QVBoxLayout, QWidget,
)

from ..core.bayesian import MCMCResult, calibrate_mcmc
from ..core.calibration import CalibrationResult, calibrate, compute_metrics, load_observations
from ..core.parallel import default_workers
from ..core.simulation import CROP_PARAM_INFO, DAILY_VARS, NON_CONTINUOUS_PARAMS
from .widgets import CheckParamTable, DataFrameModel, MplCanvas, fmt_num, save_dataframe_dialog, show_error

PRESELECT = ["TSUM1", "TSUM2", "SPAN"]


class CalibrationTab(QWidget):
    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self.obs: pd.DataFrame | None = None
        self.result: CalibrationResult | None = None
        self._populated = False
        self._build()

    def _build(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        split = QSplitter(Qt.Orientation.Horizontal)
        lay.addWidget(split)

        left = QWidget()
        ll = QVBoxLayout(left)

        go = QGroupBox("Data observasi")
        vo = QVBoxLayout(go)
        hb = QHBoxLayout()
        self.bt_load = QPushButton("Buka file observasi (CSV/Excel)...")
        self.bt_load.clicked.connect(self._load_obs)
        hb.addWidget(self.bt_load)
        vo.addLayout(hb)
        self.lb_obs = QLabel("Format: kolom 'day' + kolom variabel (LAI, TAGP, TWSO, SM, ...), "
                             "atau format panjang 'day, variable, value'.")
        self.lb_obs.setWordWrap(True); self.lb_obs.setStyleSheet("color:#555;")
        vo.addWidget(self.lb_obs)
        self.ls_vars = QListWidget()
        self.ls_vars.setMaximumHeight(90)
        vo.addWidget(self.ls_vars)
        ll.addWidget(go)

        gp = QGroupBox("Parameter yang dikalibrasi")
        vp = QVBoxLayout(gp)
        hp = QHBoxLayout()
        self.sp_pct = QDoubleSpinBox(); self.sp_pct.setRange(1, 90); self.sp_pct.setValue(30); self.sp_pct.setSuffix(" %")
        b_pct = QPushButton("Terapkan rentang"); b_pct.clicked.connect(lambda: self.tb.apply_pct(self.sp_pct.value()))
        b_reload = QPushButton("Muat ulang parameter"); b_reload.clicked.connect(lambda: self.refresh_params(force=True))
        hp.addWidget(QLabel("Rentang +/-")); hp.addWidget(self.sp_pct); hp.addWidget(b_pct); hp.addWidget(b_reload)
        vp.addLayout(hp)
        self.tb = CheckParamTable(value_label="Nilai awal")
        vp.addWidget(self.tb)
        ll.addWidget(gp, 1)

        gm = QGroupBox("Optimasi")
        fm = QFormLayout(gm)
        self.cb_method = QComboBox()
        self.cb_method.addItem("Least squares (Trust Region Reflective, berbatas)", "least_squares")
        self.cb_method.addItem("Nelder-Mead (simplex, berbatas)", "nelder")
        self.cb_method.addItem("Bayesian MCMC (emcee, prior seragam)", "mcmc")
        self.cb_method.currentIndexChanged.connect(self._method_changed)
        self.sp_max = QSpinBox(); self.sp_max.setRange(10, 5000); self.sp_max.setValue(150)
        self.sp_walkers = QSpinBox(); self.sp_walkers.setRange(4, 200); self.sp_walkers.setValue(12)
        self.sp_steps = QSpinBox(); self.sp_steps.setRange(10, 5000); self.sp_steps.setValue(100)
        self.sp_relerr = QDoubleSpinBox(); self.sp_relerr.setRange(1, 100); self.sp_relerr.setValue(10); self.sp_relerr.setSuffix(" %")
        self.sp_relerr.setToolTip("Simpangan baku kesalahan observasi relatif terhadap nilai observasi (likelihood Gaussian)")
        self.sp_pred = QSpinBox(); self.sp_pred.setRange(0, 500); self.sp_pred.setValue(40)
        self.sp_workers = QSpinBox(); self.sp_workers.setRange(1, 64); self.sp_workers.setValue(default_workers())
        self.sp_workers.setToolTip("1 = serial; >1 = pool proses untuk evaluasi walker secara paralel")
        fm.addRow("Metode", self.cb_method)
        self.lb_max = QLabel("Evaluasi maksimum"); fm.addRow(self.lb_max, self.sp_max)
        self.lb_walkers = QLabel("Jumlah walker"); fm.addRow(self.lb_walkers, self.sp_walkers)
        self.lb_steps = QLabel("Langkah per walker"); fm.addRow(self.lb_steps, self.sp_steps)
        self.lb_relerr = QLabel("Kesalahan observasi"); fm.addRow(self.lb_relerr, self.sp_relerr)
        self.lb_pred = QLabel("Sampel pita prediktif"); fm.addRow(self.lb_pred, self.sp_pred)
        self.lb_workers = QLabel("Proses paralel"); fm.addRow(self.lb_workers, self.sp_workers)
        self.lb_mcmc_count = QLabel(""); fm.addRow(self.lb_mcmc_count)
        for w in (self.sp_walkers, self.sp_steps, self.sp_pred, self.sp_workers):
            w.valueChanged.connect(self._update_mcmc_count)
        ll.addWidget(gm)
        self._method_changed()

        hr = QHBoxLayout()
        self.bt_run = QPushButton("Jalankan kalibrasi")
        self.bt_run.setStyleSheet("font-weight:bold; padding:6px;")
        self.bt_run.clicked.connect(self.run)
        self.bt_cancel = QPushButton("Batal")
        self.bt_cancel.clicked.connect(lambda: self.main.cancel_worker())
        self.bt_apply = QPushButton("Terapkan hasil ke Pengaturan")
        self.bt_apply.setEnabled(False)
        self.bt_apply.clicked.connect(self._apply)
        hr.addWidget(self.bt_run); hr.addWidget(self.bt_cancel); hr.addWidget(self.bt_apply)
        ll.addLayout(hr)
        split.addWidget(left)

        right = QWidget()
        rl = QVBoxLayout(right)
        self.tabs = QTabWidget()
        self.canvas = MplCanvas(self)
        self.tabs.addTab(self.canvas, "Grafik")
        self.tv_params = QTableView(); self.model_params = DataFrameModel(); self.tv_params.setModel(self.model_params)
        self.tabs.addTab(self.tv_params, "Parameter")
        self.tv_metrics = QTableView(); self.model_metrics = DataFrameModel(); self.tv_metrics.setModel(self.model_metrics)
        self.tabs.addTab(self.tv_metrics, "Metrik")
        self.tv_obs = QTableView(); self.model_obs = DataFrameModel(); self.tv_obs.setModel(self.model_obs)
        self.tabs.addTab(self.tv_obs, "Observasi")
        self.canvas_post = MplCanvas(self)
        self.tabs.addTab(self.canvas_post, "Posterior (MCMC)")
        rl.addWidget(self.tabs)
        he = QHBoxLayout()
        b1 = QPushButton("Simpan parameter")
        b1.clicked.connect(lambda: self.result is not None and save_dataframe_dialog(self, self.model_params.df(), "kalibrasi_parameter.csv"))
        b2 = QPushButton("Simpan metrik")
        b2.clicked.connect(lambda: self.result is not None and save_dataframe_dialog(self, self.model_metrics.df(), "kalibrasi_metrik.csv"))
        b3 = QPushButton("Simpan grafik")
        b3.clicked.connect(lambda: self.canvas.save_dialog(self, "kalibrasi.png"))
        for b in (b1, b2, b3):
            he.addWidget(b)
        he.addStretch()
        rl.addLayout(he)
        split.addWidget(right)
        left.setMaximumWidth(620)
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setSizes([560, 640])

    # ------------------------------------------------------------------
    def _method_changed(self) -> None:
        mcmc = self.cb_method.currentData() == "mcmc"
        for w in (self.lb_max, self.sp_max):
            w.setVisible(not mcmc)
        for w in (self.lb_walkers, self.sp_walkers, self.lb_steps, self.sp_steps, self.lb_relerr, self.sp_relerr,
                  self.lb_pred, self.sp_pred, self.lb_workers, self.sp_workers, self.lb_mcmc_count):
            w.setVisible(mcmc)
        self._update_mcmc_count()

    def _update_mcmc_count(self) -> None:
        n = self.sp_walkers.value() * self.sp_steps.value() + self.sp_pred.value()
        w = max(1, int(self.sp_workers.value()))
        self.lb_mcmc_count.setText(f"~{n} simulasi (~{n * 0.15 / 60 / w:.1f} menit dengan {w} proses)")

    def showEvent(self, ev) -> None:  # noqa: N802
        super().showEvent(ev)
        if not self._populated:
            self.refresh_params()

    def refresh_params(self, force: bool = False) -> None:
        try:
            values = self.main.setup_tab.current_crop_params()
        except ValueError as e:
            show_error(self, "Parameter", str(e))
            return
        checked = PRESELECT
        if self._populated and not force:
            try:
                checked = [d["name"] for d in self.tb.selected()]
            except ValueError:
                pass
        self.tb.set_params(values, CROP_PARAM_INFO, self.sp_pct.value(), exclude=NON_CONTINUOUS_PARAMS,
                           preselect=checked)
        self._populated = True

    def _load_obs(self) -> None:
        p, _ = QFileDialog.getOpenFileName(self, "Buka file observasi", "", "Data (*.csv *.xlsx *.xls)")
        if p:
            self.load_obs_file(p)

    def load_obs_file(self, p: str) -> None:
        try:
            self.obs = load_observations(p)
        except Exception as e:  # noqa: BLE001
            show_error(self, "Gagal membaca observasi", f"{type(e).__name__}: {e}")
            return
        self.model_obs.set_df(self.obs)
        self.tv_obs.resizeColumnsToContents()
        self.ls_vars.clear()
        known = [c for c in self.obs.columns if c in DAILY_VARS]
        for c in self.obs.columns:
            it = QListWidgetItem(f"{c}  -  {DAILY_VARS.get(c, 'bukan keluaran model')}")
            it.setData(Qt.ItemDataRole.UserRole, c)
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            it.setCheckState(Qt.CheckState.Checked if c in known else Qt.CheckState.Unchecked)
            self.ls_vars.addItem(it)
        self.lb_obs.setText(f"{p}\n{len(self.obs)} tanggal, {self.obs.index.min().date()} s.d. "
                            f"{self.obs.index.max().date()}; variabel: {', '.join(self.obs.columns)}")
        self.tabs.setCurrentWidget(self.tv_obs)

    def _selected_vars(self) -> list[str]:
        out = []
        for i in range(self.ls_vars.count()):
            it = self.ls_vars.item(i)
            if it.checkState() == Qt.CheckState.Checked:
                out.append(it.data(Qt.ItemDataRole.UserRole))
        return out

    def run(self) -> None:
        if self.obs is None:
            show_error(self, "Kalibrasi", "Muat file observasi terlebih dahulu.")
            return
        variables = [v for v in self._selected_vars() if v in DAILY_VARS]
        if not variables:
            show_error(self, "Kalibrasi", "Pilih minimal satu variabel observasi yang merupakan keluaran model.")
            return
        try:
            sel = self.tb.selected()
        except ValueError as e:
            show_error(self, "Parameter", str(e))
            return
        if not sel:
            show_error(self, "Parameter", "Pilih minimal satu parameter untuk dikalibrasi.")
            return
        runner = self.main.get_runner()
        if runner is None:
            return
        # pastikan observasi berada dalam periode simulasi
        cfg = runner.cfg
        inside = self.obs[(self.obs.index.date >= cfg.crop_start_date) & (self.obs.index.date <= cfg.crop_end_date)]
        if inside.empty:
            show_error(self, "Kalibrasi", "Tidak ada tanggal observasi di dalam periode simulasi "
                                          f"({cfg.crop_start_date} s.d. {cfg.crop_end_date}). Sesuaikan kalender tanam.")
            return
        names = [d["name"] for d in sel]
        x0 = [d["x0"] for d in sel]
        bounds = [(d["lo"], d["hi"]) for d in sel]
        method = self.cb_method.currentData()
        max_evals = int(self.sp_max.value())
        obs = self.obs
        self._runner_for_plot = runner
        if method == "mcmc":
            nw, ns = int(self.sp_walkers.value()), int(self.sp_steps.value())
            rel, npred = float(self.sp_relerr.value()) / 100.0, int(self.sp_pred.value())
            nproc = int(self.sp_workers.value())

            def job_mcmc(progress, cancelled):
                return calibrate_mcmc(runner, obs, variables, names, x0, bounds, n_walkers=nw, n_steps=ns,
                                      rel_error=rel, n_predictive=npred, progress=progress, cancelled=cancelled,
                                      n_workers=nproc)

            self.main.start_worker(job_mcmc, self._done_mcmc, f"MCMC {', '.join(names)} ({nw} walker x {ns} langkah)")
            return

        def job(progress, cancelled):
            return calibrate(runner, obs, variables, names, x0, bounds, method=method, max_evals=max_evals,
                             progress=progress, cancelled=cancelled)

        self.main.start_worker(job, self._done, f"Kalibrasi {', '.join(names)}")

    def _done_mcmc(self, res: MCMCResult) -> None:
        self.result = res
        summ = res.summary.copy()
        summ["keterangan"] = [CROP_PARAM_INFO.get(n, "") for n in summ.index]
        self.model_params.set_df(summ)
        self.tv_params.resizeColumnsToContents()
        try:
            before = self._runner_for_plot.run({n: float(v) for n, v in zip(res.names, res.summary["awal"])})
            m0 = compute_metrics(before.daily, res.observed, list(res.metrics.index))
            m0.columns = [f"{c}_awal" for c in m0.columns]
            metrics = pd.concat([m0, res.metrics.add_suffix("_MAP")], axis=1)
        except Exception:  # noqa: BLE001
            before, metrics = None, res.metrics
        self.model_metrics.set_df(metrics)
        self.tv_metrics.resizeColumnsToContents()
        self.bt_apply.setEnabled(True)
        self.main.log(f"MCMC selesai: {res.message}; {res.n_evals} evaluasi. MAP: "
                      + "; ".join(f"{k}={fmt_num(v, 5)}" for k, v in res.map_params.items()))
        self._plot_mcmc(res, before)
        self.tabs.setCurrentIndex(0)

    def _plot_mcmc(self, res: MCMCResult, before) -> None:
        self.canvas.clear()
        vars_ = list(res.metrics.index)
        n = len(vars_) + 1
        ncols = 2
        nrows = (n + ncols - 1) // ncols
        sim = res.simulated.daily
        for i, v in enumerate(vars_, 1):
            ax = self.canvas.fig.add_subplot(nrows, ncols, i)
            band = res.predictive.get(v)
            if band is not None and not band.empty:
                ax.fill_between(band.index, band["q05"], band["q95"], color="#3b7dd8", alpha=0.2, label="Prediktif 90 %")
            if before is not None and v in before.daily.columns:
                ax.plot(before.daily.index, before.daily[v], "--", color="gray", lw=1.2, label="Simulasi awal")
            ax.plot(sim.index, sim[v], color="#3b7dd8", lw=1.8, label="Simulasi MAP")
            o = res.observed[v].dropna()
            ax.plot(o.index, o.values, "o", color="#d8583b", ms=5, label="Observasi")
            r = res.metrics.loc[v]
            ax.set_title(f"{v}: RMSE={r['RMSE']:.3g}, nRMSE={r['nRMSE_%']:.1f}%, R2={r['R2']:.3f}", fontsize=9)
            ax.grid(alpha=0.3)
            ax.tick_params(axis="x", labelrotation=30, labelsize=8)
            if i == 1:
                ax.legend(fontsize=7)
        ax = self.canvas.fig.add_subplot(nrows, ncols, n)
        lp = res.log_prob.copy()
        lp[~np.isfinite(lp)] = np.nan
        ax.plot(np.arange(lp.shape[0]), lp, lw=0.6, alpha=0.5)
        ax.axvline(res.burn, color="k", ls="--", lw=0.8)
        ax.set_xlabel("Langkah"); ax.set_ylabel("log posterior"); ax.set_title("Jejak log-posterior (per walker)", fontsize=9)
        ax.grid(alpha=0.3)
        self.canvas.draw()
        self.canvas_post.clear()
        D = len(res.names)
        for j, name in enumerate(res.names):
            axh = self.canvas_post.fig.add_subplot(D, 2, 2 * j + 1)
            axh.hist(res.flat[:, j], bins=30, color="#3b7dd8", alpha=0.8)
            axh.axvline(res.map_params[name], color="#d8583b", lw=1.5, label="MAP")
            axh.axvline(res.summary.loc[name, "q2.5"], color="k", ls=":", lw=0.9)
            axh.axvline(res.summary.loc[name, "q97.5"], color="k", ls=":", lw=0.9, label="IK 95 %")
            axh.set_title(f"Posterior {name}", fontsize=9)
            if j == 0:
                axh.legend(fontsize=7)
            axt = self.canvas_post.fig.add_subplot(D, 2, 2 * j + 2)
            axt.plot(res.chain[:, :, j], lw=0.5, alpha=0.6)
            axt.axvline(res.burn, color="k", ls="--", lw=0.8)
            axt.set_title(f"Jejak {name}", fontsize=9)
            axt.tick_params(labelsize=8)
        self.canvas_post.draw()

    def _done(self, res: CalibrationResult) -> None:
        self.result = res
        rows = []
        for n in res.params:
            x0 = res.initial[n]
            x1 = res.params[n]
            rows.append({"parameter": n, "awal": x0, "terkalibrasi": x1,
                         "perubahan_%": 100 * (x1 - x0) / x0 if x0 else np.nan,
                         "keterangan": CROP_PARAM_INFO.get(n, "")})
        self.model_params.set_df(pd.DataFrame(rows).set_index("parameter"))
        self.tv_params.resizeColumnsToContents()
        # metrik sebelum & sesudah
        try:
            before = self._runner_for_plot.run(res.initial)
            m0 = compute_metrics(before.daily, res.observed, list(res.metrics.index))
            m0.columns = [f"{c}_awal" for c in m0.columns]
            metrics = pd.concat([m0, res.metrics.add_suffix("_kalibrasi")], axis=1)
        except Exception:  # noqa: BLE001
            before = None
            metrics = res.metrics
        self.model_metrics.set_df(metrics)
        self.tv_metrics.resizeColumnsToContents()
        self.bt_apply.setEnabled(True)
        self.main.log(f"Kalibrasi selesai ({res.n_evals} evaluasi, {res.message}). "
                      + "; ".join(f"{k}={fmt_num(v, 5)}" for k, v in res.params.items()))
        self._plot(res, before)
        self.tabs.setCurrentIndex(0)

    def _plot(self, res: CalibrationResult, before) -> None:
        self.canvas.clear()
        vars_ = list(res.metrics.index)
        n = len(vars_) + 1
        ncols = 2
        nrows = (n + ncols - 1) // ncols
        sim = res.simulated.daily
        for i, v in enumerate(vars_, 1):
            ax = self.canvas.fig.add_subplot(nrows, ncols, i)
            if before is not None and v in before.daily.columns:
                ax.plot(before.daily.index, before.daily[v], "--", color="gray", lw=1.2, label="Simulasi awal")
            ax.plot(sim.index, sim[v], color="#3b7dd8", lw=1.8, label="Simulasi terkalibrasi")
            o = res.observed[v].dropna()
            ax.plot(o.index, o.values, "o", color="#d8583b", ms=5, label="Observasi")
            r = res.metrics.loc[v]
            ax.set_title(f"{v}: RMSE={r['RMSE']:.3g}, nRMSE={r['nRMSE_%']:.1f}%, R2={r['R2']:.3f}", fontsize=9)
            ax.grid(alpha=0.3)
            ax.tick_params(axis="x", labelrotation=30, labelsize=8)
            if i == 1:
                ax.legend(fontsize=7)
        ax = self.canvas.fig.add_subplot(nrows, ncols, n)
        ax.plot(np.arange(1, len(res.history) + 1), res.history, ".-", lw=1, ms=3)
        ax.set_yscale("log")
        ax.set_xlabel("Evaluasi"); ax.set_ylabel("SSE ternormalisasi")
        ax.set_title("Konvergensi", fontsize=9)
        ax.grid(alpha=0.3)
        self.canvas.draw()

    def _apply(self) -> None:
        if self.result is None:
            return
        params = self.result.map_params if isinstance(self.result, MCMCResult) else self.result.params
        self.main.setup_tab.apply_overrides(params)
        self.main.log("Parameter hasil kalibrasi diterapkan sebagai override di tab Pengaturan.")
