import numpy as np
import pandas as pd
import pytest

from src import physics


def test_earth_insolation_is_one():
    # The Sun (L = 1) at 1 AU gives Earth's flux
    assert physics.insolation(1.0, 1.0) == pytest.approx(1.0)


def test_insolation_follows_inverse_square_law():
    assert physics.insolation(1.0, 2.0) == pytest.approx(0.25)
    assert physics.insolation(4.0, 2.0) == pytest.approx(1.0)


def test_luminosity_from_log():
    assert physics.luminosity_from_log(0.0) == pytest.approx(1.0)
    assert physics.luminosity_from_log(-1.0) == pytest.approx(0.1)


def test_sun_luminosity_from_radius_and_temperature():
    assert physics.luminosity_from_radius_teff(1.0, 5772.0) == pytest.approx(1.0)
    # Twice the radius means four times the surface area
    assert physics.luminosity_from_radius_teff(2.0, 5772.0) == pytest.approx(4.0)


def test_earth_equilibrium_temperature():
    # Earth's albedo 0.3 gives the textbook value of about 255 K
    assert physics.equilibrium_temperature(1.0, 0.3) == pytest.approx(255.0, abs=1.0)
    assert physics.equilibrium_temperature(1.0, 0.0) == pytest.approx(278.3, abs=0.1)


def test_orbit_averaged_flux():
    assert physics.orbit_averaged_flux(1.0, 0.0) == pytest.approx(1.0)
    # sqrt(1 - 0.6^2) = 0.8, so the average flux is 1 / 0.8 = 1.25 times higher
    assert physics.orbit_averaged_flux(1.0, 0.6) == pytest.approx(1.25)


def test_orbit_averaged_flux_rejects_unbound_orbits():
    assert np.isnan(physics.orbit_averaged_flux(1.0, 1.0))
    assert np.isnan(physics.orbit_averaged_flux(1.0, -0.1))


def test_functions_work_on_pandas_series():
    luminosity = pd.Series([1.0, 4.0])
    distance = pd.Series([1.0, 2.0])
    flux = physics.insolation(luminosity, distance)
    assert list(flux) == pytest.approx([1.0, 1.0])

    averaged = physics.orbit_averaged_flux(pd.Series([1.0, 1.0, 1.0]), pd.Series([0.0, 0.6, np.nan]))
    assert averaged.iloc[0] == pytest.approx(1.0)
    assert averaged.iloc[1] == pytest.approx(1.25)
    assert np.isnan(averaged.iloc[2])


def test_parsec_to_light_years():
    assert physics.parsecs_to_light_years(1.0) == pytest.approx(3.2616, abs=1e-4)
