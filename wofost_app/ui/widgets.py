"""Widget bersama: kanvas matplotlib, tabel parameter, model DataFrame, dsb."""
from __future__ import annotations

import datetime as dt
import math

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
import pandas as pd  # noqa: E402
from PySide6.QtCore import QAbstractTableModel, QDate, QModelIndex, Qt  # noqa: E402
from PySide6.QtGui import QColor  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QAbstractItemView, QCheckBox, QComboBox, QDateEdit, QDialog, QDialogButtonBox, QDoubleSpinBox, QFileDialog,
    QFormLayout, QHBoxLayout, QHeaderView, QMessageBox, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from ..core.config import FertilizerEvent, IrrigationEvent

CHANGED_BG = QColor(255, 244, 200)


# ---------------------------------------------------------------------------
# util
# ---------------------------------------------------------------------------
def to_qdate(d: dt.date) -> QDate:
    return QDate(d.year, d.month, d.day)


def from_qdate(q: QDate) -> dt.date:
    return dt.date(q.year(), q.month(), q.day())


def fmt_num(v, digits: int = 4) -> str:
    if v is None:
        return ""
    if isinstance(v, (dt.date, dt.datetime, pd.Timestamp)):
        return pd.Timestamp(v).strftime("%Y-%m-%d")
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, (int,)) and not isinstance(v, bool):
        return str(v)
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    if math.isnan(f):
        return "NaN"
    if f == 0:
        return "0"
    if abs(f) >= 1e5 or abs(f) < 1e-3:
        return f"{f:.{digits}g}"
    if float(f).is_integer() and abs(f) < 1e9:
        return f"{f:.0f}"
    return f"{f:.{digits}g}"


def show_error(parent, title: str, message: str) -> None:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Critical)
    box.setWindowTitle(title)
    lines = message.strip().splitlines()
    box.setText(lines[0] if lines else title)
    if len(lines) > 1:
        box.setDetailedText(message)
    box.exec()


def save_dataframe_dialog(parent, df: pd.DataFrame, default_name: str, index: bool = True) -> str | None:
    path, flt = QFileDialog.getSaveFileName(
        parent, "Simpan tabel", default_name, "CSV (*.csv);;Excel (*.xlsx)")
    if not path:
        return None
    try:
        if path.lower().endswith(".xlsx") or "xlsx" in flt and not path.lower().endswith(".csv"):
            if not path.lower().endswith(".xlsx"):
                path += ".xlsx"
            out = df.copy()
            if isinstance(out.index, pd.DatetimeIndex):
                out.index = out.index.tz_localize(None)
            out.to_excel(path, index=index)
        else:
            if not path.lower().endswith(".csv"):
                path += ".csv"
            df.to_csv(path, index=index)
    except Exception as e:  # noqa: BLE001
        show_error(parent, "Gagal menyimpan", f"{type(e).__name__}: {e}")
        return None
    return path


# ---------------------------------------------------------------------------
# Matplotlib
# ---------------------------------------------------------------------------
JOURNAL_WIDTHS = {"1 kolom (90 mm)": 90.0, "1.5 kolom (140 mm)": 140.0, "2 kolom (190 mm)": 190.0}


