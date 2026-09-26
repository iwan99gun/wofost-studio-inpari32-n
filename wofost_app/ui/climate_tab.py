"""Tab Skenario iklim: gelombang panas, perubahan hujan/radiasi/CO2, kurva kerentanan hasil."""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDateEdit, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QPushButton, QSpinBox, QSplitter, QTableView, QTableWidget, QTableWidgetItem, QTabWidget,
    QVBoxLayout, QWidget,
)

from ..core.climate import ClimateScenario, ScenarioSet, heatwave_sweep, run_scenarios
from .widgets import DataFrameModel, MplCanvas, from_qdate, save_dataframe_dialog, show_error, to_qdate

COLS = ["Nama", "Mulai", "Selesai", "dTmax [C]", "dTmin [C]", "Faktor hujan", "Faktor radiasi", "CO2 [ppm]"]


class ScenarioTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(0, len(COLS), parent)
        self.setHorizontalHeaderLabels(COLS)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

    def add_scenario(self, sc: ClimateScenario, season: tuple[dt.date, dt.date]) -> None:
        r = self.rowCount()
        self.insertRow(r)
        self.setItem(r, 0, QTableWidgetItem(sc.name))
        for c, d in ((1, sc.start or season[0]), (2, sc.end or season[1])):
            de = QDateEdit(to_qdate(d)); de.setCalendarPopup(True); de.setDisplayFormat("yyyy-MM-dd")
            self.setCellWidget(r, c, de)
        for c, val, rng, dec in ((3, sc.d_tmax, (-10, 15), 1), (4, sc.d_tmin, (-10, 15), 1),
                                 (5, sc.rain_factor, (0, 5), 2), (6, sc.irrad_factor, (0, 3), 2)):
            sp = QDoubleSpinBox(); sp.setRange(*rng); sp.setDecimals(dec); sp.setSingleStep(0.5 if dec == 1 else 0.1); sp.setValue(val)
            self.setCellWidget(r, c, sp)
        sp = QDoubleSpinBox(); sp.setRange(0, 2000); sp.setDecimals(0); sp.setSpecialValueText("(tidak diubah)"); sp.setValue(sc.co2 or 0)
        self.setCellWidget(r, 7, sp)

    def remove_selected(self) -> None:
        rows = sorted({i.row() for i in self.selectedIndexes()}, reverse=True) or ([self.currentRow()] if self.currentRow() >= 0 else [])
        for r in rows:
            self.removeRow(r)

    def scenarios(self) -> list[ClimateScenario]:
        out = []
        for r in range(self.rowCount()):
            co2 = self.cellWidget(r, 7).value()
            out.append(ClimateScenario(
                name=self.item(r, 0).text().strip() or f"Skenario {r + 1}",
                start=from_qdate(self.cellWidget(r, 1).date()), end=from_qdate(self.cellWidget(r, 2).date()),
                d_tmax=self.cellWidget(r, 3).value(), d_tmin=self.cellWidget(r, 4).value(),
                rain_factor=self.cellWidget(r, 5).value(), irrad_factor=self.cellWidget(r, 6).value(),
                co2=co2 if co2 > 0 else None))
        return out


