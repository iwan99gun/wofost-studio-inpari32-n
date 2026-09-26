# WOFOST Studio

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22969839.svg)](https://doi.org/10.5281/zenodo.22969839)

A PySide6 desktop application wrapping [PCSE](https://github.com/ajwdewit/pcse) 6.0.13 / WOFOST for
crop-model calibration, sensitivity analysis (Morris, Sobol, eFAST), Bayesian calibration (least squares
and MCMC via `emcee`), ensemble Kalman filter data assimilation, climate-scenario runs, and
journal-ready figure export.

This repository accompanies the manuscript *"Nitrogen-limited WOFOST 8.1 for tropical transplanted
rice: parameter-consistency fixes, a leaf-level nitrogen extension and independent omission-plot
validation in West Java, Indonesia"* (manuscript in preparation; a repository/DOI badge will be added
here once submitted).

## What's in this repository

| Path | Contents |
|---|---|
| `wofost_app/` | The application: `core/` (Qt-free simulation, calibration, sensitivity, assimilation, climate modules — usable standalone from scripts/notebooks) and `ui/` (PySide6 widgets and tabs) |
| `main.py` | Application entry point (`python main.py`) |
| `data/projects/` | Saved simulation configurations (JSON) for every calibrated site/season used in the study |
| `data/lapangan/` | Digitised/derived field data (CSV) and analysis results (JSON, PNG) — see "Data provenance" below |
| `data/crop_params/` | Local copy of the WOFOST 8.1 (`wofost81` branch) crop parameter file used for reproducibility |
| `naskah/` | Scripts that regenerate every figure and the manuscript text/tables from the result files in `data/lapangan/` (`buat_gambar.py`, `buat_naskah.py`) |
| `naskah/analisis/` | Standalone analysis scripts (calibration, MCMC, Sobol sensitivity, LTFE validation, robustness checks) that produced the JSON files in `data/lapangan/` |
| `docs/` | Project documentation in Indonesian: literature-derived data sources, calibration history, feature validation |

Not included: PDF copies of the third-party journal articles used as data sources (copyrighted), and
the manuscript draft itself (will be added as a preprint link once submitted, per journal policy).

## Requirements

Python 3.12, see `requirements.txt`. Tested on Windows.

```bash
pip install -r requirements.txt
```

## Running the application

```bash
python main.py
```

## Reproducing the analysis

Each script in `naskah/analisis/` is self-contained and documents its data sources and method in its
docstring. A typical entry point:

```bash
python naskah/analisis/calib_shock.py      # Step 1: potential-production calibration
python naskah/analisis/mcmc_bersama.py     # Staged Bayesian calibration (long-running, ~12 h)
python naskah/analisis/validasi_ltfe.py    # Independent blind validation against omission plots
python naskah/buat_gambar.py               # Regenerate all manuscript figures from data/lapangan/*.json
python naskah/buat_naskah.py               # Regenerate the manuscript DOCX/PDF (requires MS Word for PDF export)
```

## Data provenance

All values in `data/lapangan/*.csv` that were extracted from figures in published papers are digitised
at the pixel level (axis calibration on major ticks) and carry, in a `sumber`/`source` column, the full
citation of the original publication. Uncertainty combines the digitising error with the reported
experimental standard deviation where available. See `docs/data_sekunder.md` for the full account of
every dataset, its source, and how it was used.

Field weather data are pulled at run time from Open-Meteo / NASA POWER via `wofost_app/core/weather.py`
and are not redistributed here.

## Key findings implemented in code

- **Parameter-consistency fixes for WOFOST 8.1** (`wofost_app/core/simulation.py`): `RGRLAI_MIN_FR`
  (keeps `RGRLAI_MIN` a fraction of the calibrated `RGRLAI`), automatic `AMAX_REF` derived from the
  calibrated `AMAXTB@y`, and a merge of same-day agromanagement events.
- **NLEAF extension** (`wofost_app/core/wofost81_nleaf.py`): an optional LINTUL3-type nitrogen-stress
  effect on specific leaf area and exponential-phase leaf expansion.
- **PART_DELAY** (`wofost_app/core/simulation.py`, `shift_postanthesis_partitioning`): an optional,
  mass-conserving delay of full post-anthesis assimilate allocation to the storage organ.

## License

Code and derived data: MIT, see `LICENSE`. Third-party source articles cited in `data/lapangan/` remain
under their publishers' copyright and are not included here.

## Citation

See `CITATION.cff`.
