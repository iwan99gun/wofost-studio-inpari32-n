"""Tab Hasil: ringkasan, grafik variabel harian, tabel, ekspor."""
from __future__ import annotations

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QSplitter, QTableView, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

from ..core.simulation import DAILY_VARS, SUMMARY_VARS, SimulationResult
from .widgets import DataFrameModel, MplCanvas, fmt_num, save_dataframe_dialog

DEFAULT_PLOT_VARS = ["LAI", "TAGP", "TWSO", "SM"]


class ResultsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.result: SimulationResult | None = None
        self._build()

    def _build(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        split = QSplitter(Qt.Orientation.Horizontal)
        lay.addWidget(split)

        # kiri: ringkasan + pilihan variabel
        left = QWidget()
        ll = QVBoxLayout(left)
        gs = QGroupBox("Ringkasan simulasi")
        vs = QVBoxLayout(gs)
        self.tb_summary = QTableWidget(0, 2)
        self.tb_summary.setHorizontalHeaderLabels(["Variabel", "Nilai"])
        self.tb_summary.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tb_summary.verticalHeader().setVisible(False)
        self.tb_summary.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        vs.addWidget(self.tb_summary)
        ll.addWidget(gs, 3)

        gv = QGroupBox("Variabel yang digambar")
        vv = QVBoxLayout(gv)
        self.ls_vars = QListWidget()
        self.ls_vars.itemChanged.connect(lambda _: self.redraw())
        vv.addWidget(self.ls_vars)
        ll.addWidget(gv, 3)

        gb = QGroupBox("Ekspor")
        vb = QVBoxLayout(gb)
        b1 = QPushButton("Simpan tabel harian (CSV/Excel)")
        b1.clicked.connect(self._export_daily)
        b2 = QPushButton("Simpan ringkasan (CSV/Excel)")
        b2.clicked.connect(self._export_summary)
        b3 = QPushButton("Simpan grafik (PNG/SVG/PDF)")
        b3.clicked.connect(lambda: self.canvas.save_dialog(self, "hasil_simulasi.png"))
        for b in (b1, b2, b3):
            vb.addWidget(b)
        ll.addWidget(gb)
        split.addWidget(left)

        # kanan: grafik / tabel
        self.tabs = QTabWidget()
        self.canvas = MplCanvas(self)
        self.tabs.addTab(self.canvas, "Grafik")
        self.tv_daily = QTableView()
        self.model_daily = DataFrameModel()
        self.tv_daily.setModel(self.model_daily)
        self.tabs.addTab(self.tv_daily, "Tabel harian")
        split.addWidget(self.tabs)
        left.setMaximumWidth(420)
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setSizes([340, 900])

        self.lb_info = QLabel("Belum ada hasil. Jalankan simulasi di tab Pengaturan.")
        self.lb_info.setStyleSheet("color:#555;")
        ll.addWidget(self.lb_info)

    # ------------------------------------------------------------------
    def show_result(self, res: SimulationResult) -> None:
        self.result = res
        # ringkasan
        self.tb_summary.setRowCount(0)
        s = res.summary
        order = ["TWSO", "TAGP", "LAIMAX", "TWLV", "TWST", "TWRT", "CTRAT", "CEVST", "RD", "DVS",
                 "DOS", "DOE", "DOA", "DOM", "DOH", "DOV", "DURASI_HARI"]
        names = {"DOS": "Tanggal tanam", "DOE": "Tanggal emergensi", "DOA": "Tanggal antesis",
                 "DOM": "Tanggal masak", "DOH": "Tanggal panen", "DOV": "Tanggal vernalisasi"}
        for k in order + [k for k in s if k not in order]:
            if k not in s:
                continue
            r = self.tb_summary.rowCount()
            self.tb_summary.insertRow(r)
            label = SUMMARY_VARS.get(k, names.get(k, k))
            it = QTableWidgetItem(f"{k}")
            it.setToolTip(label)
            self.tb_summary.setItem(r, 0, it)
            self.tb_summary.setItem(r, 1, QTableWidgetItem(fmt_num(s[k], 6)))
        self.tb_summary.resizeRowsToContents()
        # variabel
        prev = self.selected_vars() or DEFAULT_PLOT_VARS
        self.ls_vars.blockSignals(True)
        self.ls_vars.clear()
        for col in res.daily.columns:
            it = QListWidgetItem(f"{col}  -  {DAILY_VARS.get(col, '')}")
            it.setData(Qt.ItemDataRole.UserRole, col)
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            it.setCheckState(Qt.CheckState.Checked if col in prev else Qt.CheckState.Unchecked)
            self.ls_vars.addItem(it)
        self.ls_vars.blockSignals(False)
        self.model_daily.set_df(res.daily)
        self.tv_daily.resizeColumnsToContents()
        cfg = res.config
        ov = f", override: {', '.join(f'{k}={fmt_num(v)}' for k, v in cfg.crop_overrides.items())}" if cfg.crop_overrides else ""
        self.lb_info.setText(f"{cfg.model_name} | {cfg.crop_name}/{cfg.variety_name} | "
                             f"{cfg.crop_start_date} ({cfg.crop_start_type}) - {cfg.crop_end_date} ({cfg.crop_end_type})"
                             f" | {len(res.daily)} hari, {res.runtime_s:.2f} s{ov}")
        self.redraw()

    def selected_vars(self) -> list[str]:
        out = []
        for i in range(self.ls_vars.count()):
            it = self.ls_vars.item(i)
            if it.checkState() == Qt.CheckState.Checked:
                out.append(it.data(Qt.ItemDataRole.UserRole))
        return out

    def redraw(self) -> None:
        self.canvas.clear()
        if self.result is None:
            self.canvas.draw()
            return
        vars_ = [v for v in self.selected_vars() if v in self.result.daily.columns]
        df = self.result.daily
        if not vars_:
            self.canvas.draw()
            return
        n = len(vars_)
        ncols = 2 if n > 1 else 1
        nrows = (n + ncols - 1) // ncols
        for i, v in enumerate(vars_, 1):
            ax = self.canvas.fig.add_subplot(nrows, ncols, i)
            ax.plot(df.index, df[v], lw=1.6)
            ax.set_title(f"{v} - {DAILY_VARS.get(v, '')}", fontsize=9)
            ax.grid(alpha=0.3)
            ax.tick_params(axis="x", labelrotation=30, labelsize=8)
            ax.tick_params(axis="y", labelsize=8)
            s = self.result.summary
            for key, style in (("DOA", ":"), ("DOM", "--")):
                d = s.get(key)
                if d is not None:
                    ax.axvline(pd.Timestamp(d), color="gray", ls=style, lw=0.9)
        self.canvas.draw()

    # ------------------------------------------------------------------
    def _export_daily(self) -> None:
        if self.result is not None:
            save_dataframe_dialog(self, self.result.daily, "hasil_harian.csv")

    def _export_summary(self) -> None:
        if self.result is not None:
            df = pd.DataFrame([self.result.summary])
            save_dataframe_dialog(self, df, "ringkasan.csv", index=False)
