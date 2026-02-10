"""Shared test fixtures."""
import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path for imports
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


@pytest.fixture
def tmp_download_dir(tmp_path: Path) -> Path:
    """Create a temporary download directory."""
    dl = tmp_path / "downloads"
    dl.mkdir()
    return dl
