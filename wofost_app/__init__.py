"""WOFOST Studio - aplikasi desktop PySide6 untuk simulasi tanaman PCSE-WOFOST."""
__version__ = "0.1.0"


def _silence_pcse_file_logging() -> None:
    """PCSE memasang RotatingFileHandler di ~/.pcse/logs; rotasinya gagal (WinError 32) bila dua proses aktif
    (aplikasi + pool proses/skrip). Lepas handler berkas itu dan sisakan konsol level WARNING."""
    import logging
    import logging.handlers as _lh
    try:
        import pcse  # noqa: F401  (memicu konfigurasi logging PCSE)
    except Exception:  # noqa: BLE001
        return
    for name in ("", "pcse"):
        lg = logging.getLogger(name)
        for h in list(lg.handlers):
            if isinstance(h, _lh.RotatingFileHandler):
                lg.removeHandler(h)
    logging.getLogger("pcse").setLevel(logging.WARNING)


_silence_pcse_file_logging()
