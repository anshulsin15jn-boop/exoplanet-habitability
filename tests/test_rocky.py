import numpy as np
import pandas as pd

from src import rocky

CALCULATED = "<a refstr=CALCULATED_VALUE href=/docs/pscp_calc.html>Calculated Value</a>"
MEASURED = "<a refstr=SOME_PAPER>Some et al. 2021</a>"


def make_planet(**values):
    """One-row table with sensible defaults; keyword arguments override them."""
    planet = {
        "pl_name": "Test b",
        "discoverymethod": "Transit",
        "pl_rade": 1.0,
        "pl_rade_reflink": MEASURED,
        "pl_bmasse": 1.0,
        "pl_bmassprov": "Mass",
        "pl_orbper": 10.0,
        "pl_orbsmax": 0.1,
        "pl_orbeccen": 0.0,
        "pl_insol": 1.0,
        "pl_eqt": 255.0,
        "st_teff": 5772.0,
        "st_rad": 1.0,
        "st_mass": 1.0,
        "sy_dist": 10.0,
    }
    planet.update(values)
    return pd.DataFrame([planet])


def classify(planets):
    return rocky.label_rockiness(rocky.assign_rocky_path(planets))


def test_radius_boundaries():
    planets = pd.concat([make_planet(pl_rade=r) for r in [1.6, 1.61, 2.0, 2.01]])
    labels = list(classify(planets)["rocky_label"])
    assert labels == ["rocky", "possibly rocky", "possibly rocky", "not rocky"]


def test_mass_boundaries_for_minimum_mass():
    planets = pd.concat([
        make_planet(discoverymethod="Radial Velocity", pl_rade=1.0, pl_rade_reflink=CALCULATED,
                    pl_bmasse=m, pl_bmassprov="Msini")
        for m in [5.0, 5.01]
    ])
    result = classify(planets)
    assert list(result["rocky_path"]) == ["minimum mass", "minimum mass"]
    assert list(result["mass_type"]) == ["minimum", "minimum"]
    assert list(result["rocky_label"]) == ["possibly rocky", "not rocky"]


def test_estimated_radius_is_ignored_for_radial_velocity():
    # The archive's calculated radius says "rocky", but the minimum mass of 12 says no
    planet = make_planet(discoverymethod="Radial Velocity", pl_rade=1.0, pl_rade_reflink=CALCULATED,
                         pl_bmasse=12.0, pl_bmassprov="Msini")
    result = classify(planet).iloc[0]
    assert result["rocky_path"] == "minimum mass"
    assert result["rocky_label"] == "not rocky"


def test_mass_from_radius_never_confirms_rockiness():
    # Circularity guard: a mass computed from the radius must not override the radius
    planet = make_planet(pl_rade=3.0, pl_bmasse=1.0, pl_bmassprov="M-R relationship")
    result = classify(planet).iloc[0]
    assert result["rocky_path"] == "measured radius"
    assert result["rocky_label"] == "not rocky"


def test_mass_from_radius_never_puts_a_planet_on_the_mass_path():
    planet = make_planet(pl_rade=np.nan, pl_bmasse=1.0, pl_bmassprov="M-R relationship")
    result = classify(planet).iloc[0]
    assert result["rocky_path"] == "excluded"
    assert result["exclusion_reason"] == "no measured radius and no usable mass"


def test_microlensing_is_excluded():
    planet = make_planet(discoverymethod="Microlensing", pl_rade=1.0, pl_rade_reflink=CALCULATED,
                         pl_bmasse=2.0, pl_bmassprov="Mass")
    result = classify(planet).iloc[0]
    assert result["rocky_path"] == "excluded"
    assert result["exclusion_reason"].startswith("microlensing")
    assert result["rocky_label"] == ""


def test_impossible_values_become_missing_and_rows_are_kept():
    planets = pd.concat([make_planet(pl_rade=0.0), make_planet(pl_orbeccen=1.2)])
    clean, removed = rocky.clean_impossible_values(planets)
    assert len(clean) == 2
    assert np.isnan(clean["pl_rade"].iloc[0])
    assert np.isnan(clean["pl_orbeccen"].iloc[1])
    assert removed["pl_rade"] == 1
    assert removed["pl_orbeccen"] == 1


def test_input_is_not_changed():
    planets = make_planet(pl_rade=0.0)
    rocky.clean_impossible_values(planets)
    classify(planets)
    assert planets["pl_rade"].iloc[0] == 0.0
    assert "rocky_path" not in planets.columns
