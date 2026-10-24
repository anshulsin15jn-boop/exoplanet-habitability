"""Habitable zone (HZ) boundaries as a function of stellar temperature.

Every boundary uses the same fourth-order polynomial (Kopparapu et al. 2013, 2014):

    S_eff = S_sun + a*T + b*T^2 + c*T^3 + d*T^4,   with T = Teff - 5780 K

S_eff is the flux (in Earth units) at the boundary. A planet receiving more flux than the
inner boundary is "too hot"; less than the outer boundary is "too cold".
Each coefficient tuple is (S_sun, a, b, c, d), copied from the table named above it.
"""

import numpy as np

TEFF_REFERENCE = 5780.0  # K, the T = Teff - 5780 K used in all three papers

# Kopparapu et al. (2014, ApJL 787, L29), Table 1, 1 Earth-mass planet. Valid 2600-7200 K (Section 3.1).
KOPPARAPU_2014 = {
    "recent_venus":       (1.776, 2.136e-4, 2.533e-8, -1.332e-11, -3.097e-15),
    "runaway_greenhouse": (1.107, 1.332e-4, 1.58e-8, -8.308e-12, -1.931e-15),
    "maximum_greenhouse": (0.356, 6.171e-5, 1.698e-9, -3.198e-12, -5.575e-16),
    "early_mars":         (0.32, 5.547e-5, 1.526e-9, -2.874e-12, -5.011e-16),
}
KOPPARAPU_TEFF_RANGE = (2600.0, 7200.0)

# Kopparapu et al. (2013, ApJ 765, 131), Table 3 (arXiv:1301.6674v2). Valid 2600-7200 K (Section 4.1).
# Bohl et al. (2026) cite this paper for their empirical HZ; these values reproduce their Table 1.
KOPPARAPU_2013 = {
    "recent_venus":       (1.7753, 1.4316e-4, 2.9875e-9, -7.5702e-12, -1.1635e-15),
    "runaway_greenhouse": (1.0512, 1.3242e-4, 1.5418e-8, -7.9895e-12, -1.8328e-15),
    "moist_greenhouse":   (1.0140, 8.1774e-5, 1.7063e-9, -4.3241e-12, -6.6462e-16),
    "maximum_greenhouse": (0.3438, 5.8942e-5, 1.6558e-9, -3.0045e-12, -5.2983e-16),
    "early_mars":         (0.3179, 5.4513e-5, 1.5313e-9, -2.7786e-12, -4.8997e-16),
}

# Ramirez & Kaltenegger (2018, ApJ 858, 72), Table 2, "Leconte et al." column: the 3D-model inner
# edge that Bohl et al. (2026) use for their narrower 3D HZ. Valid 2600-10,000 K.
RAMIREZ_KALTENEGGER_2018_LECONTE = (1.105, 1.1921e-4, 9.5932e-9, -2.6189e-12, 1.3710e-16)
RAMIREZ_KALTENEGGER_TEFF_RANGE = (2600.0, 10000.0)

INSIDE = "inside"
TOO_HOT = "too hot"
TOO_COLD = "too cold"
OUTSIDE_MODEL_RANGE = "outside model range"
MISSING_DATA = "missing data"


def in_teff_range(teff, teff_range):
    """True where teff lies inside [low, high] (inclusive)."""
    low, high = teff_range
    return (teff >= low) & (teff <= high)


def clamp_teff(teff, teff_range):
    """Move temperatures outside [low, high] to the nearest edge (e.g. 2566 K -> 2600 K).

    Used only for the flagged "limits evaluated at the nearest valid temperature" caveat,
    never for the strict HZ flags.
    """
    low, high = teff_range
    return np.clip(teff, low, high)


def hz_flux_limit(teff, coefficients, teff_range=None):
    """Flux at one HZ boundary for a star of temperature teff.

    If teff_range is given, stars outside it get NaN instead of an extrapolated value.
    """
    s_sun, a, b, c, d = coefficients
    t = teff - TEFF_REFERENCE
    limit = s_sun + a * t + b * t ** 2 + c * t ** 3 + d * t ** 4
    if teff_range is not None:
        limit = np.where(in_teff_range(teff, teff_range), limit, np.nan)
    return limit


def hz_status(flux, inner, outer, teff=None, teff_range=None):
    """Classify each planet as inside, too hot, too cold, outside model range, or missing data.

    inner and outer are the boundary fluxes (numbers or arrays). If teff_range is given, stars
    outside it are labelled "outside model range" instead of being compared with the limits.
    """
    flux = np.asarray(flux, dtype=float)
    inner = np.broadcast_to(np.asarray(inner, dtype=float), flux.shape)
    outer = np.broadcast_to(np.asarray(outer, dtype=float), flux.shape)

    missing = np.isnan(flux)
    outside_range = np.zeros(flux.shape, dtype=bool)
    if teff_range is not None:
        teff = np.asarray(teff, dtype=float)
        missing = missing | np.isnan(teff)
        outside_range = ~missing & ~in_teff_range(teff, teff_range)

    conditions = [
        missing,
        outside_range,
        flux > inner,
        flux < outer,
    ]
    choices = [MISSING_DATA, OUTSIDE_MODEL_RANGE, TOO_HOT, TOO_COLD]
    return np.select(conditions, choices, default=INSIDE)
