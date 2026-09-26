"""Tab Pengaturan: cuaca, tanaman/model, kalender tanam, irigasi, tanah, lokasi, override."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDateEdit, QDoubleSpinBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QSpinBox, QSplitter, QVBoxLayout, QWidget,
)

from ..core.config import (
    CROP_END_TYPES, CROP_START_TYPES, SITE_PARAM_INFO, SOIL_PARAM_INFO, SOIL_PRESETS,
    SimulationConfig, WeatherConfig,
)
from ..core.simulation import CROP_PARAM_INFO, MODELS, analysis_crop_params, list_crops
from ..core.weather import WEATHER_SOURCES
from .widgets import FertilizationTable, IrrigationTable, OverrideTable, ParamTable, from_qdate, show_error, to_qdate


class SetupTab(QWidget):
    crop_changed = Signal()          # model/tanaman/varietas berubah -> parameter default berubah
    load_weather_requested = Signal()
    run_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._crops = list_crops()
        self._defaults: dict[str, float] = {}
        self._build()
        self.apply_config(SimulationConfig())

    # ------------------------------------------------------------------ UI
    def _build(self) -> None:
        split = QSplitter(Qt.Orientation.Horizontal, self)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.addWidget(split)

        # ---------------- kolom kiri ----------------
        left = QWidget()
        ll = QVBoxLayout(left)

        # Cuaca
        gw = QGroupBox("Sumber data cuaca")
        fw = QFormLayout(gw)
        self.cb_source = QComboBox()
        for k, v in WEATHER_SOURCES.items():
            self.cb_source.addItem(v, k)
        self.cb_source.currentIndexChanged.connect(self._update_weather_widgets)
        fw.addRow("Sumber", self.cb_source)
        self.sp_lat = QDoubleSpinBox(); self.sp_lat.setRange(-90, 90); self.sp_lat.setDecimals(4)
        self.sp_lon = QDoubleSpinBox(); self.sp_lon.setRange(-180, 180); self.sp_lon.setDecimals(4)
        row = QHBoxLayout(); row.addWidget(QLabel("Lintang")); row.addWidget(self.sp_lat)
        row.addWidget(QLabel("Bujur")); row.addWidget(self.sp_lon)
        self.w_latlon = QWidget(); self.w_latlon.setLayout(row); row.setContentsMargins(0, 0, 0, 0)
        fw.addRow("Koordinat", self.w_latlon)
        self.ed_path = QLineEdit()
        self.bt_browse = QPushButton("...")
        self.bt_browse.setFixedWidth(32)
        self.bt_browse.clicked.connect(self._browse_weather)
        prow = QHBoxLayout(); prow.setContentsMargins(0, 0, 0, 0)
        prow.addWidget(self.ed_path); prow.addWidget(self.bt_browse)
        self.w_path = QWidget(); self.w_path.setLayout(prow)
        fw.addRow("File / folder", self.w_path)
        self.ed_station = QLineEdit(); self.ed_station.setPlaceholderText("mis. NL1")
        fw.addRow("Stasiun CABO", self.ed_station)
        self.ed_tz = QLineEdit("Asia/Jakarta")
        fw.addRow("Zona waktu (Open-Meteo)", self.ed_tz)
        self.cb_et = QComboBox(); self.cb_et.addItems(["PM", "P"])
        self.cb_et.setToolTip("PM = Penman-Monteith, P = Penman")
        fw.addRow("Model ET0", self.cb_et)
        self.bt_load_weather = QPushButton("Muat data cuaca")
        self.bt_load_weather.clicked.connect(self.load_weather_requested.emit)
        self.lb_weather = QLabel("Cuaca belum dimuat.")
        self.lb_weather.setWordWrap(True)
        self.lb_weather.setStyleSheet("color: #7a4b00;")
        fw.addRow(self.bt_load_weather)
        fw.addRow(self.lb_weather)
        ll.addWidget(gw)

        # Tanaman & model
        gc = QGroupBox("Tanaman dan model")
        fc = QFormLayout(gc)
        self.cb_model = QComboBox()
        for k, v in MODELS.items():
            self.cb_model.addItem(f"{k}  -  {v}", k)
        self.cb_crop = QComboBox()
        self.cb_crop.addItems(list(self._crops.keys()))
        self.cb_variety = QComboBox()
        self.cb_model.currentIndexChanged.connect(self._on_crop_changed)
        self.cb_crop.currentIndexChanged.connect(self._on_crop_selected)
        self.cb_variety.currentIndexChanged.connect(self._on_crop_changed)
        fc.addRow("Model", self.cb_model)
        fc.addRow("Tanaman", self.cb_crop)
        fc.addRow("Varietas", self.cb_variety)
        self.lb_crop_hint = QLabel("")
        self.lb_crop_hint.setWordWrap(True)
        self.lb_crop_hint.setStyleSheet("color: #555;")
        fc.addRow(self.lb_crop_hint)
        ll.addWidget(gc)

        # Kalender
        gk = QGroupBox("Kalender tanam (agromanagement)")
        fk = QFormLayout(gk)
        self.de_start = QDateEdit(); self.de_start.setCalendarPopup(True); self.de_start.setDisplayFormat("yyyy-MM-dd")
        self.cb_start_type = QComboBox(); self.cb_start_type.addItems(CROP_START_TYPES)
        self.cb_start_type.setToolTip("sowing = mulai dari tanam benih (butuh TSUMEM>0);\n"
                                      "emergence = mulai dari emergensi/tanam pindah")
        self.de_end = QDateEdit(); self.de_end.setCalendarPopup(True); self.de_end.setDisplayFormat("yyyy-MM-dd")
        self.cb_end_type = QComboBox(); self.cb_end_type.addItems(CROP_END_TYPES)
        self.cb_end_type.setToolTip("maturity = berhenti saat masak fisiologis;\n"
                                    "harvest = berhenti pada tanggal akhir;\n"
                                    "earliest = mana yang lebih dulu")
        self.sp_maxdur = QSpinBox(); self.sp_maxdur.setRange(30, 730); self.sp_maxdur.setValue(300)
        fk.addRow("Tanggal awal", self.de_start)
        fk.addRow("Tipe awal", self.cb_start_type)
        fk.addRow("Tanggal akhir", self.de_end)
        fk.addRow("Tipe akhir", self.cb_end_type)
        fk.addRow("Durasi maksimum [hari]", self.sp_maxdur)
        self.cb_shock = QCheckBox("Emulasi syok tanam pindah (ORYZA2000: SHCKL, SHCKD)")
        self.cb_shock.setToolTip("Pertumbuhan daun ditahan selama SHCKL x TSTR dan perkembangan ditunda SHCKD x TSTR;\n"
                                 "TSTR = jumlah suhu efektif di persemaian (umur bibit). Bouman et al. (2001) baku: 0,25 dan 0,40.")
        self.sp_seedage = QSpinBox(); self.sp_seedage.setRange(5, 60); self.sp_seedage.setValue(21)
        self.sp_shckl = QDoubleSpinBox(); self.sp_shckl.setRange(0, 1); self.sp_shckl.setSingleStep(0.05); self.sp_shckl.setValue(0.25)
        self.sp_shckd = QDoubleSpinBox(); self.sp_shckd.setRange(0, 1); self.sp_shckd.setSingleStep(0.05); self.sp_shckd.setValue(0.40)
        fk.addRow(self.cb_shock)
        fk.addRow("Umur bibit [hari]", self.sp_seedage)
        fk.addRow("SHCKL (penundaan daun)", self.sp_shckl)
        fk.addRow("SHCKD (penundaan perkembangan)", self.sp_shckd)
        ll.addWidget(gk)

        # Irigasi
        gi = QGroupBox("Irigasi terjadwal (opsional)")
        vi = QVBoxLayout(gi)
        self.tb_irr = IrrigationTable()
        self.tb_irr.setMinimumHeight(110)
        vi.addWidget(self.tb_irr)
        hb = QHBoxLayout()
        b_add = QPushButton("Tambah"); b_add.clicked.connect(lambda: self.tb_irr.add_event())
        b_del = QPushButton("Hapus"); b_del.clicked.connect(self.tb_irr.remove_selected)
        b_flood = QPushButton("Isi genangan sawah")
        b_flood.setToolTip("Isi irigasi 2 cm tiap 2 hari (efisiensi 1,0) dari tanggal awal sampai +130 hari.\n"
                           "Meniru sawah tergenang: neraca air klasik WOFOST menganggap tanah drainase bebas,\n"
                           "sehingga tanpa irigasi padi musim kemarau tercekam air secara artifisial.")
        b_flood.clicked.connect(self.fill_flooding)
        hb.addWidget(b_add); hb.addWidget(b_del); hb.addWidget(b_flood); hb.addStretch()
        vi.addLayout(hb)
        ll.addWidget(gi)

        # Pemupukan N (hanya model terbatas N)
        self.gf = QGroupBox("Pemupukan N terjadwal (hanya WOFOST 8.1 terbatas N)")
        self.gf.setToolTip("Setiap baris = sinyal apply_n PCSE: N_amount [kg N/ha] x recovery masuk ke kolam N tersedia.\n"
                           "Parameter N tanah (NAVAILI, NSOILBASE, NSOILBASE_FR, BG_N_SUPPLY) ada di tabel lokasi.")
        vf = QVBoxLayout(self.gf)
        self.tb_fert = FertilizationTable()
        self.tb_fert.setMinimumHeight(110)
        vf.addWidget(self.tb_fert)
        hf = QHBoxLayout()
        f_add = QPushButton("Tambah"); f_add.clicked.connect(lambda: self.tb_fert.add_event())
        f_del = QPushButton("Hapus"); f_del.clicked.connect(self.tb_fert.remove_selected)
        hf.addWidget(f_add); hf.addWidget(f_del); hf.addStretch()
        vf.addLayout(hf)
        ll.addWidget(self.gf)
        self.cb_model.currentIndexChanged.connect(self._update_n_widgets)
        self._update_n_widgets()

        self.bt_run = QPushButton("Jalankan simulasi")
        self.bt_run.setStyleSheet("font-weight: bold; padding: 6px;")
        self.bt_run.clicked.connect(self.run_requested.emit)
        ll.addWidget(self.bt_run)
        ll.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(left)
        split.addWidget(scroll)

        # ---------------- kolom kanan ----------------
        right = QWidget()
        rl = QVBoxLayout(right)

        gs = QGroupBox("Parameter tanah")
        vs = QVBoxLayout(gs)
        hp = QHBoxLayout()
        hp.addWidget(QLabel("Preset"))
        self.cb_soil_preset = QComboBox()
        self.cb_soil_preset.addItems(list(SOIL_PRESETS.keys()))
        self.cb_soil_preset.currentTextChanged.connect(self._apply_soil_preset)
        hp.addWidget(self.cb_soil_preset, 1)
        vs.addLayout(hp)
        self.tb_soil = ParamTable()
        vs.addWidget(self.tb_soil)
        rl.addWidget(gs, 3)

        gsite = QGroupBox("Parameter lokasi (site)")
        vsite = QVBoxLayout(gsite)
        self.tb_site = ParamTable()
        vsite.addWidget(self.tb_site)
        rl.addWidget(gsite, 2)

        go = QGroupBox("Parameter tanaman (ubah nilai untuk override; baris kuning = di-override; "
                       "NAME@y = pengali tabel, NAME@x = geser suhu tabel)")
        vo = QVBoxLayout(go)
        self.tb_over = OverrideTable()
        vo.addWidget(self.tb_over)
        ho = QHBoxLayout()
        b_reset = QPushButton("Kembalikan ke default")
        b_reset.clicked.connect(self.tb_over.reset)
        ho.addWidget(b_reset); ho.addStretch()
        vo.addLayout(ho)
        rl.addWidget(go, 5)

        split.addWidget(right)
        split.setSizes([520, 680])

    # ---------------------------------------------------------- perilaku
    def _update_weather_widgets(self) -> None:
        src = self.cb_source.currentData()
        online = src in ("openmeteo", "nasapower")
        self.w_latlon.setEnabled(online)
        self.w_path.setEnabled(not online)
        self.ed_station.setEnabled(src == "cabo")
        self.ed_tz.setEnabled(src == "openmeteo")

    def _browse_weather(self) -> None:
        src = self.cb_source.currentData()
        if src == "cabo":
            p = QFileDialog.getExistingDirectory(self, "Pilih folder file CABO")
        elif src == "excel":
            p, _ = QFileDialog.getOpenFileName(self, "Pilih file Excel cuaca", "", "Excel (*.xlsx *.xls)")
        else:
            p, _ = QFileDialog.getOpenFileName(self, "Pilih file CSV cuaca (format PCSE)", "", "CSV (*.csv)")
        if p:
            self.ed_path.setText(p)

    def _on_crop_selected(self) -> None:
        crop = self.cb_crop.currentText()
        self.cb_variety.blockSignals(True)
        self.cb_variety.clear()
        self.cb_variety.addItems(self._crops.get(crop, []))
        self.cb_variety.blockSignals(False)
        self._on_crop_changed()

    def _on_crop_changed(self) -> None:
        model = self.cb_model.currentData()
        crop = self.cb_crop.currentText()
        var = self.cb_variety.currentText()
        if not (model and crop and var):
            return
        try:
            self._defaults = analysis_crop_params(model, crop, var)
        except Exception as e:  # noqa: BLE001
            show_error(self, "Gagal memuat parameter tanaman", f"{type(e).__name__}: {e}")
            self._defaults = {}
        keep = {}
        try:
            keep = self.tb_over.overrides()
        except ValueError:
            pass
        keep = {k: v for k, v in keep.items() if k in self._defaults}
        self.tb_over.set_params(self._defaults, keep, CROP_PARAM_INFO)
        tsumem = self._defaults.get("TSUMEM", 1.0)
        if tsumem <= 0:
            self.lb_crop_hint.setText("Varietas ini memiliki TSUMEM = 0 (tanam pindah). Gunakan tipe awal 'emergence'.")
            self.cb_start_type.setCurrentText("emergence")
        else:
            self.lb_crop_hint.setText(f"TSUM1 = {self._defaults.get('TSUM1', '?')}, TSUM2 = {self._defaults.get('TSUM2', '?')}, "
                                      f"TSUMEM = {tsumem}")
        self.crop_changed.emit()

    def fill_flooding(self, amount_cm: float = 2.0, every_days: int = 2, span_days: int = 130) -> None:
        import datetime as _dt
        from ..core.config import IrrigationEvent
        start = from_qdate(self.de_start.date())
        end = min(from_qdate(self.de_end.date()), start + _dt.timedelta(days=span_days))
        n = max((end - start).days, 0)
        self.tb_irr.set_events([IrrigationEvent(start + _dt.timedelta(days=d), amount_cm, 1.0) for d in range(0, n + 1, every_days)])

    def _update_n_widgets(self) -> None:
        name = self.cb_model.currentData() or ""
        self.gf.setEnabled(name.startswith("Wofost81") and "NWLP" in name)

    def _apply_soil_preset(self, name: str) -> None:
        if name in SOIL_PRESETS:
            self.tb_soil.set_params(SOIL_PRESETS[name], SOIL_PARAM_INFO)

    # ----------------------------------------------------------- API luar
    def set_weather_summary(self, text: str, ok: bool) -> None:
        self.lb_weather.setText(text)
        self.lb_weather.setStyleSheet("color: #0a6b2a;" if ok else "color: #7a4b00;")

    def weather_config(self) -> WeatherConfig:
        return WeatherConfig(
            source=self.cb_source.currentData(),
            latitude=float(self.sp_lat.value()), longitude=float(self.sp_lon.value()),
            path=self.ed_path.text().strip(), station=self.ed_station.text().strip(),
            et_model=self.cb_et.currentText(), timezone=self.ed_tz.text().strip() or "UTC",
        )

    def collect_config(self) -> SimulationConfig:
        cfg = SimulationConfig(
            model_name=self.cb_model.currentData(),
            crop_name=self.cb_crop.currentText(),
            variety_name=self.cb_variety.currentText(),
            crop_start_date=from_qdate(self.de_start.date()),
            crop_start_type=self.cb_start_type.currentText(),
            crop_end_date=from_qdate(self.de_end.date()),
            crop_end_type=self.cb_end_type.currentText(),
            max_duration=int(self.sp_maxdur.value()),
            soil=self.tb_soil.values(),
            site=self.tb_site.values(),
            crop_overrides=self.tb_over.overrides(),
            irrigation=self.tb_irr.events(),
            fertilization=self.tb_fert.events(),
            weather=self.weather_config(),
            transplant_shock=self.cb_shock.isChecked(),
            seedling_age_days=int(self.sp_seedage.value()),
            shckl=float(self.sp_shckl.value()), shckd=float(self.sp_shckd.value()),
        )
        if cfg.crop_end_date <= cfg.crop_start_date:
            raise ValueError("Tanggal akhir harus setelah tanggal awal.")
        return cfg

    def apply_config(self, cfg: SimulationConfig) -> None:
        w = cfg.weather
        i = self.cb_source.findData(w.source)
        self.cb_source.setCurrentIndex(max(i, 0))
        self.sp_lat.setValue(w.latitude); self.sp_lon.setValue(w.longitude)
        self.ed_path.setText(w.path); self.ed_station.setText(w.station)
        self.ed_tz.setText(w.timezone); self.cb_et.setCurrentText(w.et_model)
        self._update_weather_widgets()

        i = self.cb_model.findData(cfg.model_name)
        self.cb_model.blockSignals(True); self.cb_model.setCurrentIndex(max(i, 0)); self.cb_model.blockSignals(False)
        self.cb_crop.blockSignals(True); self.cb_crop.setCurrentText(cfg.crop_name); self.cb_crop.blockSignals(False)
        self.cb_variety.blockSignals(True)
        self.cb_variety.clear(); self.cb_variety.addItems(self._crops.get(cfg.crop_name, []))
        self.cb_variety.setCurrentText(cfg.variety_name)
        self.cb_variety.blockSignals(False)
        self.tb_over.set_params({}, {}, {})
        self._on_crop_changed()
        self.tb_over.apply_overrides(cfg.crop_overrides)

        self.de_start.setDate(to_qdate(cfg.crop_start_date))
        self.cb_start_type.setCurrentText(cfg.crop_start_type)
        self.de_end.setDate(to_qdate(cfg.crop_end_date))
        self.cb_end_type.setCurrentText(cfg.crop_end_type)
        self.sp_maxdur.setValue(cfg.max_duration)
        self.tb_irr.set_events(cfg.irrigation)
        self.tb_fert.set_events(cfg.fertilization)
        self._update_n_widgets()
        self.cb_shock.setChecked(bool(cfg.transplant_shock))
        self.sp_seedage.setValue(int(cfg.seedling_age_days))
        self.sp_shckl.setValue(float(cfg.shckl)); self.sp_shckd.setValue(float(cfg.shckd))

        self.tb_soil.set_params(cfg.soil, SOIL_PARAM_INFO)
        site = {k: cfg.site.get(k, SITE_PARAM_INFO[k][1]) for k in SITE_PARAM_INFO}
        site.update({k: v for k, v in cfg.site.items() if k not in site})
        self.tb_site.set_params(site, SITE_PARAM_INFO)

    def apply_overrides(self, values: dict[str, float]) -> None:
        self.tb_over.apply_overrides(values)

    def current_crop_params(self) -> dict[str, float]:
        """Nilai parameter tanaman aktif (default + override)."""
        return self.tb_over.current_values()
