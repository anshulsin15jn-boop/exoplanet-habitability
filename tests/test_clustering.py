import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import adjusted_rand_score

from src import clustering


def test_build_features_takes_logs_and_drops_incomplete_rows():
    planets = pd.DataFrame({
        "pl_rade": [1.0, 10.0, np.nan, 2.0],
        "hz_flux": [1.0, 100.0, 1.0, 0.0],
        "pl_orbper": [365.256, 10.0, 5.0, 5.0],
        "st_teff": [5772.0, 4000.0, 3000.0, 3000.0],
    }, index=[10, 11, 12, 13])
    features = clustering.build_features(planets)
    # Row 12 has no radius and row 13 has zero flux, so only 10 and 11 remain
    assert list(features.index) == [10, 11]
    assert features.loc[11, "log_radius"] == pytest.approx(1.0)
    assert features.loc[11, "log_flux"] == pytest.approx(2.0)
    assert features.loc[11, "st_teff"] == 4000.0


def test_earth_features():
    earth = clustering.earth_features()
    assert earth["log_radius"].iloc[0] == pytest.approx(0.0)
    assert earth["log_flux"].iloc[0] == pytest.approx(0.0)
    assert earth["log_period"].iloc[0] == pytest.approx(np.log10(365.256))


def test_similarity_is_one_for_earth_and_lower_further_away():
    earth = np.array([[0.0, 0.0]])
    planets = np.array([[0.0, 0.0], [1.0, 0.0], [-1.0, 0.0], [3.0, 4.0]])
    scores = clustering.similarity_to_earth(planets, earth)
    assert scores[0] == pytest.approx(1.0)
    assert scores[1] == pytest.approx(0.5)
    assert scores[1] == pytest.approx(scores[2])      # same distance in either direction
    assert scores[3] == pytest.approx(1 / 6)          # distance 5


def test_earth_similarity_index_is_one_for_earth():
    assert clustering.earth_similarity_index(1.0, 1.0) == 1.0


def test_earth_similarity_index_hand_computed_values():
    # S = R = 3: each term is ((3 - 1) / (3 + 1))^2 = 0.25, so ESI = 1 - sqrt(0.25) = 0.5
    assert clustering.earth_similarity_index(3.0, 3.0) == pytest.approx(0.5)
    # S = 1, R = 2: only the radius term, (1/3)^2; ESI = 1 - sqrt(0.5 / 9)
    assert clustering.earth_similarity_index(1.0, 2.0) == pytest.approx(1 - np.sqrt(0.5 / 9))
    # Works on arrays
    values = clustering.earth_similarity_index(np.array([1.0, 3.0]), np.array([1.0, 3.0]))
    assert values == pytest.approx([1.0, 0.5])


def three_blobs():
    rng = np.random.default_rng(0)
    centers = np.array([[0, 0], [10, 0], [0, 10]])
    points = np.vstack([center + rng.normal(0, 0.5, size=(30, 2)) for center in centers])
    truth = np.repeat([0, 1, 2], 30)
    return points, truth


def test_kmeans_recovers_clear_clusters_and_is_reproducible():
    points, truth = three_blobs()
    first = clustering.fit_kmeans(points, 3, seed=0).labels_
    again = clustering.fit_kmeans(points, 3, seed=0).labels_
    assert adjusted_rand_score(truth, first) == pytest.approx(1.0)
    assert list(first) == list(again)
    assert all(score == pytest.approx(1.0) for score in clustering.seed_stability(points, 3))


def test_order_clusters_sorts_by_median():
    labels = [5, 5, 7, 7, 9, 9]
    values = [1.0, 1.0, 100.0, 100.0, 10.0, 10.0]
    ordered, mapping = clustering.order_clusters(labels, values)
    assert list(ordered) == [2, 2, 0, 0, 1, 1]
    assert mapping == {7: 0, 9: 1, 5: 2}
