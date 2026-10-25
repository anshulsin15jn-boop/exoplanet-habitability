"""The notebook's Colab setup cell must do nothing outside Colab, and the right things inside it."""

import io
import json
import os
import subprocess
import sys
import types
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = PROJECT_ROOT / "notebooks" / "exoplanet_habitability.ipynb"
REPO_URL = "https://github.com/anshulsin15jn-boop/exoplanet-habitability.git"
REPO_DIR = "/content/exoplanet-habitability"


def colab_cell_source():
    """Source of the code cell tagged "colab-setup" (read with json, so Jupyter is not needed)."""
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = [c for c in notebook["cells"] if "colab-setup" in c.get("metadata", {}).get("tags", [])]
    assert len(cells) == 1, "expected exactly one cell tagged colab-setup"
    assert cells[0]["cell_type"] == "code"
    return "".join(cells[0]["source"])


def install_recorders(monkeypatch):
    """Replace subprocess.run and os.chdir with recorders so the cell cannot touch anything.

    Call this after any monkeypatch.chdir, which itself uses os.chdir.
    """
    calls = {"run": [], "chdir": []}
    monkeypatch.setattr(subprocess, "run", lambda args, **kwargs: calls["run"].append(list(args)))
    monkeypatch.setattr(os, "chdir", lambda path: calls["chdir"].append(path))
    return calls


def test_colab_cell_is_the_first_code_cell():
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    first_code = next(c for c in notebook["cells"] if c["cell_type"] == "code")
    assert "colab-setup" in first_code.get("metadata", {}).get("tags", [])


def test_does_nothing_outside_colab(monkeypatch, tmp_path):
    monkeypatch.delitem(sys.modules, "google.colab", raising=False)
    monkeypatch.chdir(tmp_path)
    recorder = install_recorders(monkeypatch)
    namespace = {}
    exec(colab_cell_source(), namespace)
    assert namespace["IN_COLAB"] is False
    assert recorder["run"] == []
    assert recorder["chdir"] == []
    assert Path.cwd() == tmp_path
    assert list(tmp_path.iterdir()) == []


def test_in_colab_clones_installs_and_moves_into_notebooks(monkeypatch):
    recorder = install_recorders(monkeypatch)
    monkeypatch.setitem(sys.modules, "google.colab", types.ModuleType("google.colab"))
    monkeypatch.setattr(os.path, "exists", lambda path: False)
    requirements = (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8")
    namespace = {"open": lambda path, *args, **kwargs: io.StringIO(requirements)}
    exec(colab_cell_source(), namespace)

    assert namespace["IN_COLAB"] is True
    clone, install = recorder["run"]
    assert clone == ["git", "clone", "--depth", "1", REPO_URL, REPO_DIR]
    assert install[:5] == [sys.executable, "-m", "pip", "install", "-q"]
    packages = install[5:]
    assert "pandas>=2.0" in packages and "scikit-learn>=1.4" in packages
    assert not any(p.startswith("jupyter") for p in packages)
    assert recorder["chdir"] == [os.path.join(REPO_DIR, "notebooks")]
