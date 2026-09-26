"""Tab Batch tanggal tanam: jendela tanam x tahun -> hasil per tanggal tanam."""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDateEdit, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QSpinBox, QSplitter,
    QTableView, QTabWidget, QVBoxLayout, QWidget,
)

from ..core.simulation import run_sowing_batch
from .widgets import DataFrameModel, MplCanvas, from_qdate, save_dataframe_dialog, show_error, to_qdate


def _safe_replace_year(d: dt.date, year: int) -> dt.date:
    try:
        return d.replace(year=year)
    except ValueError:  # 29 Feb
        return d.replace(year=year, day=28)


class BatchTab(QWidget):
    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self.table: pd.DataFrame | None = None
        self.agg: pd.DataFrame | None = None
        self._build()

    def _build(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        split = QSplitter(Qt.Orientation.Horizontal)
        lay.addWidget(split)

        left = QWidget()
        ll = QVBoxLayout(left)
        g = QGroupBox("Jendela tanggal tanam")
        f = QFormLayout(g)
        today = dt.date.today()
        self.de_from = QDateEdit(to_qdate(dt.date(today.year - 1, 10, 1)))
        self.de_to = QDateEdit(to_qdate(dt.date(today.year, 1, 31)))
        for de in (self.de_from, self.de_to):
            de.setCalendarPopup(True)
            de.setDisplayFormat("yyyy-MM-dd")
        self.sp_step = QSpinBox(); self.sp_step.setRange(1, 60); self.sp_step.setValue(10)
        self.sp_y0 = QSpinBox(); self.sp_y0.setRange(1950, 2100); self.sp_y0.setValue(today.year - 5)
        self.sp_y1 = QSpinBox(); self.sp_y1.setRange(1950, 2100); self.sp_y1.setValue(today.year - 1)
        self.sp_dur = QSpinBox(); self.sp_dur.setRange(30, 730); self.sp_dur.setValue(180)
        f.addRow("Tanam dari (tanggal templat)", self.de_from)
        f.addRow("Tanam sampai (tanggal templat)", self.de_to)
        f.addRow("Langkah [hari]", self.sp_step)
        f.addRow("Tahun awal", self.sp_y0)
        f.addRow("Tahun akhir", self.sp_y1)
        f.addRow("Durasi musim maks [hari]", self.sp_dur)
        hint = QLabel("Bulan/hari dari tanggal templat dipakai untuk setiap tahun. Jika 'sampai' lebih awal "
                      "dari 'dari', jendela dianggap melewati pergantian tahun (mis. Okt-Jan). "
                      "Tipe awal/akhir, tanah, dan override mengikuti tab Pengaturan.")
        hint.setWordWrap(True); hint.setStyleSheet("color:#555;")
        f.addRow(hint)
        ll.addWidget(g)

        self.lb_count = QLabel("")
        ll.addWidget(self.lb_count)
        for w in (self.de_from, self.de_to):
            w.dateChanged.connect(self._update_count)
        for w in (self.sp_step, self.sp_y0, self.sp_y1):
            w.valueChanged.connect(self._update_count)
        self._update_count()

        hb = QHBoxLayout()
        self.bt_run = QPushButton("Jalankan batch")
        self.bt_run.setStyleSheet("font-weight:bold; padding:6px;")
        self.bt_run.clicked.connect(self.run)
        self.bt_cancel = QPushButton("Batal")
        self.bt_cancel.clicked.connect(lambda: self.main.cancel_worker())
        hb.addWidget(self.bt_run); hb.addWidget(self.bt_cancel)
        ll.addLayout(hb)

        gv = QGroupBox("Validasi terhadap hasil observasi lapangan")
        vv = QVBoxLayout(gv)
        self.bt_obs = QPushButton("Muat hasil observasi (CSV/Excel)...")
        self.bt_obs.setToolTip("Kolom: tanggal_tanam (YYYY-MM-DD) dan TWSO_obs [kg/ha]; opsional kolom 'lokasi'.\n"
                               "Tanggal tanam harus sama dengan salah satu run batch.")
        self.bt_obs.clicked.connect(self._load_obs)
        vv.addWidget(self.bt_obs)
        self.lb_val = QLabel("Belum ada observasi.")
        self.lb_val.setWordWrap(True); self.lb_val.setStyleSheet("color:#555;")
        vv.addWidget(self.lb_val)
        ll.addWidget(gv)

        ge = QGroupBox("Ekspor")
        ve = QVBoxLayout(ge)
        b1 = QPushButton("Simpan tabel per run")
        b1.clicked.connect(lambda: self.table is not None and save_dataframe_dialog(self, self.table, "batch_tanggal_tanam.csv", index=False))
        b2 = QPushButton("Simpan tabel agregat per tanggal")
        b2.clicked.connect(lambda: self.agg is not None and save_dataframe_dialog(self, self.agg, "batch_agregat.csv", index=False))
        b3 = QPushButton("Simpan grafik")
        b3.clicked.connect(lambda: self.canvas.save_dialog(self, "batch_tanggal_tanam.png"))
        for b in (b1, b2, b3):
            ve.addWidget(b)
        ll.addWidget(ge)
        ll.addStretch()
        split.addWidget(left)

        self.tabs = QTabWidget()
        self.canvas = MplCanvas(self)
        self.tabs.addTab(self.canvas, "Grafik")
        self.tv = QTableView(); self.model = DataFrameModel(); self.tv.setModel(self.model)
        self.tabs.addTab(self.tv, "Tabel per run")
        self.tv_agg = QTableView(); self.model_agg = DataFrameModel(); self.tv_agg.setModel(self.model_agg)
        self.tabs.addTab(self.tv_agg, "Agregat per tanggal")
        self.canvas_val = MplCanvas(self)
        self.tabs.addTab(self.canvas_val, "Validasi 1:1")
        self.tv_val = QTableView(); self.model_val = DataFrameModel(); self.tv_val.setModel(self.model_val)
        self.tabs.addTab(self.tv_val, "Tabel validasi")
        self.obs_yield: pd.DataFrame | None = None
        split.addWidget(self.tabs)
        left.setMaximumWidth(380)
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setSizes([360, 840])

    # ------------------------------------------------------------------ validasi
    def _load_obs(self) -> None:
        p, _ = QFileDialog.getOpenFileName(self, "Muat hasil observasi", "", "Data (*.csv *.xlsx *.xls)")
        if p:
            self.load_obs_file(p)

    def load_obs_file(self, p: str) -> None:
        try:
            df = pd.read_excel(p) if p.lower().endswith((".xlsx", ".xls")) else pd.read_csv(p)
            cols = {c.lower(): c for c in df.columns}
            dcol = cols.get("tanggal_tanam") or cols.get("sowing_date") or cols.get("day")
            ycol = cols.get("twso_obs") or cols.get("twso") or cols.get("yield") or cols.get("hasil")
            if not dcol or not ycol:
                raise ValueError("Butuh kolom 'tanggal_tanam' dan 'TWSO_obs'.")
            df = df.rename(columns={dcol: "tanggal_tanam", ycol: "TWSO_obs"})
            df["tanggal_tanam"] = pd.to_datetime(df["tanggal_tanam"]).dt.date
            df["TWSO_obs"] = pd.to_numeric(df["TWSO_obs"], errors="coerce")
            self.obs_yield = df.dropna(subset=["TWSO_obs"])
        except Exception as e:  # noqa: BLE001
            show_error(self, "Gagal membaca observasi", f"{type(e).__name__}: {e}")
            return
        self.lb_val.setText(f"{p}: {len(self.obs_yield)} observasi hasil.")
        self._validate()

    @staticmethod
    def yield_metrics(o: np.ndarray, s: np.ndarray) -> dict:
        err = s - o
        rmse = float(np.sqrt(np.mean(err ** 2)))
        ss_res = float(np.sum(err ** 2)); ss_tot = float(np.sum((o - o.mean()) ** 2))
        d = 1 - ss_res / float(np.sum((np.abs(s - o.mean()) + np.abs(o - o.mean())) ** 2)) if len(o) > 1 else np.nan
        r = float(np.corrcoef(o, s)[0, 1]) if len(o) > 2 else np.nan
        return {"n": len(o), "RMSE": rmse, "nRMSE_%": 100 * rmse / float(o.mean()) if o.mean() else np.nan,
                "bias": float(err.mean()), "R2": 1 - ss_res / ss_tot if ss_tot > 0 else np.nan,
                "r_pearson": r, "d_Willmott": d, "EF_Nash": 1 - ss_res / ss_tot if ss_tot > 0 else np.nan}

    def _validate(self) -> None:
        if self.obs_yield is None or self.table is None:
            return
        sim = self.table[self.table["status"] == "OK"][["tanggal_tanam", "TWSO"]].rename(columns={"TWSO": "TWSO_sim"})
        m = self.obs_yield.merge(sim, on="tanggal_tanam", how="inner")
        if m.empty:
            self.lb_val.setText("Tidak ada tanggal tanam observasi yang cocok dengan run batch. "
                                "Samakan jendela/langkah batch dengan tanggal tanam observasi.")
            return
        o, s = m["TWSO_obs"].values.astype(float), m["TWSO_sim"].values.astype(float)
        met = self.yield_metrics(o, s)
        m["galat"] = s - o
        m["galat_%"] = 100 * (s - o) / o
        self.model_val.set_df(m); self.tv_val.resizeColumnsToContents()
        txt = (f"n={met['n']}, RMSE={met['RMSE']:.0f} kg/ha, nRMSE={met['nRMSE_%']:.1f} %, bias={met['bias']:+.0f}, "
               f"R2={met['R2']:.3f}, d={met['d_Willmott']:.3f}, EF={met['EF_Nash']:.3f}")
        self.lb_val.setText(txt)
        self.main.log("Validasi hasil: " + txt)
        self.canvas_val.clear()
        ax = self.canvas_val.fig.add_subplot(111)
        lim = [min(o.min(), s.min()) * 0.9, max(o.max(), s.max()) * 1.1]
        ax.plot(lim, lim, "k--", lw=1, label="1:1")
        ax.scatter(o, s, color="#3b7dd8", s=30, zorder=3, label="Musim/tanggal tanam")
        if len(o) > 2:
            b, a = np.polyfit(o, s, 1)
            ax.plot(lim, [a + b * lim[0], a + b * lim[1]], color="#d8583b", lw=1.2, label=f"y = {b:.2f}x + {a:.0f}")
        ax.set_xlim(lim); ax.set_ylim(lim); ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("Hasil observasi [kg/ha]"); ax.set_ylabel("Hasil simulasi WOFOST [kg/ha]")
        ax.set_title(f"Validasi hasil: RMSE {met['RMSE']:.0f} kg/ha, nRMSE {met['nRMSE_%']:.1f} %, R2 {met['R2']:.2f}, d {met['d_Willmott']:.2f}", fontsize=9)
        ax.grid(alpha=0.3); ax.legend(fontsize=8)
        self.canvas_val.draw()
        self.tabs.setCurrentWidget(self.canvas_val)

    # ------------------------------------------------------------------
    def _dates(self) -> list[dt.date]:
        return [d for _, d in self._seasons()]

    def _seasons(self) -> list[tuple[int, dt.date]]:
        """Daftar (musim, tanggal tanam); musim = tahun awal jendela tanam."""
        d0 = from_qdate(self.de_from.date())
        d1 = from_qdate(self.de_to.date())
        step = int(self.sp_step.value())
        out = []
        for y in range(int(self.sp_y0.value()), int(self.sp_y1.value()) + 1):
            s = _safe_replace_year(d0, y)
            e = _safe_replace_year(d1, y)
            if e < s:
                e = _safe_replace_year(d1, y + 1)
            d = s
            while d <= e:
                out.append((y, d))
                d += dt.timedelta(days=step)
        return out

    def _update_count(self) -> None:
        try:
            n = len(self._dates())
        except Exception:  # noqa: BLE001
            n = 0
        self.lb_count.setText(f"Jumlah simulasi: {n}")

    def run(self) -> None:
        runner = self.main.get_runner()
        if runner is None:
            return
        dates = self._dates()
        if not dates:
            show_error(self, "Batch", "Tidak ada tanggal tanam dalam jendela yang dipilih.")
            return
        wdp = runner.wdp
        bad = [d for d in dates if d < wdp.first_date or d + dt.timedelta(days=self.sp_dur.value()) > wdp.last_date]
        if bad:
            show_error(self, "Batch", f"{len(bad)} tanggal berada di luar cakupan data cuaca "
                                      f"({wdp.first_date} s.d. {wdp.last_date}). Sesuaikan tahun/durasi.")
            return
        dur = int(self.sp_dur.value())
        season_of = {d: y for y, d in self._seasons()}

        def job(progress, cancelled):
            table = run_sowing_batch(runner, dates, dur, progress=progress, cancelled=cancelled)
            table.insert(1, "musim", table["tanggal_tanam"].map(season_of))
            return table

        self.main.start_worker(job, self._done, f"Batch {len(dates)} simulasi")

    def _done(self, table: pd.DataFrame) -> None:
        self.table = table
        self.model.set_df(table)
        self.tv.resizeColumnsToContents()
        ok = table[table["status"] == "OK"].copy() if "status" in table else table.copy()
        n_fail = len(table) - len(ok)
        if n_fail:
            self.main.log(f"Batch: {n_fail} simulasi gagal (lihat kolom status).")
        if ok.empty:
            self.agg = None
            self.model_agg.set_df(pd.DataFrame())
            self.canvas.clear(); self.canvas.draw()
            return
        ok["tanggal_templat"] = ok["tanggal_tanam"].apply(lambda d: d.strftime("%m-%d"))
        ok["_ord"] = ok.groupby("musim").cumcount()
        agg = (ok.groupby("tanggal_templat")
                 .agg(_ord=("_ord", "min"), n=("TWSO", "size"), TWSO_mean=("TWSO", "mean"), TWSO_std=("TWSO", "std"),
                      TWSO_min=("TWSO", "min"), TWSO_max=("TWSO", "max"),
                      TAGP_mean=("TAGP", "mean"), LAIMAX_mean=("LAIMAX", "mean"),
                      DURASI_mean=("DURASI_HARI", "mean"))
                 .reset_index().sort_values("_ord").drop(columns="_ord").reset_index(drop=True))
        pos = {t: i for i, t in enumerate(agg["tanggal_templat"])}
        ok["_x"] = ok["tanggal_templat"].map(pos)
        agg["TWSO_cv_%"] = 100 * agg["TWSO_std"] / agg["TWSO_mean"]
        self.agg = agg
        self.model_agg.set_df(agg)
        self.tv_agg.resizeColumnsToContents()
        best = agg.loc[agg["TWSO_mean"].idxmax()]
        self.main.log(f"Batch selesai: hasil rata-rata tertinggi {best['TWSO_mean']:.0f} kg/ha pada tanggal tanam "
                      f"{best['tanggal_templat']} (CV {best['TWSO_cv_%']:.1f}%).")
        # grafik
        self.canvas.clear()
        ax = self.canvas.fig.add_subplot(111)
        years = sorted(ok["musim"].unique())
        for y in years:
            sub = ok[ok["musim"] == y].sort_values("_x")
            ax.plot(sub["_x"], sub["TWSO"], marker="o", ms=3, lw=1, alpha=0.6, label=f"musim {y}")
        if len(years) > 1:
            ax.errorbar(np.arange(len(agg)), agg["TWSO_mean"], yerr=agg["TWSO_std"].fillna(0),
                        color="k", lw=2.2, capsize=3, label="Rata-rata +/- SD")
        ax.set_xticks(np.arange(len(agg)))
        ax.set_xticklabels(agg["tanggal_templat"], rotation=45, fontsize=8)
        ax.set_xlabel("Tanggal tanam (bulan-hari)")
        ax.set_ylabel("TWSO [kg/ha]")
        ax.set_title("Hasil vs tanggal tanam")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7, ncol=2 if len(years) > 6 else 1)
        self.canvas.draw()
        self.tabs.setCurrentIndex(0)
        if self.obs_yield is not None:
            self._validate()
