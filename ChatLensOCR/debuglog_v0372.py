# -*- coding: utf-8 -*-
"""Private, local, copyable diagnostic log for ChatLens OCR.

Only filenames, image geometry, selected settings, processing stages and
exception tracebacks are recorded. OCR'd conversations and image pixels are
not written to this log. Logs rotate to avoid unbounded growth.
"""
import logging
from logging.handlers import RotatingFileHandler
import os
import platform
import sys
import threading
import traceback
from pathlib import Path

VERSION = "0.3.7.2"
LOG_DIR = Path(os.environ.get("LOCALAPPDATA") or str(Path.home())) / "ChatLensOCR" / "logs"
LOG_FILE = LOG_DIR / "ChatLensOCR.log"
_LOGGER = logging.getLogger("ChatLensOCR.diagnostics")
_LOCK = threading.RLock()
_LOCAL = threading.local()
_CONFIGURED = False

def _init():
    global _CONFIGURED
    with _LOCK:
        if _CONFIGURED:
            return
        _LOGGER.setLevel(logging.INFO)
        _LOGGER.propagate = False
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                                datefmt="%Y-%m-%d %H:%M:%S")
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            handler = RotatingFileHandler(str(LOG_FILE), maxBytes=2_000_000,
                                          backupCount=2, encoding="utf-8")
            handler.setFormatter(fmt)
            _LOGGER.addHandler(handler)
        except OSError:
            # Even when writing is blocked, avoid crashing the OCR application.
            _LOGGER.addHandler(logging.NullHandler())
        _CONFIGURED = True
        _LOGGER.info("ChatLens OCR %s | platform=%s | python=%s | frozen=%s",
                     VERSION, platform.platform(),sys.version.split()[0],
                     bool(getattr(sys, "frozen", False)))

def context(**fields):
    _LOCAL.context = dict(fields)

def clear_context():
    _LOCAL.context = {}

def _where(**fields):
    state = dict(getattr(_LOCAL,"context",{}))
    state.update(fields)
    return " | ".join("%s=%r" % (key,value) for key,value in state.items())

def note(event,**fields):
    _init()
    _LOGGER.info("%s | %s", event, _where(**fields))

def warning(event,**fields):
    _init()
    _LOGGER.warning("%s | %s",event,_where(**fields))

def exception(event, exc=None, **fields):
    _init()
    detail=traceback.format_exc()
    if detail.strip()=="NoneType: None":
        if exc is None: detail="(traceback unavailable)"
        else: detail="".join(traceback.format_exception(type(exc),exc,exc.__traceback__))
    _LOGGER.error("%s | %s\n%s",event,_where(**fields),detail)
    return detail

def recent_text(limit=250_000):
    _init()
    with _LOCK:
        for handler in _LOGGER.handlers:
            try:handler.flush()
            except Exception:pass
        try:
            with LOG_FILE.open("rb") as f:
                f.seek(0,2)
                size=f.tell()
                f.seek(max(0,size-limit))
                content=f.read().decode("utf-8",errors="replace")
            if size>limit:
                content="(가장 최근 로그만 표시합니다.)\n"+content.partition("\n")[2]
            return "ChatLens OCR v%s | 로그 파일: %s\n\n%s" % (VERSION,LOG_FILE,content)
        except OSError as e:
            return "로그 파일을 읽을 수 없습니다: %s\n경로: %s" % (e,LOG_FILE)
