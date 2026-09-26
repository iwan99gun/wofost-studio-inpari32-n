"""Jendela utama WOFOST Studio."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDockWidget, QFileDialog, QLabel, QMainWindow, QMessageBox, QPlainTextEdit, QProgressBar,
    QPushButton, QTabWidget,
)

from .. import __version__
from ..core.config import SimulationConfig, WeatherConfig
from ..core.simulation import SimulationResult, SimulationRunner
from ..core.weather import build_weather_provider, export_weather_csv_pcse, weather_summary
from .assimilation_tab import AssimilationTab
from .batch_tab import BatchTab
from .calibration_tab import CalibrationTab
from .climate_tab import ClimateTab
from .results_tab import ResultsTab
from .sensitivity_tab import SensitivityTab
from .setup_tab import SetupTab
from .widgets import show_error
from .workers import Worker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"WOFOST Studio {__version__} - Simulasi tanaman PCSE-WOFOST")
        self.resize(1360, 860)

        self.wdp = None
        self.wdp_cfg: WeatherConfig | None = None
        self.worker: Worker | None = None
        self._on_done = None
        self.last_result: SimulationResult | None = None
        self.project_path: str | None = None

        # tab
        self.tabs = QTabWidget()
        self.setup_tab = SetupTab()
        self.results_tab = ResultsTab()
        self.batch_tab = BatchTab(self)
        self.sens_tab = SensitivityTab(self)
        self.calib_tab = CalibrationTab(self)
        self.assim_tab = AssimilationTab(self)
        self.climate_tab = ClimateTab(self)
        self.tabs.addTab(self.setup_tab, "1. Pengaturan")
        self.tabs.addTab(self.results_tab, "2. Hasil simulasi")
        self.tabs.addTab(self.batch_tab, "3. Batch tanggal tanam")
        self.tabs.addTab(self.sens_tab, "4. Analisis sensitivitas")
        self.tabs.addTab(self.calib_tab, "5. Kalibrasi")
        self.tabs.addTab(self.assim_tab, "6. Asimilasi data (EnKF)")
        self.tabs.addTab(self.climate_tab, "7. Skenario iklim")
        self.setCentralWidget(self.tabs)

        self.setup_tab.load_weather_requested.connect(lambda: self.load_weather(False))
        self.setup_tab.run_requested.connect(self.run_simulation)
        self.setup_tab.crop_changed.connect(self._crop_changed)

        # dock log
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(2000)
        self.log_view.setMaximumHeight(150)
        dock = QDockWidget("Log", self)
        dock.setWidget(self.log_view)
        dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetClosable)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)
        self.log_dock = dock

        # status bar
        self.lb_status = QLabel("Siap.")
        self.progress = QProgressBar()
        self.progress.setMaximumWidth(260)
        self.progress.setVisible(False)
        self.bt_cancel = QPushButton("Batal")
        self.bt_cancel.setVisible(False)
        self.bt_cancel.clicked.connect(self.cancel_worker)
        self.statusBar().addWidget(self.lb_status, 1)
        self.statusBar().addPermanentWidget(self.progress)
        self.statusBar().addPermanentWidget(self.bt_cancel)

        self._build_menu()
        self.log(f"WOFOST Studio {__version__} siap. Pilih sumber cuaca, muat cuaca, lalu jalankan simulasi.")

    # ------------------------------------------------------------------ menu
    def _build_menu(self) -> None:
        m = self.menuBar().addMenu("&Proyek")
        a_open = QAction("Buka proyek (JSON)...", self); a_open.setShortcut("Ctrl+O"); a_open.triggered.connect(self.open_project)
        a_save = QAction("Simpan proyek", self); a_save.setShortcut("Ctrl+S"); a_save.triggered.connect(self.save_project)
        a_saveas = QAction("Simpan proyek sebagai...", self); a_saveas.triggered.connect(lambda: self.save_project(True))
        a_quit = QAction("Keluar", self); a_quit.setShortcut("Ctrl+Q"); a_quit.triggered.connect(self.close)
        for a in (a_open, a_save, a_saveas):
            m.addAction(a)
        m.addSeparator(); m.addAction(a_quit)

        s = self.menuBar().addMenu("&Simulasi")
        a_w = QAction("Muat data cuaca", self); a_w.setShortcut("F5"); a_w.triggered.connect(lambda: self.load_weather(False))
        a_wf = QAction("Muat ulang cuaca (paksa unduh)", self); a_wf.triggered.connect(lambda: self.load_weather(True))
        a_r = QAction("Jalankan simulasi", self); a_r.setShortcut("F9"); a_r.triggered.connect(self.run_simulation)
        a_ex = QAction("Ekspor cuaca ke CSV PCSE...", self); a_ex.triggered.connect(self.export_weather)
        for a in (a_w, a_wf, a_r):
            s.addAction(a)
        s.addSeparator(); s.addAction(a_ex)

        v = self.menuBar().addMenu("&Tampilan")
        v.addAction(self.log_dock.toggleViewAction())

        h = self.menuBar().addMenu("&Bantuan")
        a_about = QAction("Tentang", self); a_about.triggered.connect(self.about)
        h.addAction(a_about)

    # ------------------------------------------------------------------ util
    def log(self, msg: str) -> None:
        ts = dt.datetime.now().strftime("%H:%M:%S")
        self.log_view.appendPlainText(f"[{ts}] {msg}")
        self.lb_status.setText(msg.splitlines()[0][:160])

    def is_busy(self) -> bool:
        return self.worker is not None and self.worker.isRunning()

    def start_worker(self, fn, on_done, label: str, *args, **kwargs) -> Worker | None:
        """Jalankan fn(progress, cancelled, *args) di thread; on_done(result) di thread UI."""
        if self.is_busy():
            QMessageBox.information(self, "Sedang sibuk", "Tunggu proses yang sedang berjalan selesai atau tekan Batal.")
            return None
        self.worker = Worker(fn, *args, **kwargs)
        self._on_done = on_done
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_ok.connect(self._worker_ok)
        self.worker.failed.connect(self._worker_failed)
        self.worker.finished.connect(self._worker_cleanup)
        self.progress.setRange(0, 0)
        self.progress.setVisible(True)
        self.bt_cancel.setVisible(True)
        self._set_enabled(False)
        self.log(f"Mulai: {label}")
        self.worker.start()
        return self.worker

    def cancel_worker(self) -> None:
        if self.is_busy():
            self.worker.cancel()
            self.log("Permintaan batal dikirim, menunggu simulasi berjalan selesai...")

    def _set_enabled(self, on: bool) -> None:
        for w in (self.setup_tab.bt_run, self.setup_tab.bt_load_weather, self.batch_tab.bt_run,
                  self.sens_tab.bt_run, self.calib_tab.bt_run, self.assim_tab.bt_run, self.climate_tab.bt_run):
            w.setEnabled(on)

    def _on_progress(self, i: int, n: int, msg: str) -> None:
        if n > 0:
            self.progress.setRange(0, n)
            self.progress.setValue(i)
        if msg:
            self.lb_status.setText(f"{msg} ({i}/{n})" if n else msg)

    def _worker_ok(self, result) -> None:
        cb = self._on_done
        self._on_done = None
        if cb is not None:
            try:
                cb(result)
            except Exception as e:  # noqa: BLE001
                import traceback
                show_error(self, "Gagal memproses hasil", f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}")

    def _worker_failed(self, msg: str) -> None:
        self._on_done = None
        self.log(f"Gagal: {msg.splitlines()[0]}")
        if not msg.startswith("Dibatalkan"):
            show_error(self, "Proses gagal", msg)

    def _worker_cleanup(self) -> None:
        self.progress.setVisible(False)
        self.bt_cancel.setVisible(False)
        self._set_enabled(True)
        if self.lb_status.text().startswith("Mulai:"):
            self.lb_status.setText("Selesai.")

    def _crop_changed(self) -> None:
        # parameter default berubah -> perbarui tabel di tab analisis bila sudah terisi
        for tab in (self.sens_tab, self.calib_tab, self.assim_tab):
            if tab._populated:
                tab.refresh_params(force=True)

    # ------------------------------------------------------------------ cuaca
    def load_weather(self, force: bool = False, then=None) -> None:
        cfg = self.setup_tab.weather_config()

        def job(progress, cancelled):
            progress(0, 0, f"Memuat cuaca: {cfg.describe()}")
            return build_weather_provider(cfg, force_update=force)

        def done(wdp):
            self.wdp = wdp
            self.wdp_cfg = cfg
            s = weather_summary(wdp)
            txt = (f"OK: {cfg.describe()} | elevasi {s['Elevasi [m]']} m | "
                   f"{s['Tanggal awal']} s.d. {s['Tanggal akhir']} | hari hilang: {s['Hari hilang']}")
            self.setup_tab.set_weather_summary(txt, True)
            self.log("Cuaca dimuat. " + txt)
            if then:
                then()

        self.start_worker(job, done, f"Memuat cuaca ({cfg.describe()})")

    def _weather_ready(self) -> bool:
        cfg = self.setup_tab.weather_config()
        return self.wdp is not None and self.wdp_cfg == cfg

    def get_runner(self) -> SimulationRunner | None:
        """Bangun SimulationRunner dari konfigurasi saat ini; None bila belum siap."""
        if not self._weather_ready():
            QMessageBox.warning(self, "Cuaca belum dimuat",
                                "Data cuaca belum dimuat atau pengaturan cuaca berubah.\n"
                                "Tekan 'Muat data cuaca' di tab Pengaturan (F5) terlebih dahulu.")
            return None
        try:
            cfg = self.setup_tab.collect_config()
            return SimulationRunner(cfg, self.wdp)
        except Exception as e:  # noqa: BLE001
            show_error(self, "Konfigurasi tidak valid", f"{type(e).__name__}: {e}")
            return None

    # ------------------------------------------------------------------ simulasi
    def run_simulation(self) -> None:
        if not self._weather_ready():
            # muat cuaca dulu, lalu jalankan
            if self.is_busy():
                return
            self.load_weather(False, then=self.run_simulation)
            return
        runner = self.get_runner()
        if runner is None:
            return
        cfg = runner.cfg
        if cfg.crop_start_date < self.wdp.first_date or cfg.crop_end_date > self.wdp.last_date:
            show_error(self, "Di luar cakupan cuaca",
                       f"Periode simulasi {cfg.crop_start_date} s.d. {cfg.crop_end_date} berada di luar data cuaca "
                       f"({self.wdp.first_date} s.d. {self.wdp.last_date}).")
            return

        def job(progress, cancelled):
            progress(0, 0, "Menjalankan WOFOST...")
            return runner.run()

        def done(res: SimulationResult):
            self.last_result = res
            self.results_tab.show_result(res)
            s = res.summary
            self.log(f"Simulasi selesai ({res.runtime_s:.2f} s): TWSO = {s.get('TWSO', float('nan')):.0f} kg/ha, "
                     f"TAGP = {s.get('TAGP', float('nan')):.0f} kg/ha, LAImax = {s.get('LAIMAX', float('nan')):.2f}, "
                     f"masak = {s.get('DOM')}")
            self.tabs.setCurrentWidget(self.results_tab)

        self.start_worker(job, done, f"Simulasi {cfg.model_name} {cfg.crop_name}/{cfg.variety_name}")

    # ------------------------------------------------------------------ proyek
    def open_project(self) -> None:
        p, _ = QFileDialog.getOpenFileName(self, "Buka proyek", str(Path("data/projects").resolve()), "Proyek JSON (*.json)")
        if not p:
            return
        try:
            cfg = SimulationConfig.load(p)
            self.setup_tab.apply_config(cfg)
        except Exception as e:  # noqa: BLE001
            show_error(self, "Gagal membuka proyek", f"{type(e).__name__}: {e}")
            return
        self.project_path = p
        self.setWindowTitle(f"WOFOST Studio {__version__} - {Path(p).name}")
        self.log(f"Proyek dibuka: {p}")

    def save_project(self, save_as: bool = False) -> None:
        try:
            cfg = self.setup_tab.collect_config()
        except Exception as e:  # noqa: BLE001
            show_error(self, "Konfigurasi tidak valid", f"{type(e).__name__}: {e}")
            return
        p = self.project_path
        if save_as or not p:
            p, _ = QFileDialog.getSaveFileName(self, "Simpan proyek", str(Path("data/projects").resolve() / "proyek.json"),
                                               "Proyek JSON (*.json)")
            if not p:
                return
        cfg.save(p)
        self.project_path = p
        self.setWindowTitle(f"WOFOST Studio {__version__} - {Path(p).name}")
        self.log(f"Proyek disimpan: {p}")

    def export_weather(self) -> None:
        if self.wdp is None:
            QMessageBox.information(self, "Ekspor cuaca", "Muat data cuaca terlebih dahulu.")
            return
        p, _ = QFileDialog.getSaveFileName(self, "Ekspor cuaca ke CSV PCSE", "cuaca_pcse.csv", "CSV (*.csv)")
        if not p:
            return
        try:
            export_weather_csv_pcse(self.wdp, p)
        except Exception as e:  # noqa: BLE001
            show_error(self, "Gagal mengekspor", f"{type(e).__name__}: {e}")
            return
        self.log(f"Cuaca diekspor ke {p} (dapat dimuat ulang lewat sumber 'File CSV format PCSE').")

    def about(self) -> None:
        QMessageBox.about(self, "Tentang WOFOST Studio",
                          f"<b>WOFOST Studio {__version__}</b><br>"
                          "Antarmuka PySide6 untuk PCSE (Python Crop Simulation Environment) - WOFOST.<br><br>"
                          "Fitur: simulasi WOFOST 7.2/7.3 (potensial & terbatas air), cuaca Open-Meteo / NASA POWER / "
                          "CSV / Excel / CABO, batch tanggal tanam, analisis sensitivitas global (SALib Morris & Sobol), "
                          "kalibrasi parameter (scipy.optimize), kalibrasi Bayesian MCMC (emcee), dan asimilasi data EnKF.<br><br>"
                          "Referensi: de Wit et al. (2019) Agricultural Systems 168:154-167 (WOFOST 25 tahun); "
                          "PCSE: https://pcse.readthedocs.io")

    def closeEvent(self, ev) -> None:  # noqa: N802
        if self.is_busy():
            self.worker.cancel()
            self.worker.wait(5000)
        super().closeEvent(ev)
