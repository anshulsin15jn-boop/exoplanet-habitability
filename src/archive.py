"""Helpers for downloading tables from the NASA Exoplanet Archive TAP service.

TAP endpoint and CSV format are documented at
https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html
"""

from datetime import datetime
from pathlib import Path

import requests

TAP_SYNC_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"


def download_tap_csv(adql, out_path):
    """Run an ADQL query on the archive and save the result as a CSV file.

    The data is first written to a temporary ``.part`` file and renamed only when the
    download is complete, so a failed download never looks like a real snapshot.
    The query text is saved next to the CSV as ``<name>.query.txt``.
    Refuses to overwrite an existing file.
    """
    out_path = Path(out_path)
    if out_path.exists():
        raise FileExistsError(f"{out_path} already exists; snapshots are never overwritten")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(TAP_SYNC_URL, params={"query": adql, "format": "csv"}, timeout=120)
    response.raise_for_status()

    part_path = out_path.with_name(out_path.name + ".part")
    part_path.write_bytes(response.content)
    part_path.replace(out_path)

    query_path = out_path.with_name(out_path.stem + ".query.txt")
    query_path.write_text(
        f"Downloaded: {datetime.now().isoformat(timespec='seconds')}\n"
        f"Endpoint: {TAP_SYNC_URL}\n"
        f"Format: csv\n"
        f"Query:\n{adql}\n"
    )
    return out_path


def latest_snapshot(folder, prefix):
    """Return the newest ``<prefix>_YYYY-MM-DD.csv`` in ``folder``, or None if there is none.

    ISO dates (year-month-day) sort correctly as plain text, so the last name is the newest.
    """
    snapshots = sorted(Path(folder).glob(f"{prefix}_????-??-??.csv"))
    if not snapshots:
        return None
    return snapshots[-1]
