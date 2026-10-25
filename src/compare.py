"""Helpers for comparing our habitable zone list with published lists (Phase 6)."""

import math
import re

FLUX_TOLERANCE = 0.10  # fluxes within 10% of each other count as "the same"


def normalize_name(name):
    """Planet or star names for matching: lowercase, single spaces ("Kepler-452  b" -> "kepler-452 b")."""
    if not isinstance(name, str):
        return None
    return " ".join(name.lower().split())


def catalog_number(value, prefix):
    """Pull the number out of an identifier such as "HIP 64797 A" or an HTML link to "TIC 373765355".

    Returns the digits as a string (e.g. "64797"), or None if there is no such identifier.
    """
    if not isinstance(value, str):
        return None
    match = re.search(prefix + r"\s*(\d+)", value)
    return match.group(1) if match else None


def precision_recall(predicted, truth):
    """Compare a predicted set of names with an answer-key set.

    precision = share of our planets that are also in the answer key
    recall    = share of the answer key's planets that we found
    """
    predicted, truth = set(predicted), set(truth)
    true_positives = len(predicted & truth)
    return {
        "ours": len(predicted),
        "answer_key": len(truth),
        "in_both": true_positives,
        "only_ours": len(predicted - truth),
        "only_answer_key": len(truth - predicted),
        "precision": true_positives / len(predicted) if predicted else float("nan"),
        "recall": true_positives / len(truth) if truth else float("nan"),
    }


def fluxes_differ(ours, theirs, tolerance=FLUX_TOLERANCE):
    """True if two fluxes differ by more than the tolerance (as a ratio), False if not, None if either is missing."""
    if ours is None or theirs is None or math.isnan(ours) or math.isnan(theirs) or ours <= 0 or theirs <= 0:
        return None
    return abs(math.log(ours / theirs)) > math.log(1 + tolerance)


def disagreement_reason(row):
    """Most likely reason a planet is in only one of the two lists. Rules are tried in order.

    Expected keys (missing ones count as unknown): in_ours, in_bohl, new_since_bohl, updated_since_bohl,
    found_in_our_table, rocky_label, our_radius, our_mass, bohl_radius, bohl_mass, in_bohl_all_hz,
    hz_status, our_flux, our_circular_flux, bohl_flux, bohl_eccentricity, ecc_status.
    """
    get = row.get
    if bool(get("in_ours")) == bool(get("in_bohl")):
        return ""

    def note(reason):
        return reason + ("; also updated in the archive after Bohl's download" if get("updated_since_bohl") else "")

    if get("new_since_bohl"):
        return "new since Bohl's download (first released after 2025-12-20)"
    if get("in_bohl") and not get("found_in_our_table"):
        return "not in our table under this name"

    # Rocky verdict
    if get("in_bohl") and get("rocky_label") not in ("rocky", "possibly rocky"):
        label = get("rocky_label") or "excluded"
        return note(f"different rocky verdict: ours {label} (R={get('our_radius')}, M={get('our_mass')}) "
                    f"vs Bohl R={get('bohl_radius')}, M={get('bohl_mass')}")
    if get("in_ours") and get("in_bohl_all_hz"):
        return note(f"Bohl has it in their HZ but not as rocky (their R={get('bohl_radius')}, M={get('bohl_mass')}; "
                    f"ours R={get('our_radius')}, M={get('our_mass')})")

    # Data we lack
    our_flux = get("our_flux")
    if get("in_bohl") and (our_flux is None or (isinstance(our_flux, float) and math.isnan(our_flux))
                           or get("hz_status") == "missing data"):
        return note("missing flux or star temperature in our table")
    if get("in_bohl") and get("hz_status") == "outside model range":
        return note("star outside our 2600-7200 K model range")

    # Eccentricity: Bohl time-averages the flux; we do only when e is measured
    bohl_e = get("bohl_eccentricity")
    circular = get("our_circular_flux")
    if (bohl_e is not None and not (isinstance(bohl_e, float) and math.isnan(bohl_e)) and 0 < bohl_e < 1
            and get("ecc_status") != "measured" and circular is not None):
        averaged = circular / math.sqrt(1 - bohl_e ** 2)
        if fluxes_differ(circular, get("bohl_flux")) and fluxes_differ(averaged, get("bohl_flux")) is False:
            return note(f"eccentricity: Bohl averages over e={bohl_e}, we used a circular orbit")

    # Different flux values
    if fluxes_differ(our_flux, get("bohl_flux")):
        return note(f"flux differs: ours {our_flux:.2f} vs Bohl {get('bohl_flux'):.2f} S⊕")
    if get("in_ours") and not get("in_bohl_all_hz"):
        return note("not in Bohl's HZ at all: different stellar or orbital parameters (their flux not published)")

    return note("same data, different HZ boundaries (Kopparapu 2014 vs 2013 edges)")
