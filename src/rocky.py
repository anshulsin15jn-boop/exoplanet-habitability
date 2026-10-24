"""Cleaning and rocky-planet classification for the pscomppars table.

Every function returns a new DataFrame and never changes its input. Assignment uses
``.loc`` so the code behaves the same on pandas 2 and pandas 3 (Copy-on-Write).
"""

import numpy as np
import pandas as pd

# Rocky cutoffs and their sources
# Rogers (2015, ApJ, arXiv:1407.4457): most planets of 1.6 Earth radii are not rocky
ROCKY_MAX_RADIUS = 1.6
# Bohl et al. (2026, MNRAS, arXiv:2501.14054) Sections 1 and 3: rocky if <= 2 Earth radii
POSSIBLY_ROCKY_MAX_RADIUS = 2.0
# Bohl et al. (2026) Sections 1 and 3: <= 5 Earth masses for planets without measured radii
ROCKY_MAX_MASS = 5.0

# Columns that must be positive to be physically possible
POSITIVE_COLUMNS = [
    "pl_rade", "pl_bmasse", "pl_orbper", "pl_orbsmax", "pl_insol", "pl_eqt",
    "st_teff", "st_rad", "st_mass", "sy_dist",
]

# pl_bmassprov values that are real measurements (not computed from the radius)
MINIMUM_MASS_TYPES = ["Msini"]
TRUE_MASS_TYPES = ["Mass", "Msin(i)/sin(i)"]

PATH_MEASURED_RADIUS = "measured radius"
PATH_MINIMUM_MASS = "minimum mass"
PATH_EXCLUDED = "excluded"


def clean_impossible_values(planets):
    """Replace physically impossible values with NaN, keeping every row.

    Returns the cleaned copy and a Series with how many values were removed per column.
    """
    clean = planets.copy()
    removed = {}

    for column in POSITIVE_COLUMNS:
        bad = clean[column] <= 0
        removed[column] = int(bad.sum())
        clean.loc[bad, column] = np.nan

    # A bound orbit needs 0 <= e < 1
    bad_eccentricity = (clean["pl_orbeccen"] < 0) | (clean["pl_orbeccen"] >= 1)
    removed["pl_orbeccen"] = int(bad_eccentricity.sum())
    clean.loc[bad_eccentricity, "pl_orbeccen"] = np.nan

    return clean, pd.Series(removed, name="values_removed")


def radius_is_calculated(planets):
    """True where the archive computed the radius from the mass instead of measuring it."""
    return planets["pl_rade_reflink"].str.contains("Calculated Value", na=False)


def assign_rocky_path(planets):
    """Add rocky_path, exclusion_reason and mass_type columns.

    Order of the rules:
    1. microlensing planets are excluded (projected separation, almost no stellar data)
    2. a measured radius is used when there is one
    3. otherwise a measured mass (minimum or true) is used; the estimated radius is ignored
    4. everything else is excluded
    A mass from the "M-R relationship" was computed from the radius, so it never qualifies.
    """
    result = planets.copy()

    is_microlensing = result["discoverymethod"] == "Microlensing"
    has_measured_radius = result["pl_rade"].notna() & ~radius_is_calculated(result)
    has_measured_mass = result["pl_bmasse"].notna() & result["pl_bmassprov"].isin(
        MINIMUM_MASS_TYPES + TRUE_MASS_TYPES
    )

    use_radius = ~is_microlensing & has_measured_radius
    use_mass = ~is_microlensing & ~has_measured_radius & has_measured_mass

    result["rocky_path"] = PATH_EXCLUDED
    result.loc[use_radius, "rocky_path"] = PATH_MEASURED_RADIUS
    result.loc[use_mass, "rocky_path"] = PATH_MINIMUM_MASS

    result["exclusion_reason"] = ""
    result.loc[is_microlensing, "exclusion_reason"] = "microlensing: projected separation, no stellar data"
    no_usable_data = ~is_microlensing & ~use_radius & ~use_mass
    result.loc[no_usable_data, "exclusion_reason"] = "no measured radius and no usable mass"

    result["mass_type"] = ""
    result.loc[use_mass & result["pl_bmassprov"].isin(MINIMUM_MASS_TYPES), "mass_type"] = "minimum"
    result.loc[use_mass & result["pl_bmassprov"].isin(TRUE_MASS_TYPES), "mass_type"] = "true"

    return result


def label_rockiness(planets):
    """Add rocky_label ("rocky", "possibly rocky", "not rocky", or "" for excluded planets).

    Needs the rocky_path column from assign_rocky_path. Planets on the mass path are at most
    "possibly rocky", because mass alone says nothing about what a planet is made of.
    """
    result = planets.copy()
    radius = result["pl_rade"]
    mass = result["pl_bmasse"]
    on_radius_path = result["rocky_path"] == PATH_MEASURED_RADIUS
    on_mass_path = result["rocky_path"] == PATH_MINIMUM_MASS

    result["rocky_label"] = ""

    result.loc[on_radius_path & (radius <= ROCKY_MAX_RADIUS), "rocky_label"] = "rocky"
    result.loc[
        on_radius_path & (radius > ROCKY_MAX_RADIUS) & (radius <= POSSIBLY_ROCKY_MAX_RADIUS),
        "rocky_label",
    ] = "possibly rocky"
    result.loc[on_radius_path & (radius > POSSIBLY_ROCKY_MAX_RADIUS), "rocky_label"] = "not rocky"

    result.loc[on_mass_path & (mass <= ROCKY_MAX_MASS), "rocky_label"] = "possibly rocky"
    result.loc[on_mass_path & (mass > ROCKY_MAX_MASS), "rocky_label"] = "not rocky"

    return result