class ClimateTab(QWidget):
    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self.result: ScenarioSet | None = None
        self._build()

    def _build(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        split = QSplitter(Qt.Orientation.Horizontal)
        lay.addWidget(split)
        left = QWidget()
        ll = QVBoxLayout(left)

        gs = QGroupBox("Daftar skenario (relatif terhadap cuaca yang dimuat)")
        vs = QVBoxLayout(gs)
        self.tb = ScenarioTable()
        vs.addWidget(self.tb)
        hb = QHBoxLayout()
        b_add = QPushButton("Tambah"); b_add.clicked.connect(self._add_default)
        b_del = QPushButton("Hapus"); b_del.clicked.connect(self.tb.remove_selected)
        b_clear = QPushButton("Kosongkan"); b_clear.clicked.connect(lambda: self.tb.setRowCount(0))
        for b in (b_add, b_del, b_clear):
            hb.addWidget(b)
        hb.addStretch()
        vs.addLayout(hb)
        ll.addWidget(gs, 2)

        gw = QGroupBox("Generator sweep gelombang panas")
        fw = QFormLayout(gw)
        self.sp_d0 = QDoubleSpinBox(); self.sp_d0.setRange(-10, 15); self.sp_d0.setValue(1); self.sp_d0.setSuffix(" C")
        self.sp_d1 = QDoubleSpinBox(); self.sp_d1.setRange(-10, 15); self.sp_d1.setValue(6); self.sp_d1.setSuffix(" C")
        self.sp_ds = QDoubleSpinBox(); self.sp_ds.setRange(0.1, 5); self.sp_ds.setValue(1); self.sp_ds.setSuffix(" C")
        self.sp_ratio = QDoubleSpinBox(); self.sp_ratio.setRange(0, 1); self.sp_ratio.setSingleStep(0.1); self.sp_ratio.setValue(0.5)
        self.sp_ratio.setToolTip("dTmin = rasio x dTmax (malam memanas lebih sedikit)")
        self.cb_anchor = QComboBox(); self.cb_anchor.addItem("Antesis (DOA) baseline", "DOA"); self.cb_anchor.addItem("Masak (DOM) baseline", "DOM")
        self.cb_anchor.addItem("Tanggal tetap", "fixed")
        self.sp_before = QSpinBox(); self.sp_before.setRange(0, 120); self.sp_before.setValue(7)
        self.sp_after = QSpinBox(); self.sp_after.setRange(0, 120); self.sp_after.setValue(7)
        self.de_fs = QDateEdit(to_qdate(dt.date.today())); self.de_fe = QDateEdit(to_qdate(dt.date.today()))
        for de in (self.de_fs, self.de_fe):
            de.setCalendarPopup(True); de.setDisplayFormat("yyyy-MM-dd")
        fw.addRow("dTmax dari", self.sp_d0); fw.addRow("dTmax sampai", self.sp_d1); fw.addRow("Langkah", self.sp_ds)
        fw.addRow("Rasio dTmin/dTmax", self.sp_ratio)
        fw.addRow("Jendela relatif terhadap", self.cb_anchor)
        fw.addRow("Hari sebelum", self.sp_before); fw.addRow("Hari sesudah", self.sp_after)
        fw.addRow("Tanggal tetap mulai", self.de_fs); fw.addRow("Tanggal tetap selesai", self.de_fe)
        b_sweep = QPushButton("Tambahkan sweep ke daftar")
        b_sweep.clicked.connect(self._add_sweep)
        fw.addRow(b_sweep)
        ll.addWidget(gw)

        gst = QGroupBox("Pasca-proses sterilitas panas empiris (opsional, tipe Horie 1993 / ORYZA v3)")
        fst = QFormLayout(gst)
        self.cb_ster = QCheckBox("Hitung TWSO_sterilitas = TWSO x (1 - sterilitas)")
        self.cb_ster.setChecked(True)
        self.sp_st_before = QSpinBox(); self.sp_st_before.setRange(0, 30); self.sp_st_before.setValue(5)
        self.sp_st_after = QSpinBox(); self.sp_st_after.setRange(0, 30); self.sp_st_after.setValue(5)
        self.sp_st_a = QDoubleSpinBox(); self.sp_st_a.setRange(0.05, 5); self.sp_st_a.setDecimals(3); self.sp_st_a.setValue(0.853)
        self.sp_st_t50 = QDoubleSpinBox(); self.sp_st_t50.setRange(25, 45); self.sp_st_t50.setDecimals(1); self.sp_st_t50.setValue(36.6); self.sp_st_t50.setSuffix(" C")
        fst.addRow(self.cb_ster)
        fst.addRow("Hari sebelum antesis", self.sp_st_before); fst.addRow("Hari sesudah antesis", self.sp_st_after)
        self.sp_st_t50.setToolTip("T50 semi-letal: 36.6 C baku ORYZA/APSIM-Oryza; 34.9-43.2 C antar varietas (Sun et al. 2025)")
        fst.addRow("Kemiringan a", self.sp_st_a); fst.addRow("Tmax 50 % steril (T50)", self.sp_st_t50)
        ll.addWidget(gst)
        note = QLabel("WOFOST 7.x merespons suhu lewat fenologi, fotosintesis (AMAXTB/TMPFTB), respirasi, dan ET0; "
                      "tidak ada modul sterilitas panas (Zheng et al. 2025, GMD), jadi dampak heatwave WOFOST murni "
                      "adalah batas bawah. Fungsi logistik sterilitas vs Tmax rata-rata saat pembungaan bersifat empiris.")
        note.setWordWrap(True); note.setStyleSheet("color:#7a4b00;")
        ll.addWidget(note)

        hr = QHBoxLayout()
        self.bt_run = QPushButton("Jalankan skenario")
        self.bt_run.setStyleSheet("font-weight:bold; padding:6px;")
        self.bt_run.clicked.connect(self.run)
        self.bt_cancel = QPushButton("Batal"); self.bt_cancel.clicked.connect(lambda: self.main.cancel_worker())
        hr.addWidget(self.bt_run); hr.addWidget(self.bt_cancel)
        ll.addLayout(hr)
        split.addWidget(left)

        right = QWidget()
        rl = QVBoxLayout(right)
        self.tabs = QTabWidget()
        self.canvas = MplCanvas(self)
        self.tabs.addTab(self.canvas, "Grafik")
        self.tv = QTableView(); self.model = DataFrameModel(); self.tv.setModel(self.model)
        self.tabs.addTab(self.tv, "Tabel skenario")
        rl.addWidget(self.tabs)
        he = QHBoxLayout()
        b1 = QPushButton("Simpan tabel"); b1.clicked.connect(lambda: self.result is not None and save_dataframe_dialog(self, self.result.table, "skenario_iklim.csv", index=False))
        b2 = QPushButton("Simpan deret harian"); b2.clicked.connect(self._export_daily)
        b3 = QPushButton("Simpan grafik"); b3.clicked.connect(lambda: self.canvas.save_dialog(self, "skenario_iklim.png"))
        for b in (b1, b2, b3):
            he.addWidget(b)
        he.addStretch()
        rl.addLayout(he)
        split.addWidget(right)
        left.setMaximumWidth(620)
        split.setStretchFactor(0, 0); split.setStretchFactor(1, 1)
        split.setSizes([560, 700])

    # ------------------------------------------------------------------
    def _season(self) -> tuple[dt.date, dt.date]:
        try:
            cfg = self.main.setup_tab.collect_config()
            return cfg.crop_start_date, cfg.crop_end_date
        except Exception:  # noqa: BLE001
            t = dt.date.today()
            return t, t + dt.timedelta(days=120)

    def _add_default(self) -> None:
        s = self._season()
        self.tb.add_scenario(ClimateScenario(name=f"Skenario {self.tb.rowCount() + 1}", start=s[0], end=s[1], d_tmax=2.0, d_tmin=1.0), s)

    def _add_sweep(self) -> None:
        runner = self.main.get_runner()
        if runner is None:
            return
        d0, d1, ds = self.sp_d0.value(), self.sp_d1.value(), self.sp_ds.value()
        if d1 < d0:
            show_error(self, "Sweep", "dTmax 'sampai' harus >= 'dari'.")
            return
        values = list(np.round(np.arange(d0, d1 + 1e-9, ds), 2))
        anchor = self.cb_anchor.currentData()
        try:
            if anchor == "fixed":
                scs = heatwave_sweep(runner.cfg, runner.wdp, values, d_tmin_ratio=self.sp_ratio.value(),
                                     fixed_start=from_qdate(self.de_fs.date()), fixed_end=from_qdate(self.de_fe.date()))
            else:
                scs = heatwave_sweep(runner.cfg, runner.wdp, values, self.sp_before.value(), self.sp_after.value(),
                                     relative_to=anchor, d_tmin_ratio=self.sp_ratio.value())
        except Exception as e:  # noqa: BLE001
            show_error(self, "Sweep", f"{type(e).__name__}: {e}")
            return
        s = (runner.cfg.crop_start_date, runner.cfg.crop_end_date)
        for sc in scs:
            self.tb.add_scenario(sc, s)
        self.main.log(f"Sweep heatwave ditambahkan: {len(scs)} skenario, jendela {scs[0].start}..{scs[0].end}.")

    def run(self) -> None:
        scs = self.tb.scenarios()
        if not scs:
            show_error(self, "Skenario", "Tambahkan minimal satu skenario.")
            return
        runner = self.main.get_runner()
        if runner is None:
            return
        cfg, wdp = runner.cfg, runner.wdp
        ster = None
        if self.cb_ster.isChecked():
            ster = {"days_before": int(self.sp_st_before.value()), "days_after": int(self.sp_st_after.value()),
                    "a": float(self.sp_st_a.value()), "t50": float(self.sp_st_t50.value())}

        def job(progress, cancelled):
            return run_scenarios(cfg, wdp, scs, progress=progress, cancelled=cancelled, sterility=ster)

        self.main.start_worker(job, self._done, f"Skenario iklim ({len(scs)} skenario)")

    def _done(self, res: ScenarioSet) -> None:
        self.result = res
        self.model.set_df(res.table); self.tv.resizeColumnsToContents()
        ok = res.table[res.table["status"] == "OK"]
        if len(ok) > 1:
            worst = ok.iloc[1:].loc[ok.iloc[1:]["dTWSO_%"].idxmin()]
            self.main.log(f"Skenario selesai. Baseline TWSO {res.baseline.summary['TWSO']:.0f} kg/ha; "
                          f"dampak terbesar: {worst['skenario']} ({worst['dTWSO_%']:+.1f} %).")
        self._plot(res)
        self.tabs.setCurrentIndex(0)

    def _plot(self, res: ScenarioSet) -> None:
        self.canvas.clear()
        fig = self.canvas.fig
        runs = [r for r in res.runs if r.result is not None]
        colors = [f"C{i % 10}" for i in range(len(runs) + 1)]

        ax1 = fig.add_subplot(2, 2, 1)
        ax1.plot(res.baseline.daily.index, res.baseline.daily["TWSO"], "k-", lw=2, label="Baseline")
        for i, r in enumerate(runs[:12]):
            ax1.plot(r.result.daily.index, r.result.daily["TWSO"], lw=1.2, color=colors[i], label=r.scenario.name)
        ax1.set_title("TWSO [kg/ha]", fontsize=9); ax1.grid(alpha=0.3); ax1.legend(fontsize=6, ncol=2)
        ax1.tick_params(axis="x", labelrotation=30, labelsize=8)

        ax2 = fig.add_subplot(2, 2, 2)
        ax2.plot(res.baseline.daily.index, res.baseline.daily["LAI"], "k-", lw=2)
        for i, r in enumerate(runs[:12]):
            ax2.plot(r.result.daily.index, r.result.daily["LAI"], lw=1.2, color=colors[i])
        ax2.set_title("LAI [-]", fontsize=9); ax2.grid(alpha=0.3)
        ax2.tick_params(axis="x", labelrotation=30, labelsize=8)

        ax3 = fig.add_subplot(2, 2, 3)
        sweep = res.table[(res.table["status"] == "OK") & res.table["skenario"].str.startswith("sweep")]
        if len(sweep) >= 2:
            ax3.plot(sweep["d_tmax"], sweep["dTWSO_%"], "o-", color="#d8583b", label="TWSO (WOFOST)")
            ax3.plot(sweep["d_tmax"], sweep["dTAGP_%"], "s--", color="#3b7dd8", label="TAGP")
            if "dTWSO_sterilitas_%" in sweep.columns and sweep["dTWSO_sterilitas_%"].notna().any():
                ax3.plot(sweep["d_tmax"], sweep["dTWSO_sterilitas_%"], "^-", color="#7a4b00", label="TWSO + sterilitas empiris")
            ax3.axhline(0, color="k", lw=0.8)
            ax3.set_xlabel("dTmax gelombang panas [C]"); ax3.set_ylabel("Perubahan vs baseline [%]")
            ax3.set_title("Kurva kerentanan hasil", fontsize=9); ax3.legend(fontsize=7)
        else:
            ok = res.table[res.table["status"] == "OK"].iloc[1:]
            y = np.arange(len(ok))[::-1]
            ax3.barh(y, ok["dTWSO_%"], color=["#d8583b" if v < 0 else "#3b7dd8" for v in ok["dTWSO_%"]])
            ax3.set_yticks(y); ax3.set_yticklabels(ok["skenario"], fontsize=7)
            ax3.axvline(0, color="k", lw=0.8); ax3.set_xlabel("dTWSO vs baseline [%]")
            ax3.set_title("Dampak per skenario", fontsize=9)
        ax3.grid(alpha=0.3)

        ax4 = fig.add_subplot(2, 2, 4)
        wb = res.weather.get("Baseline")
        if wb is not None and not wb.empty:
            ax4.plot(wb.index, wb["TMAX"], "k-", lw=1, label="TMAX baseline")
            strongest = max(runs, key=lambda r: abs(r.scenario.d_tmax), default=None)
            if strongest is not None and strongest.scenario.name in res.weather:
                w = res.weather[strongest.scenario.name]
                ax4.plot(w.index, w["TMAX"], color="#d8583b", lw=1, label=f"TMAX {strongest.scenario.name}")
            doa = res.baseline.summary.get("DOA")
            if doa:
                ax4.axvline(pd.Timestamp(doa), color="gray", ls=":", lw=1, label="Antesis baseline")
            ax4.set_ylabel("TMAX [C]"); ax4.legend(fontsize=7)
        ax4.set_title("Cuaca: TMAX", fontsize=9); ax4.grid(alpha=0.3)
        ax4.tick_params(axis="x", labelrotation=30, labelsize=8)
        self.canvas.draw()

    def _export_daily(self) -> None:
        if self.result is None:
            return
        frames = [self.result.baseline.daily[["TWSO", "TAGP", "LAI", "DVS"]].add_prefix("Baseline_")]
        for r in self.result.runs:
            if r.result is not None:
                frames.append(r.result.daily[["TWSO", "TAGP", "LAI", "DVS"]].add_prefix(f"{r.scenario.name}_"))
        save_dataframe_dialog(self, pd.concat(frames, axis=1), "skenario_harian.csv")
