#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Singleton per SenseHat — una sola istanza per l'intera applicazione.
Include cleanup automatico dei LED all'uscita (atexit + SIGTERM).
"""

import atexit
import signal
import sys


_instance = None


def get_sense_hat():
    """
    Restituisce l'istanza singleton del SenseHat.
    Al primo accesso inizializza l'hardware e registra i cleanup hook.
    """
    global _instance
    if _instance is None:
        from sense_hat import SenseHat
        _instance = SenseHat()
        _instance.set_rotation(180)

        atexit.register(_cleanup)

        signal.signal(signal.SIGTERM, _sigterm_handler)
    return _instance


def _cleanup():
    """Spegne i LED all'uscita normale (atexit)."""
    if _instance is not None:
        try:
            _instance.clear()
        except Exception:
            pass


def _sigterm_handler(signum, frame):
    """Gestore SIGTERM: forza l'uscita con codice 0, atexit pulira i LED."""
    sys.exit(0)
