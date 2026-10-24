"""Reusable physics functions for the exoplanet habitability project.

All functions work on single numbers and on pandas Series / NumPy arrays.
Units: luminosity and radius in solar units, distances in AU, flux in Earth units
(1 = what Earth receives from the Sun), temperatures in kelvin.
"""

import numpy as np

# IAU 2015 Resolution B3 nominal solar values (exact conversion constants)
SUN_TEFF = 5772.0  # K
SOLAR_IRRADIANCE = 1361.0  # W m^-2 at 1 AU

# CODATA exact value of the Stefan-Boltzmann constant
STEFAN_BOLTZMANN = 5.670374419e-8  # W m^-2 K^-4

# Equilibrium temperature of a black body at 1 AU with no albedo, full heat redistribution:
# T0 = (S0 / (4 sigma))^(1/4), about 278.3 K. (Using the older S0 = 1367 W m^-2 gives 278.6 K.)
T_EQ_EARTH_NO_ALBEDO = (SOLAR_IRRADIANCE / (4 * STEFAN_BOLTZMANN)) ** 0.25

# Distance units: 1 parsec = 648000/pi AU (IAU 2015 B2), 1 AU = 149,597,870,700 m (IAU 2012 B2),
# 1 light year = speed of light x one Julian year (365.25 days)
AU_IN_M = 149_597_870_700.0
PARSEC_IN_M = 648_000 / np.pi * AU_IN_M
LIGHT_YEAR_IN_M = 299_792_458.0 * 365.25 * 86_400
LIGHT_YEARS_PER_PARSEC = PARSEC_IN_M / LIGHT_YEAR_IN_M  # about 3.2616


def luminosity_from_log(log_luminosity):
    """Convert the archive's st_lum (log10 of L / L_sun) to L / L_sun."""
    return 10.0 ** log_luminosity


def luminosity_from_radius_teff(radius, teff):
    """Stefan-Boltzmann law in solar units: L = R^2 (Teff / 5772 K)^4."""
    return radius ** 2 * (teff / SUN_TEFF) ** 4


def insolation(luminosity, semimajor_axis):
    """Flux at the planet in Earth units: S = L / a^2 (inverse-square law)."""
    return luminosity / semimajor_axis ** 2


def orbit_averaged_flux(flux, eccentricity):
    """Time-averaged flux over an eccentric orbit: S / sqrt(1 - e^2).

    ``flux`` is the flux at the semimajor axis. Returns NaN unless 0 <= e < 1.
    Sources: Williams & Pollard (2002); Bolmont et al. (2016, A&A 591, A106).
    """
    is_bound_orbit = (eccentricity >= 0) & (eccentricity < 1)
    safe_eccentricity = np.where(is_bound_orbit, eccentricity, np.nan)
    return flux / np.sqrt(1 - safe_eccentricity ** 2)


def equilibrium_temperature(flux, albedo):
    """Equilibrium temperature in K: T0 * S^(1/4) * (1 - albedo)^(1/4).

    Assumes the planet radiates as a black body and spreads heat evenly over its surface.
    """
    return T_EQ_EARTH_NO_ALBEDO * flux ** 0.25 * (1 - albedo) ** 0.25


def parsecs_to_light_years(distance_pc):
    """Convert parsecs to light years."""
    return distance_pc * LIGHT_YEARS_PER_PARSEC
