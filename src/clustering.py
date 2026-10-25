"""Feature building, KMeans helpers, and similarity-to-Earth scores for Phase 5."""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score

FEATURE_COLUMNS = ["log_radius", "log_flux", "log_period", "st_teff"]

# Earth's values in the same units as the archive columns.
# Orbital period: the sidereal year, 365.256 days. Star: the Sun's nominal Teff (IAU 2015 B3).
EARTH = {"pl_rade": 1.0, "hz_flux": 1.0, "pl_orbper": 365.256, "st_teff": 5772.0}


def build_features(planets):
    """Return the four clustering features for planets that have all of them.

    log10 is taken for radius, flux and period because they span many powers of ten.
    Rows with a missing or non-positive input are left out. The index matches ``planets``.
    """
    inputs = planets[["pl_rade", "hz_flux", "pl_orbper", "st_teff"]]
    complete = inputs.notna().all(axis=1) & (inputs[["pl_rade", "hz_flux", "pl_orbper"]] > 0).all(axis=1)
    usable = inputs[complete]
    return pd.DataFrame({
        "log_radius": np.log10(usable["pl_rade"]),
        "log_flux": np.log10(usable["hz_flux"]),
        "log_period": np.log10(usable["pl_orbper"]),
        "st_teff": usable["st_teff"],
    }, index=usable.index)


def earth_features():
    """Earth as a one-row feature table, built the same way as the planets."""
    return build_features(pd.DataFrame([EARTH]))


def fit_kmeans(scaled, k, seed=0, n_init=10):
    """KMeans with a fixed seed so the result is reproducible."""
    return KMeans(n_clusters=k, n_init=n_init, random_state=seed).fit(scaled)


def seed_stability(scaled, k, seeds=(0, 1, 2, 3, 4), n_init=10):
    """Adjusted Rand index between the first seed's clustering and each other seed's (1 = identical)."""
    runs = [fit_kmeans(scaled, k, seed, n_init).labels_ for seed in seeds]
    return [adjusted_rand_score(runs[0], labels) for labels in runs[1:]]


def order_clusters(labels, sort_values):
    """Renumber clusters so cluster 0 has the highest median of sort_values, 1 the next, and so on.

    KMeans numbers clusters arbitrarily; a fixed order makes colors and names stable.
    """
    labels = np.asarray(labels)
    medians = pd.Series(sort_values).groupby(labels).median()
    new_number = {old: new for new, old in enumerate(medians.sort_values(ascending=False).index)}
    return np.array([new_number[label] for label in labels]), new_number


def earth_similarity_index(flux, radius):
    """Simplified Earth Similarity Index from stellar flux S and radius R, both in Earth units.

    ESI = 1 - sqrt(0.5 * [((S - 1)/(S + 1))^2 + ((R - 1)/(R + 1))^2])
    Source: Dabhade et al. (2025, arXiv:2512.00899), eq. 7, after Schulze-Makuch et al. (2011).
    Earth scores exactly 1; the score falls toward 0 for planets unlike Earth.
    """
    flux_term = ((flux - 1) / (flux + 1)) ** 2
    radius_term = ((radius - 1) / (radius + 1)) ** 2
    return 1 - np.sqrt(0.5 * (flux_term + radius_term))


def similarity_to_earth(scaled, earth_scaled):
    """Similarity score 1 / (1 + distance), where distance is measured in the scaled feature space.

    Earth itself scores exactly 1; the farther a planet is from Earth, the closer the score gets to 0.
    """
    distance = np.sqrt(((np.asarray(scaled) - np.asarray(earth_scaled)) ** 2).sum(axis=1))
    return 1.0 / (1.0 + distance)
