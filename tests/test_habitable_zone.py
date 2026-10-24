import numpy as np
import pytest

from src import habitable_zone as hz

ALL_TABLES = [
    hz.KOPPARAPU_2014["recent_venus"], hz.KOPPARAPU_2014["runaway_greenhouse"],
    hz.KOPPARAPU_2014["maximum_greenhouse"], hz.KOPPARAPU_2014["early_mars"],
    hz.KOPPARAPU_2013["recent_venus"], hz.KOPPARAPU_2013["early_mars"],
    hz.RAMIREZ_KALTENEGGER_2018_LECONTE,
]


@pytest.mark.parametrize("coefficients", ALL_TABLES)
def test_reference_temperature_gives_solar_value(coefficients):
    # At Teff = 5780 K every polynomial term is zero, leaving S_sun
    assert hz.hz_flux_limit(5780.0, coefficients) == pytest.approx(coefficients[0])


@pytest.mark.parametrize("teff, recent_venus, early_mars", [
    (2829.35, 1.49, 0.20),  # Proxima Cen b
    (3096.0, 1.50, 0.21),   # LHS 1140 b
    (3382.0, 1.52, 0.22),   # GJ 273 b
])
def test_kopparapu_2013_reproduces_bohl_table_1(teff, recent_venus, early_mars):
    # Bohl et al. (2026) Table 1 prints these limits rounded to 2 decimals
    assert hz.hz_flux_limit(teff, hz.KOPPARAPU_2013["recent_venus"]) == pytest.approx(recent_venus, abs=0.006)
    assert hz.hz_flux_limit(teff, hz.KOPPARAPU_2013["early_mars"]) == pytest.approx(early_mars, abs=0.006)


def k14_status(flux, teff, inner="recent_venus", outer="early_mars"):
    inner_limit = hz.hz_flux_limit(teff, hz.KOPPARAPU_2014[inner], hz.KOPPARAPU_TEFF_RANGE)
    outer_limit = hz.hz_flux_limit(teff, hz.KOPPARAPU_2014[outer], hz.KOPPARAPU_TEFF_RANGE)
    return hz.hz_status([flux], inner_limit, outer_limit, [teff], hz.KOPPARAPU_TEFF_RANGE)[0]


def test_solar_system_planets():
    assert k14_status(1.0, 5780.0) == "inside"                      # Earth, optimistic
    assert k14_status(1.0, 5780.0, "runaway_greenhouse", "maximum_greenhouse") == "inside"  # Earth, conservative
    assert k14_status(1.91, 5780.0) == "too hot"                    # Venus
    assert k14_status(0.43, 5780.0) == "inside"                     # Mars, optimistic
    assert k14_status(0.04, 5780.0) == "too cold"                   # Jupiter


def test_outside_model_range_is_not_extrapolated():
    assert k14_status(0.65, 2566.0) == "outside model range"        # TRAPPIST-1 e
    assert k14_status(1.0, 7500.0) == "outside model range"
    assert np.isnan(hz.hz_flux_limit(2566.0, hz.KOPPARAPU_2014["early_mars"], hz.KOPPARAPU_TEFF_RANGE))


def test_missing_values():
    assert k14_status(np.nan, 5780.0) == "missing data"
    assert k14_status(1.0, np.nan) == "missing data"


def test_clamp_teff_moves_only_out_of_range_values():
    clamped = hz.clamp_teff(np.array([2566.0, 5000.0, 8000.0]), hz.KOPPARAPU_TEFF_RANGE)
    assert list(clamped) == [2600.0, 5000.0, 7200.0]


def test_simple_window_ignores_temperature():
    statuses = hz.hz_status([1.0, 1.0, 2.0], 1.776, 0.32)
    assert list(statuses) == ["inside", "inside", "too hot"]
