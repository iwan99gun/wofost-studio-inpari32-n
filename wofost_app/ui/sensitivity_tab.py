"""Tab Analisis Sensitivitas Global (Morris / Sobol via SALib)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QSpinBox,
    QSplitter, QTableView, QTabWidget, QVBoxLayout, QWidget,
)

from ..core.parallel import default_workers
from ..core.sensitivity import SensitivityResult, run_fast, run_morris, run_sobol, sample_count
from ..core.simulation import CROP_PARAM_INFO, NON_CONTINUOUS_PARAMS, SUMMARY_VARS
from .widgets import CheckParamTable, DataFrameModel, MplCanvas, save_dataframe_dialog, show_error

PRESELECT = ["TSUM1", "TSUM2", "SPAN", "CVO", "CVL", "RGRLAI", "TDWI", "Q10", "CFET"]
TARGETS = list(SUMMARY_VARS.keys()) + ["DOA", "DOM"]


class SensitivityTab(QWidget):
    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self.result: SensitivityResult | None = None
        self._populated = False
        self._build()

    def _build(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        split = QSplitter(Qt.Orientation.Horizontal)
        lay.addWidget(split)

        left = QWidget()
        ll = QVBoxLayout(left)
        g = QGroupBox("Pengaturan analisis")
        f = QFormLayout(g)
        self.cb_method = QComboBox(); self.cb_method.addItems(["Morris", "Sobol", "eFAST"])
        self.cb_method.setToolTip("Morris: screening/peringkat murah; Sobol: dekomposisi varians;\n"
                                  "eFAST: dekomposisi varians berbasis Fourier (lazim di literatur WOFOST)")
        self.cb_method.currentTextChanged.connect(self._method_changed)
        self.sp_n = QSpinBox(); self.sp_n.setRange(2, 4096); self.sp_n.setValue(10)
        self.sp_n.valueChanged.connect(self._update_count)
        self.cb_target = QComboBox()
        for t in TARGETS:
            self.cb_target.addItem(f"{t}  -  {SUMMARY_VARS.get(t, 'tanggal (hari dalam tahun)')}", t)
        self.sp_pct = QDoubleSpinBox(); self.sp_pct.setRange(1, 90); self.sp_pct.setValue(20); self.sp_pct.setSuffix(" %")
        self.sp_seed = QSpinBox(); self.sp_seed.setRange(0, 999999); self.sp_seed.setValue(42)
        self.sp_workers = QSpinBox(); self.sp_workers.setRange(1, 64); self.sp_workers.setValue(default_workers())
        self.sp_workers.setToolTip("1 = serial; >1 = pool proses (tiap proses memuat ulang cuaca dari cache)")
        self.sp_workers.valueChanged.connect(self._update_count)
        f.addRow("Metode", self.cb_method)
        self.lb_n = QLabel("Jumlah lintasan (N)")
        f.addRow(self.lb_n, self.sp_n)
        f.addRow("Keluaran target", self.cb_target)
        f.addRow("Rentang +/- dari nilai", self.sp_pct)
        f.addRow("Seed acak", self.sp_seed)
        f.addRow("Proses paralel", self.sp_workers)
        ll.addWidget(g)

        hb = QHBoxLayout()
        b_pct = QPushButton("Terapkan rentang %")
        b_pct.clicked.connect(lambda: (self.tb.apply_pct(self.sp_pct.value()), self._update_count()))
        b_reload = QPushButton("Muat ulang parameter")
        b_reload.clicked.connect(lambda: self.refresh_params(force=True))
        b_all = QPushButton("Pilih semua"); b_all.clicked.connect(lambda: (self.tb.check_all(True), self._update_count()))
        b_none = QPushButton("Kosongkan"); b_none.clicked.connect(lambda: (self.tb.check_all(False), self._update_count()))
        for b in (b_pct, b_reload, b_all, b_none):
            hb.addWidget(b)
        ll.addLayout(hb)

        self.tb = CheckParamTable(value_label="Nilai acuan")
        self.tb.itemChanged.connect(lambda _: self._update_count())
        ll.addWidget(self.tb, 1)
        self.lb_count = QLabel("")
        ll.addWidget(self.lb_count)

        hr = QHBoxLayout()
        self.bt_run = QPushButton("Jalankan analisis")
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
        self.tv = QTableView(); self.model = DataFrameModel(); self.tv.setModel(self.model)
        self.tabs.addTab(self.tv, "Indeks sensitivitas")
        self.tv_s = QTableView(); self.model_s = DataFrameModel(); self.tv_s.setModel(self.model_s)
        self.tabs.addTab(self.tv_s, "Sampel (X, Y)")
        rl.addWidget(self.tabs)
        he = QHBoxLayout()
        b1 = QPushButton("Simpan indeks")
        b1.clicked.connect(lambda: self.result is not None and save_dataframe_dialog(self, self.result.table, "sensitivitas_indeks.csv"))
        b2 = QPushButton("Simpan sampel")
        b2.clicked.connect(lambda: self.result is not None and save_dataframe_dialog(self, self.result.samples, "sensitivitas_sampel.csv", index=False))
        b3 = QPushButton("Simpan grafik")
        b3.clicked.connect(lambda: self.canvas.save_dialog(self, "sensitivitas.png"))
        for b in (b1, b2, b3):
            he.addWidget(b)
        he.addStretch()
        rl.addLayout(he)
        split.addWidget(right)
        left.setMaximumWidth(600)
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setSizes([560, 640])

    # ------------------------------------------------------------------
    def showEvent(self, ev) -> None:  # noqa: N802
        super().showEvent(ev)
        if not self._populated:
            self.refresh_params()

    def refresh_params(self, force: bool = False) -> None:
        """Isi tabel dari parameter tanaman aktif di tab Pengaturan."""
        try:
            values = self.main.setup_tab.current_crop_params()
        except ValueError as e:
            show_error(self, "Parameter", str(e))
            return
        checked = [d["name"] for d in self._safe_selected()] if (self._populated and not force) else PRESELECT
        self.tb.set_params(values, CROP_PARAM_INFO, self.sp_pct.value(), exclude=NON_CONTINUOUS_PARAMS,
                           preselect=checked)
        self._populated = True
        self._update_count()

    def _safe_selected(self) -> list[dict]:
        try:
            return self.tb.selected()
        except ValueError:
            return []

    def _method_changed(self, m: str) -> None:
        if m == "Morris":
            self.lb_n.setText("Jumlah lintasan (N)")
            self.sp_n.setValue(10)
        elif m == "Sobol":
            self.lb_n.setText("N dasar Sobol (pangkat 2)")
            self.sp_n.setValue(64)
        else:
            self.lb_n.setText("N per parameter eFAST (> 64)")
            self.sp_n.setValue(72)
        self._update_count()

    def _update_count(self) -> None:
        k = len(self._safe_selected())
        n = sample_count(self.cb_method.currentText(), k, int(self.sp_n.value()))
        w = max(1, int(self.sp_workers.value()))
        self.lb_count.setText(f"{k} parameter terpilih -> {n} simulasi (perkiraan ~{n * 0.15 / w + (3 if w > 1 else 0):.0f} detik, {w} proses)")

    def run(self) -> None:
        try:
            sel = self.tb.selected()
        except ValueError as e:
            show_error(self, "Parameter", str(e))
            return
        if len(sel) < 2:
            show_error(self, "Parameter", "Pilih minimal 2 parameter.")
            return
        runner = self.main.get_runner()
        if runner is None:
            return
        names = [d["name"] for d in sel]
        bounds = [(d["lo"], d["hi"]) for d in sel]
        target = self.cb_target.currentData()
        method = self.cb_method.currentText()
        n = int(self.sp_n.value())
        seed = int(self.sp_seed.value())
        nw = int(self.sp_workers.value())
        if method == "Sobol" and (n & (n - 1)) != 0:
            show_error(self, "Sobol", "N dasar Sobol sebaiknya pangkat 2 (mis. 32, 64, 128, 256).")
            return

        if method == "eFAST" and n <= 64:
            show_error(self, "eFAST", "N per parameter eFAST harus > 64 (mis. 72, 100, 129).")
            return

        def job(progress, cancelled):
            if method == "Morris":
                return run_morris(runner, names, bounds, target, n_trajectories=n, progress=progress,
                                  cancelled=cancelled, seed=seed, n_workers=nw)
            if method == "eFAST":
                return run_fast(runner, names, bounds, target, n_base=n, progress=progress,
                                cancelled=cancelled, seed=seed, n_workers=nw)
            return run_sobol(runner, names, bounds, target, n_base=n, progress=progress,
                             cancelled=cancelled, seed=seed, n_workers=nw)

        self.main.start_worker(job, self._done, f"Sensitivitas {method} ({len(names)} parameter)")

    def _done(self, res: SensitivityResult) -> None:
        self.result = res
        self.model.set_df(res.table)
        self.tv.resizeColumnsToContents()
        self.model_s.set_df(res.samples)
        if res.n_failed:
            self.main.log(f"Sensitivitas: {res.n_failed} simulasi gagal (diisi rata-rata).")
        self.main.log(f"Sensitivitas {res.method} selesai. Parameter paling berpengaruh pada {res.target}: "
                      f"{', '.join(res.table.index[:3])}")
        self._plot(res)
        self.tabs.setCurrentIndex(0)

    def _plot(self, res: SensitivityResult) -> None:
        self.canvas.clear()
        t = res.table
        if res.method == "Morris":
            ax1 = self.canvas.fig.add_subplot(121)
            y = np.arange(len(t))[::-1]
            ax1.barh(y, t["mu_star"], xerr=t["mu_star_conf"], color="#3b7dd8", capsize=3)
            ax1.set_yticks(y); ax1.set_yticklabels(t.index, fontsize=8)
            ax1.set_xlabel("mu* (efek elementer rata-rata absolut)")
            ax1.set_title(f"Morris - target {res.target}", fontsize=10)
            ax1.grid(alpha=0.3, axis="x")
            ax2 = self.canvas.fig.add_subplot(122)
            ax2.scatter(t["mu_star"], t["sigma"], color="#d8583b")
            for name, row in t.iterrows():
                ax2.annotate(name, (row["mu_star"], row["sigma"]), fontsize=8, xytext=(3, 3), textcoords="offset points")
            lim = max(float(t["mu_star"].max()), float(t["sigma"].max()), 1e-9)
            ax2.plot([0, lim], [0, lim], "k--", lw=0.8, alpha=0.5)
            ax2.set_xlabel("mu*"); ax2.set_ylabel("sigma (interaksi / non-linearitas)")
            ax2.set_title("mu* vs sigma", fontsize=10)
            ax2.grid(alpha=0.3)
        else:
            ax = self.canvas.fig.add_subplot(111)
            y = np.arange(len(t))[::-1]
            h = 0.38
            ax.barh(y + h / 2, t["S1"], height=h, xerr=t["S1_conf"], color="#3b7dd8", capsize=2, label="S1 (orde-1)")
            ax.barh(y - h / 2, t["ST"], height=h, xerr=t["ST_conf"], color="#d8583b", capsize=2, label="ST (total)")
            ax.set_yticks(y); ax.set_yticklabels(t.index, fontsize=8)
            ax.set_xlabel("Indeks Sobol")
            ax.set_title(f"{res.method} - target {res.target}", fontsize=10)
            ax.legend(); ax.grid(alpha=0.3, axis="x")
        self.canvas.draw()
