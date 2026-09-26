"""Tab Asimilasi data: Ensemble Kalman Filter (EnKF) untuk LAI / SM."""
from __future__ import annotations

import numpy as np
import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QPushButton, QSpinBox, QSplitter, QTableView, QTableWidget, QTableWidgetItem, QTabWidget,
    QVBoxLayout, QWidget,
)

from ..core.assimilation import ASSIMILABLE, EnKFResult, run_enkf
from ..core.calibration import load_observations
from ..core.simulation import CROP_PARAM_INFO, NON_CONTINUOUS_PARAMS
from .widgets import DataFrameModel, MplCanvas, fmt_num, save_dataframe_dialog, show_error

DEFAULT_PERTURB = {"TDWI": 20.0, "SPAN": 10.0, "TSUM1": 5.0}   # TDWI & SPAN mengikuti Guo et al. (2024, FCR)


class PerturbTable(QTableWidget):
    """Tabel [centang | Parameter | Nilai | SD %] untuk perturbasi ansambel."""

    def __init__(self, parent=None):
        super().__init__(0, 5, parent)
        self.setHorizontalHeaderLabels(["", "Parameter", "Nilai", "SD [%]", "Keterangan"])
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

    def set_params(self, values: dict[str, float], defaults: dict[str, float]) -> None:
        self.blockSignals(True)
        self.setRowCount(0)
        for name, val in values.items():
            if name in NON_CONTINUOUS_PARAMS:
                continue
            r = self.rowCount()
            self.insertRow(r)
            cb = QCheckBox(); cb.setChecked(name in defaults)
            self.setCellWidget(r, 0, cb)
            it = QTableWidgetItem(name); it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(r, 1, it)
            v = QTableWidgetItem(fmt_num(val, 6)); v.setFlags(v.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(r, 2, v)
            self.setItem(r, 3, QTableWidgetItem(fmt_num(defaults.get(name, 10.0))))
            k = QTableWidgetItem(CROP_PARAM_INFO.get(name, "")); k.setFlags(k.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(r, 4, k)
        self.resizeColumnsToContents()
        self.setColumnWidth(0, 28)
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.blockSignals(False)

    def perturbations(self) -> dict[str, float]:
        out = {}
        for r in range(self.rowCount()):
            cb = self.cellWidget(r, 0)
            if cb is None or not cb.isChecked():
                continue
            name = self.item(r, 1).text()
            try:
                sd = float(self.item(r, 3).text().replace(",", "."))
            except ValueError as e:
                raise ValueError(f"SD % parameter {name} tidak valid.") from e
            out[name] = sd / 100.0
        return out


class AssimilationTab(QWidget):
    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self.obs: pd.DataFrame | None = None
        self.result: EnKFResult | None = None
        self._populated = False
        self._build()

    def _build(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        split = QSplitter(Qt.Orientation.Horizontal)
        lay.addWidget(split)

        left = QWidget()
        ll = QVBoxLayout(left)
        go = QGroupBox("Observasi state (LAI / SM)")
        vo = QVBoxLayout(go)
        self.bt_load = QPushButton("Buka file observasi (CSV/Excel)...")
        self.bt_load.clicked.connect(self._load_obs)
        vo.addWidget(self.bt_load)
        self.lb_obs = QLabel("Kolom 'day' + kolom LAI (mis. dari citra satelit/UAV) atau SM (sensor tanah).")
        self.lb_obs.setWordWrap(True); self.lb_obs.setStyleSheet("color:#555;")
        vo.addWidget(self.lb_obs)
        ll.addWidget(go)

        gs = QGroupBox("Pengaturan EnKF")
        fs = QFormLayout(gs)
        self.cb_var = QComboBox()
        for k, v in ASSIMILABLE.items():
            self.cb_var.addItem(f"{k}  -  {v}", k)
        self.sp_members = QSpinBox(); self.sp_members.setRange(4, 500); self.sp_members.setValue(100)
        self.sp_members.setToolTip("Guo et al. (2024) menemukan akurasi terbaik pada 100 anggota (uji 50-200)")
        self.sp_obserr = QDoubleSpinBox(); self.sp_obserr.setRange(1, 100); self.sp_obserr.setValue(10); self.sp_obserr.setSuffix(" %")
        self.sp_infl = QDoubleSpinBox(); self.sp_infl.setRange(1.0, 5.0); self.sp_infl.setSingleStep(0.1); self.sp_infl.setValue(1.0)
        self.sp_infl.setToolTip("Faktor inflasi kovarians ansambel (>1 mencegah kolaps ansambel)")
        self.sp_seed = QSpinBox(); self.sp_seed.setRange(0, 999999); self.sp_seed.setValue(42)
        self.cb_update = QCheckBox("Perbarui parameter dulu (ES-MDA, inferensi gabungan parameter + state)")
        self.cb_update.setToolTip("Langkah 1: ensemble smoother memperbarui parameter ansambel dengan semua observasi\n"
                                  "(Emerick & Reynolds 2013); langkah 2: EnKF pada state. Cf. Song et al. 2024, AFM.")
        self.sp_iter = QSpinBox(); self.sp_iter.setRange(1, 6); self.sp_iter.setValue(2)
        self.cb_update.toggled.connect(lambda _: self._update_count())
        self.sp_iter.valueChanged.connect(self._update_count)
        fs.addRow("Variabel diasimilasi", self.cb_var)
        fs.addRow("Jumlah anggota ansambel", self.sp_members)
        fs.addRow("Kesalahan observasi (SD relatif)", self.sp_obserr)
        fs.addRow("Inflasi kovarians", self.sp_infl)
        fs.addRow("Seed acak", self.sp_seed)
        fs.addRow(self.cb_update)
        fs.addRow("Iterasi ES-MDA", self.sp_iter)
        self.lb_count = QLabel("")
        fs.addRow(self.lb_count)
        self.sp_members.valueChanged.connect(self._update_count)
        ll.addWidget(gs)

        gp = QGroupBox("Perturbasi parameter ansambel (lognormal, SD relatif; untuk NAME@x: SD [%] x 0.1 = SD [C])")
        vp = QVBoxLayout(gp)
        hp = QHBoxLayout()
        b_reload = QPushButton("Muat ulang parameter"); b_reload.clicked.connect(lambda: self.refresh_params(force=True))
        hp.addWidget(b_reload); hp.addStretch()
        vp.addLayout(hp)
        self.tb = PerturbTable()
        vp.addWidget(self.tb)
        ll.addWidget(gp, 1)

        hr = QHBoxLayout()
        self.bt_run = QPushButton("Jalankan EnKF")
        self.bt_run.setStyleSheet("font-weight:bold; padding:6px;")
        self.bt_run.clicked.connect(self.run)
        self.bt_cancel = QPushButton("Batal")
        self.bt_cancel.clicked.connect(lambda: self.main.cancel_worker())
        hr.addWidget(self.bt_run); hr.addWidget(self.bt_cancel)
        ll.addLayout(hr)
        split.addWidget(left)

        right = QWidget()
        rl = QVBoxLayout(right)
        self.tabs = QTabWidget()
        self.canvas = MplCanvas(self)
        self.tabs.addTab(self.canvas, "Grafik")
        self.tv_upd = QTableView(); self.model_upd = DataFrameModel(); self.tv_upd.setModel(self.model_upd)
        self.tabs.addTab(self.tv_upd, "Langkah analisis")
        self.tv_sum = QTableView(); self.model_sum = DataFrameModel(); self.tv_sum.setModel(self.model_sum)
        self.tabs.addTab(self.tv_sum, "Ringkasan per anggota")
        self.tv_mem = QTableView(); self.model_mem = DataFrameModel(); self.tv_mem.setModel(self.model_mem)
        self.tabs.addTab(self.tv_mem, "Parameter anggota")
        rl.addWidget(self.tabs)
        he = QHBoxLayout()
        b1 = QPushButton("Simpan langkah analisis")
        b1.clicked.connect(lambda: self.result is not None and save_dataframe_dialog(self, self.result.updates, "enkf_analisis.csv", index=False))
        b2 = QPushButton("Simpan ringkasan anggota")
        b2.clicked.connect(lambda: self.result is not None and save_dataframe_dialog(self, self.model_sum.df(), "enkf_ringkasan.csv"))
        b3 = QPushButton("Simpan pita harian")
        b3.clicked.connect(self._export_band)
        b4 = QPushButton("Simpan grafik")
        b4.clicked.connect(lambda: self.canvas.save_dialog(self, "enkf.png"))
        for b in (b1, b2, b3, b4):
            he.addWidget(b)
        he.addStretch()
        rl.addLayout(he)
        split.addWidget(right)
        left.setMaximumWidth(600)
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setSizes([540, 700])
        self.lb_info = QLabel("")
        self.lb_info.setWordWrap(True); self.lb_info.setStyleSheet("color:#555;")
        rl.addWidget(self.lb_info)
        self._update_count()

    # ------------------------------------------------------------------
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
        keep = DEFAULT_PERTURB
        if self._populated and not force:
            try:
                keep = {k: v * 100 for k, v in self.tb.perturbations().items()}
            except ValueError:
                pass
        self.tb.set_params(values, keep)
        self._populated = True

    def _update_count(self) -> None:
        k = 2 + (int(self.sp_iter.value()) if self.cb_update.isChecked() else 0)
        n = k * int(self.sp_members.value()) + 1
        self.lb_count.setText(f"{n} simulasi (open-loop{' + ES-MDA' if k > 2 else ''} + asimilasi), ~{n * 0.2:.0f} detik")

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
        cols = [c for c in self.obs.columns if c in ASSIMILABLE]
        if cols:
            self.cb_var.setCurrentIndex(self.cb_var.findData(cols[0]))
        self.lb_obs.setText(f"{p}\n{len(self.obs)} tanggal, {self.obs.index.min().date()} s.d. {self.obs.index.max().date()}; "
                            f"variabel: {', '.join(self.obs.columns)}"
                            + ("" if cols else "\nPERINGATAN: tidak ada kolom LAI/SM."))

    def run(self) -> None:
        if self.obs is None:
            show_error(self, "EnKF", "Muat file observasi terlebih dahulu.")
            return
        var = self.cb_var.currentData()
        if var not in self.obs.columns:
            show_error(self, "EnKF", f"Kolom {var} tidak ada pada observasi.")
            return
        try:
            perturb = self.tb.perturbations()
        except ValueError as e:
            show_error(self, "Parameter", str(e))
            return
        if not perturb:
            show_error(self, "Parameter", "Pilih minimal satu parameter untuk diperturbasi (agar ansambel menyebar).")
            return
        runner = self.main.get_runner()
        if runner is None:
            return
        n, err, infl, seed = int(self.sp_members.value()), self.sp_obserr.value() / 100.0, self.sp_infl.value(), int(self.sp_seed.value())
        obs = self.obs
        upd, nit = self.cb_update.isChecked(), int(self.sp_iter.value())

        def job(progress, cancelled):
            return run_enkf(runner, obs, var, perturb, n_members=n, obs_rel_error=err, inflation=infl,
                            progress=progress, cancelled=cancelled, seed=seed, update_params=upd, n_smoother_iter=nit)

        self.main.start_worker(job, self._done, f"EnKF {var} ({n} anggota)")

    def _done(self, res: EnKFResult) -> None:
        self.result = res
        self.model_upd.set_df(res.updates); self.tv_upd.resizeColumnsToContents()
        cols = [c for c in ("TWSO", "TAGP", "LAIMAX", "DOA", "DOM", "CTRAT") if c in res.summary_assim.columns]
        a = res.summary_assim[cols].add_suffix("_asimilasi")
        o = res.summary_open[cols].add_suffix("_openloop")
        self.model_sum.set_df(pd.concat([o, a], axis=1)); self.tv_sum.resizeColumnsToContents()
        self.model_mem.set_df(res.members); self.tv_mem.resizeColumnsToContents()
        self.lb_info.setText(res.message)
        self.main.log("EnKF selesai. " + res.message)
        self._plot(res)
        self.tabs.setCurrentIndex(0)

    def _plot(self, res: EnKFResult) -> None:
        self.canvas.clear()
        v = res.assim_var
        ax1 = self.canvas.fig.add_subplot(2, 2, 1)
        bo, ba = res.band(v, False), res.band(v, True)
        if not bo.empty:
            ax1.fill_between(bo.index, bo["q05"], bo["q95"], color="gray", alpha=0.25, label="Open-loop 90 %")
            ax1.plot(bo.index, bo["mean"], color="gray", lw=1.4, label="Open-loop rata-rata")
        if not ba.empty:
            ax1.fill_between(ba.index, ba["q05"], ba["q95"], color="#3b7dd8", alpha=0.25, label="EnKF 90 %")
            ax1.plot(ba.index, ba["mean"], color="#3b7dd8", lw=1.8, label="EnKF rata-rata")
        o = res.obs[v].dropna()
        ax1.plot(o.index, o.values, "o", color="#d8583b", ms=5, label="Observasi")
        ax1.set_title(f"{v}: ansambel open-loop vs EnKF", fontsize=9); ax1.grid(alpha=0.3); ax1.legend(fontsize=7)
        ax1.tick_params(axis="x", labelrotation=30, labelsize=8)

        ax2 = self.canvas.fig.add_subplot(2, 2, 2)
        bo, ba = res.band("TWSO", False), res.band("TWSO", True)
        if not bo.empty:
            ax2.fill_between(bo.index, bo["q05"], bo["q95"], color="gray", alpha=0.25)
            ax2.plot(bo.index, bo["mean"], color="gray", lw=1.4, label="Open-loop")
        if not ba.empty:
            ax2.fill_between(ba.index, ba["q05"], ba["q95"], color="#3b7dd8", alpha=0.25)
            ax2.plot(ba.index, ba["mean"], color="#3b7dd8", lw=1.8, label="EnKF")
        ax2.plot(res.baseline.daily.index, res.baseline.daily["TWSO"], "k--", lw=1, label="Deterministik")
        ax2.set_title("TWSO [kg/ha]", fontsize=9); ax2.grid(alpha=0.3); ax2.legend(fontsize=7)
        ax2.tick_params(axis="x", labelrotation=30, labelsize=8)

        ax3 = self.canvas.fig.add_subplot(2, 2, 3)
        yo = res.summary_open["TWSO"].dropna(); ya = res.summary_assim["TWSO"].dropna()
        bins = np.linspace(min(yo.min(), ya.min()), max(yo.max(), ya.max()), 20) if len(yo) and len(ya) else 20
        ax3.hist(yo, bins=bins, color="gray", alpha=0.5, label=f"Open-loop ({yo.mean():.0f} +/- {yo.std():.0f})")
        ax3.hist(ya, bins=bins, color="#3b7dd8", alpha=0.6, label=f"EnKF ({ya.mean():.0f} +/- {ya.std():.0f})")
        ax3.set_xlabel("Hasil akhir TWSO [kg/ha]"); ax3.set_title("Sebaran hasil ansambel", fontsize=9)
        ax3.legend(fontsize=7); ax3.grid(alpha=0.3)

        ax4 = self.canvas.fig.add_subplot(2, 2, 4)
        u = res.updates[res.updates["status"] == "OK"] if not res.updates.empty else res.updates
        if not u.empty:
            x = pd.to_datetime(u["tanggal"])
            ax4.plot(x, u["forecast_mean"], "s-", color="gray", ms=4, label="Forecast (rata-rata)")
            ax4.plot(x, u["analysis_mean"], "o-", color="#3b7dd8", ms=4, label="Analisis (rata-rata)")
            ax4.plot(x, u["observasi"], "^", color="#d8583b", ms=5, label="Observasi")
            ax4b = ax4.twinx()
            ax4b.bar(x, u["K"], width=2, color="#7fbf7f", alpha=0.4, label="Gain K")
            ax4b.set_ylim(0, 1); ax4b.set_ylabel("Gain Kalman K", fontsize=8)
            ax4.legend(fontsize=7, loc="upper left")
        ax4.set_title("Langkah analisis EnKF", fontsize=9); ax4.grid(alpha=0.3)
        ax4.tick_params(axis="x", labelrotation=30, labelsize=8)
        self.canvas.draw()

    def _export_band(self) -> None:
        if self.result is None:
            return
        frames = []
        for v in self.result.daily_assim:
            b = self.result.band(v, True).add_prefix(f"{v}_enkf_")
            bo = self.result.band(v, False).add_prefix(f"{v}_open_")
            frames += [b, bo]
        save_dataframe_dialog(self, pd.concat(frames, axis=1), "enkf_pita_harian.csv")
