from __future__ import annotations

import os
import shutil
import tempfile
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from autotag.app.config import get_settings

_DB_DIR = tempfile.mkdtemp(prefix="autotag-test-db-")
_MODELS_DIR = tempfile.mkdtemp(prefix="autotag-test-models-")
os.environ["AUTOTAG_DATABASE_URL"] = f"sqlite:///{os.path.join(_DB_DIR, 'test.db')}"
os.environ["AUTOTAG_MODELS_DIR"] = _MODELS_DIR
get_settings.cache_clear()


@pytest.fixture(scope="session", autouse=True)
def cleanup_env() -> None:
    yield
    shutil.rmtree(_DB_DIR, ignore_errors=True)
    shutil.rmtree(_MODELS_DIR, ignore_errors=True)
    get_settings.cache_clear()