class JournalExportDialog(QDialog):
    """Pengaturan ekspor figur gaya jurnal (Elsevier: 90/140/190 mm, >= 300 dpi, font 7-9 pt)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ekspor figur gaya jurnal")
        f = QFormLayout(self)
        self.cb_width = QComboBox(); self.cb_width.addItems(list(JOURNAL_WIDTHS))
        self.cb_width.setCurrentIndex(2)
        self.sp_height = QDoubleSpinBox(); self.sp_height.setRange(30, 300); self.sp_height.setValue(120); self.sp_height.setSuffix(" mm")
        self.sp_dpi = QSpinBox(); self.sp_dpi.setRange(150, 1200); self.sp_dpi.setValue(1000)
        self.sp_dpi.setToolTip("Elsevier: 300 dpi halftone, 500 dpi kombinasi, 1000 dpi line art (grafik garis)")
        self.cb_fmt = QComboBox(); self.cb_fmt.addItems(["tiff", "png", "pdf", "svg", "eps"])
        self.cb_font = QComboBox(); self.cb_font.addItems(["Arial", "Helvetica", "Times New Roman", "DejaVu Sans"])
        self.sp_font = QDoubleSpinBox(); self.sp_font.setRange(5, 14); self.sp_font.setValue(8); self.sp_font.setSuffix(" pt")
        self.cb_preset = QComboBox()
        self.cb_preset.addItems(["Line art - 1000 dpi", "Kombinasi (garis + raster) - 500 dpi", "Halftone (foto/peta) - 300 dpi"])
        self.cb_preset.currentIndexChanged.connect(lambda i: self.sp_dpi.setValue([1000, 500, 300][i]))
        f.addRow("Lebar", self.cb_width); f.addRow("Tinggi", self.sp_height)
        f.addRow("Jenis figur (Elsevier)", self.cb_preset); f.addRow("Resolusi", self.sp_dpi)
        f.addRow("Format", self.cb_fmt); f.addRow("Font", self.cb_font); f.addRow("Ukuran font", self.sp_font)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        f.addRow(bb)

    def values(self) -> dict:
        return {"width_mm": JOURNAL_WIDTHS[self.cb_width.currentText()], "height_mm": self.sp_height.value(),
                "dpi": int(self.sp_dpi.value()), "fmt": self.cb_fmt.currentText(),
                "font": self.cb_font.currentText(), "fontsize": float(self.sp_font.value())}


def save_figure_journal(fig, path: str, width_mm: float = 190, height_mm: float = 120, dpi: int = 600,
                        fmt: str = "tiff", font: str = "Arial", fontsize: float = 8.0) -> None:
    """Simpan figur dengan ukuran/font jurnal tanpa mengubah tampilan layar secara permanen."""
    import matplotlib
    from matplotlib.text import Text
    old_size = fig.get_size_inches().copy()
    texts = list(fig.findobj(Text))
    old = [(t, t.get_fontsize(), t.get_fontfamily()) for t in texts]
    try:
        fig.set_size_inches(width_mm / 25.4, height_mm / 25.4)
        for t in texts:
            t.set_fontfamily(font)
            t.set_fontsize(fontsize)
        for ax in fig.get_axes():
            ax.title.set_fontsize(fontsize + 1)
            ax.tick_params(labelsize=fontsize - 1)
            leg = ax.get_legend()
            if leg is not None:
                for t in leg.get_texts():
                    t.set_fontsize(fontsize - 1)
        kw = {}
        if fmt == "tiff":
            kw["pil_kwargs"] = {"compression": "tiff_lzw"}
        with matplotlib.rc_context({"pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none"}):
            fig.savefig(path, dpi=dpi, format=fmt, bbox_inches="tight", **kw)
    finally:
        fig.set_size_inches(old_size)
        for t, fs, ff in old:
            t.set_fontsize(fs)
            t.set_fontfamily(ff)
        fig.canvas.draw_idle()


class MplCanvas(QWidget):
    def __init__(self, parent=None, width: float = 7, height: float = 4.5):
        super().__init__(parent)
        self.fig = Figure(figsize=(width, height))
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.bt_journal = QPushButton("Figur jurnal...")
        self.bt_journal.setToolTip("Ekspor TIFF/PDF/SVG dengan lebar kolom jurnal, 600 dpi, font 8 pt")
        self.bt_journal.clicked.connect(lambda: self.export_journal(self))
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.addWidget(self.toolbar, 1)
        top.addWidget(self.bt_journal)
        lay.addLayout(top)
        lay.addWidget(self.canvas)

    def export_journal(self, parent, default_name: str = "figur") -> None:
        dlg = JournalExportDialog(parent)
        if not dlg.exec():
            return
        v = dlg.values()
        path, _ = QFileDialog.getSaveFileName(parent, "Simpan figur jurnal", f"{default_name}.{v['fmt']}",
                                              f"{v['fmt'].upper()} (*.{v['fmt']})")
        if not path:
            return
        if not path.lower().endswith("." + v["fmt"]):
            path += "." + v["fmt"]
        try:
            save_figure_journal(self.fig, path, **v)
        except Exception as e:  # noqa: BLE001
            show_error(parent, "Gagal mengekspor figur", f"{type(e).__name__}: {e}")

    def clear(self) -> None:
        self.fig.clear()

    def draw(self) -> None:
        try:
            self.fig.tight_layout()
        except Exception:  # noqa: BLE001
            pass
        self.canvas.draw_idle()

    def save_dialog(self, parent, default_name: str = "grafik.png") -> None:
        path, _ = QFileDialog.getSaveFileName(parent, "Simpan grafik", default_name,
                                              "PNG (*.png);;SVG (*.svg);;PDF (*.pdf)")
        if path:
            self.fig.savefig(path, dpi=300, bbox_inches="tight")


# ---------------------------------------------------------------------------
# Model tabel pandas (read-only)
# ---------------------------------------------------------------------------
class DataFrameModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame | None = None, parent=None):
        super().__init__(parent)
        self._df = df if df is not None else pd.DataFrame()

    def set_df(self, df: pd.DataFrame) -> None:
        self.beginResetModel()
        self._df = df if df is not None else pd.DataFrame()
        self.endResetModel()

    def df(self) -> pd.DataFrame:
        return self._df

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._df)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._df.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return fmt_num(self._df.iat[index.row(), index.column()], 5)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return str(self._df.columns[section])
        return fmt_num(self._df.index[section])


# ---------------------------------------------------------------------------
# Tabel parameter sederhana (Parameter | Nilai | Keterangan)
# ---------------------------------------------------------------------------
class ParamTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(0, 3, parent)
        self.setHorizontalHeaderLabels(["Parameter", "Nilai", "Keterangan"])
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._info: dict = {}

    def set_params(self, values: dict, info: dict | None = None) -> None:
        self._info = info or {}
        self.setRowCount(0)
        for name, val in values.items():
            r = self.rowCount()
            self.insertRow(r)
            it = QTableWidgetItem(name)
            it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(r, 0, it)
            self.setItem(r, 1, QTableWidgetItem(fmt_num(val, 6)))
            desc = self._info.get(name, "")
            if isinstance(desc, tuple):
                desc = desc[0]
            d = QTableWidgetItem(str(desc))
            d.setFlags(d.flags() & ~Qt.ItemFlag.ItemIsEditable)
            d.setToolTip(str(desc))
            self.setItem(r, 2, d)
        self.resizeColumnsToContents()
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

    def values(self) -> dict[str, float]:
        out = {}
        for r in range(self.rowCount()):
            name = self.item(r, 0).text()
            txt = self.item(r, 1).text().strip().replace(",", ".")
            try:
                out[name] = float(txt)
            except ValueError as e:
                raise ValueError(f"Nilai parameter {name} tidak valid: '{txt}'") from e
        return out

    def set_value(self, name: str, value: float) -> None:
        for r in range(self.rowCount()):
            if self.item(r, 0).text() == name:
                self.item(r, 1).setText(fmt_num(value, 6))
                return


# ---------------------------------------------------------------------------
# Tabel override parameter tanaman (Parameter | Default | Nilai | Keterangan)
# ---------------------------------------------------------------------------
class OverrideTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(0, 4, parent)
        self.setHorizontalHeaderLabels(["Parameter", "Default", "Nilai", "Keterangan"])
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._defaults: dict[str, float] = {}
        self.itemChanged.connect(self._on_changed)

    def set_params(self, defaults: dict[str, float], overrides: dict[str, float], info: dict) -> None:
        self.blockSignals(True)
        self._defaults = dict(defaults)
        self.setRowCount(0)
        for name, val in defaults.items():
            r = self.rowCount()
            self.insertRow(r)
            it = QTableWidgetItem(name)
            it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(r, 0, it)
            d = QTableWidgetItem(fmt_num(val, 6))
            d.setFlags(d.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(r, 1, d)
            cur = overrides.get(name, val)
            self.setItem(r, 2, QTableWidgetItem(fmt_num(cur, 6)))
            desc = info.get(name, "")
            k = QTableWidgetItem(str(desc))
            k.setFlags(k.flags() & ~Qt.ItemFlag.ItemIsEditable)
            k.setToolTip(str(desc))
            self.setItem(r, 3, k)
            self._paint_row(r)
        self.resizeColumnsToContents()
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.blockSignals(False)

    def _paint_row(self, r: int) -> None:
        name = self.item(r, 0).text()
        try:
            changed = abs(float(self.item(r, 2).text().replace(",", ".")) - self._defaults[name]) > 1e-12
        except (ValueError, KeyError):
            changed = True
        for c in range(self.columnCount()):
            self.item(r, c).setBackground(CHANGED_BG if changed else QColor(Qt.GlobalColor.transparent))

    def _on_changed(self, item: QTableWidgetItem) -> None:
        if item.column() == 2:
            self.blockSignals(True)
            self._paint_row(item.row())
            self.blockSignals(False)

    def overrides(self) -> dict[str, float]:
        out = {}
        for r in range(self.rowCount()):
            name = self.item(r, 0).text()
            txt = self.item(r, 2).text().strip().replace(",", ".")
            try:
                v = float(txt)
            except ValueError as e:
                raise ValueError(f"Override parameter {name} tidak valid: '{txt}'") from e
            if abs(v - self._defaults.get(name, v)) > 1e-12:
                out[name] = v
        return out

    def current_values(self) -> dict[str, float]:
        vals = dict(self._defaults)
        vals.update(self.overrides())
        return vals

    def apply_overrides(self, values: dict[str, float]) -> None:
        self.blockSignals(True)
        for r in range(self.rowCount()):
            name = self.item(r, 0).text()
            if name in values:
                self.item(r, 2).setText(fmt_num(values[name], 6))
                self._paint_row(r)
        self.blockSignals(False)

    def reset(self) -> None:
        self.apply_overrides(dict(self._defaults))


# ---------------------------------------------------------------------------
# Tabel parameter dengan centang + rentang (untuk sensitivitas & kalibrasi)
# ---------------------------------------------------------------------------
class CheckParamTable(QTableWidget):
    def __init__(self, parent=None, value_label: str = "Nilai awal"):
        super().__init__(0, 6, parent)
        self.setHorizontalHeaderLabels(["", "Parameter", value_label, "Min", "Maks", "Keterangan"])
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

    def set_params(self, values: dict[str, float], info: dict, pct: float,
                   exclude: set[str] | None = None, preselect: list[str] | None = None) -> None:
        exclude = exclude or set()
        preselect = preselect or []
        self.blockSignals(True)
        self.setRowCount(0)
        for name, val in values.items():
            if name in exclude:
                continue
            r = self.rowCount()
            self.insertRow(r)
            cb = QCheckBox()
            cb.setChecked(name in preselect)
            self.setCellWidget(r, 0, cb)
            it = QTableWidgetItem(name)
            it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(r, 1, it)
            self.setItem(r, 2, QTableWidgetItem(fmt_num(val, 6)))
            lo, hi = self._range(val, pct, name)
            self.setItem(r, 3, QTableWidgetItem(fmt_num(lo, 6)))
            self.setItem(r, 4, QTableWidgetItem(fmt_num(hi, 6)))
            desc = info.get(name, "")
            k = QTableWidgetItem(str(desc))
            k.setFlags(k.flags() & ~Qt.ItemFlag.ItemIsEditable)
            k.setToolTip(str(desc))
            self.setItem(r, 5, k)
        self.resizeColumnsToContents()
        self.setColumnWidth(0, 28)
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.blockSignals(False)

    @staticmethod
    def _range(val: float, pct: float, name: str = "") -> tuple[float, float]:
        if name.endswith("@x"):
            return (-3.0, 3.0)
        if val == 0:
            return (-1.0, 1.0)
        lo, hi = val * (1 - pct / 100.0), val * (1 + pct / 100.0)
        return (min(lo, hi), max(lo, hi))

    def apply_pct(self, pct: float) -> None:
        self.blockSignals(True)
        for r in range(self.rowCount()):
            try:
                val = float(self.item(r, 2).text().replace(",", "."))
            except ValueError:
                continue
            lo, hi = self._range(val, pct, self.item(r, 1).text())
            self.item(r, 3).setText(fmt_num(lo, 6))
            self.item(r, 4).setText(fmt_num(hi, 6))
        self.blockSignals(False)

    def set_checked(self, names: list[str]) -> None:
        for r in range(self.rowCount()):
            self.cellWidget(r, 0).setChecked(self.item(r, 1).text() in names)

    def check_all(self, state: bool) -> None:
        for r in range(self.rowCount()):
            self.cellWidget(r, 0).setChecked(state)

    def selected(self) -> list[dict]:
        out = []
        for r in range(self.rowCount()):
            cb = self.cellWidget(r, 0)
            if cb is None or not cb.isChecked() or any(self.item(r, c) is None for c in (1, 2, 3, 4)):
                continue
            name = self.item(r, 1).text()
            try:
                x0 = float(self.item(r, 2).text().replace(",", "."))
                lo = float(self.item(r, 3).text().replace(",", "."))
                hi = float(self.item(r, 4).text().replace(",", "."))
            except ValueError as e:
                raise ValueError(f"Nilai/rentang parameter {name} tidak valid.") from e
            if hi <= lo:
                raise ValueError(f"Rentang parameter {name}: Maks harus > Min.")
            out.append({"name": name, "x0": x0, "lo": lo, "hi": hi})
        return out


# ---------------------------------------------------------------------------
# Tabel irigasi
# ---------------------------------------------------------------------------
class IrrigationTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(0, 3, parent)
        self.setHorizontalHeaderLabels(["Tanggal", "Jumlah [cm]", "Efisiensi [0-1]"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)

    def add_event(self, ev: IrrigationEvent | None = None) -> None:
        ev = ev or IrrigationEvent(dt.date.today(), 2.0, 0.7)
        r = self.rowCount()
        self.insertRow(r)
        de = QDateEdit(to_qdate(ev.day))
        de.setCalendarPopup(True)
        de.setDisplayFormat("yyyy-MM-dd")
        self.setCellWidget(r, 0, de)
        amt = QDoubleSpinBox()
        amt.setRange(0.0, 100.0)
        amt.setDecimals(2)
        amt.setValue(ev.amount_cm)
        self.setCellWidget(r, 1, amt)
        eff = QDoubleSpinBox()
        eff.setRange(0.01, 1.0)
        eff.setSingleStep(0.05)
        eff.setDecimals(2)
        eff.setValue(ev.efficiency)
        self.setCellWidget(r, 2, eff)

    def remove_selected(self) -> None:
        rows = sorted({i.row() for i in self.selectedIndexes()}, reverse=True)
        if not rows and self.currentRow() >= 0:
            rows = [self.currentRow()]
        for r in rows:
            self.removeRow(r)

    def events(self) -> list[IrrigationEvent]:
        out = []
        for r in range(self.rowCount()):
            out.append(IrrigationEvent(from_qdate(self.cellWidget(r, 0).date()),
                                       float(self.cellWidget(r, 1).value()),
                                       float(self.cellWidget(r, 2).value())))
        return out

    def set_events(self, events: list[IrrigationEvent]) -> None:
        self.setRowCount(0)
        for ev in events:
            self.add_event(ev)


class FertilizationTable(QTableWidget):
    """Jadwal pemupukan N (kg N/ha) untuk model WOFOST 8.1 terbatas N."""

    def __init__(self, parent=None):
        super().__init__(0, 3, parent)
        self.setHorizontalHeaderLabels(["Tanggal", "N [kg N/ha]", "Recovery [0-1]"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)

    def add_event(self, ev: FertilizerEvent | None = None) -> None:
        ev = ev or FertilizerEvent(dt.date.today(), 40.0, 0.5)
        r = self.rowCount()
        self.insertRow(r)
        de = QDateEdit(to_qdate(ev.day)); de.setCalendarPopup(True); de.setDisplayFormat("yyyy-MM-dd")
        self.setCellWidget(r, 0, de)
        amt = QDoubleSpinBox(); amt.setRange(0.0, 500.0); amt.setDecimals(1); amt.setValue(ev.n_kg_ha)
        self.setCellWidget(r, 1, amt)
        rec = QDoubleSpinBox(); rec.setRange(0.01, 1.0); rec.setSingleStep(0.05); rec.setDecimals(2); rec.setValue(ev.recovery)
        rec.setToolTip("Fraksi N pupuk yang masuk ke kolam N tersedia (efisiensi pemulihan pupuk; urea sawah 0,3-0,6)")
        self.setCellWidget(r, 2, rec)

    def remove_selected(self) -> None:
        rows = sorted({i.row() for i in self.selectedIndexes()}, reverse=True)
        if not rows and self.currentRow() >= 0:
            rows = [self.currentRow()]
        for r in rows:
            self.removeRow(r)

    def events(self) -> list[FertilizerEvent]:
        return [FertilizerEvent(from_qdate(self.cellWidget(r, 0).date()), float(self.cellWidget(r, 1).value()),
                                float(self.cellWidget(r, 2).value())) for r in range(self.rowCount())]

    def set_events(self, events: list[FertilizerEvent]) -> None:
        self.setRowCount(0)
        for ev in events:
            self.add_event(ev)
