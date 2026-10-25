import math

import pytest

from src import compare


def test_normalize_name():
    assert compare.normalize_name("  Kepler-452   B ") == "kepler-452 b"
    assert compare.normalize_name(None) is None


def test_catalog_number_handles_links_and_components():
    html = '<a href="https://exoplanetarchive.ipac.caltech.edu/overview/TIC 373765355" target=_blank>TIC 373765355</a>'
    assert compare.catalog_number(html, "TIC") == "373765355"
    assert compare.catalog_number("HIP 64797 A", "HIP") == "64797"
    assert compare.catalog_number("HIP 64797", "HIP") == "64797"
    assert compare.catalog_number(None, "HIP") is None
    assert compare.catalog_number("HD 115404", "HIP") is None


def test_precision_recall_hand_example():
    result = compare.precision_recall({"a", "b", "c", "d"}, {"b", "c", "e"})
    assert result["in_both"] == 2
    assert result["precision"] == pytest.approx(2 / 4)
    assert result["recall"] == pytest.approx(2 / 3)
    assert result["only_ours"] == 2 and result["only_answer_key"] == 1


def test_precision_recall_empty_sets():
    result = compare.precision_recall(set(), {"a"})
    assert math.isnan(result["precision"])
    assert result["recall"] == 0


def test_fluxes_differ():
    assert compare.fluxes_differ(1.0, 1.05) is False
    assert compare.fluxes_differ(1.0, 1.5) is True
    assert compare.fluxes_differ(1.0, float("nan")) is None


def test_reason_new_planet():
    row = {"in_ours": True, "in_bohl": False, "new_since_bohl": True}
    assert compare.disagreement_reason(row).startswith("new since")


def test_reason_agreement_is_empty():
    assert compare.disagreement_reason({"in_ours": True, "in_bohl": True}) == ""


def test_reason_rocky_verdict():
    row = {"in_ours": False, "in_bohl": True, "found_in_our_table": True, "rocky_label": "not rocky",
           "our_radius": 2.3, "bohl_radius": 1.9}
    assert compare.disagreement_reason(row).startswith("different rocky verdict")


def test_reason_flux_difference_and_update_note():
    row = {"in_ours": False, "in_bohl": True, "found_in_our_table": True, "rocky_label": "rocky",
           "hz_status": "too cold", "our_flux": 0.21, "bohl_flux": 0.27, "updated_since_bohl": True}
    reason = compare.disagreement_reason(row)
    assert reason.startswith("flux differs")
    assert reason.endswith("after Bohl's download")


def test_reason_eccentricity():
    # Circular 1.0 vs Bohl's 1.25: the gap disappears once we average over e = 0.6 (1 / 0.8 = 1.25)
    row = {"in_ours": False, "in_bohl": True, "found_in_our_table": True, "rocky_label": "rocky",
           "hz_status": "too hot", "our_flux": 1.0, "our_circular_flux": 1.0, "bohl_flux": 1.25,
           "bohl_eccentricity": 0.6, "ecc_status": "assumed zero"}
    assert compare.disagreement_reason(row).startswith("eccentricity")


def test_reason_model_range():
    row = {"in_ours": False, "in_bohl": True, "found_in_our_table": True, "rocky_label": "rocky",
           "hz_status": "outside model range", "our_flux": 0.25}
    assert compare.disagreement_reason(row).startswith("star outside")


def test_reason_same_data_different_boundary():
    row = {"in_ours": True, "in_bohl": False, "rocky_label": "rocky", "in_bohl_all_hz": False,
           "our_flux": 1.0, "bohl_flux": None}
    assert compare.disagreement_reason(row).startswith("not in Bohl's HZ at all")
    row = {"in_ours": False, "in_bohl": True, "found_in_our_table": True, "rocky_label": "rocky",
           "hz_status": "too hot", "our_flux": 1.50, "bohl_flux": 1.48}
    assert compare.disagreement_reason(row).startswith("same data")
