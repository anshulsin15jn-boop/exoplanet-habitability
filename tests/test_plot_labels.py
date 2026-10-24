from itertools import combinations

from src import plot_labels


def test_lone_label_goes_to_first_choice():
    boxes = plot_labels.place_labels([(100, 100)], [(40, 10)], first_distance=6)
    # First choice: to the right of the point, vertically centered
    assert boxes == [(106, 95, 146, 105)]


def test_labels_never_overlap_each_other_or_obstacles():
    # Ten points squeezed together, plus an obstacle right next to them
    anchors = [(200 + 3 * i, 200 + 2 * i) for i in range(10)]
    sizes = [(60, 12)] * 10
    obstacles = [(190, 190, 260, 230)]
    boxes = plot_labels.place_labels(anchors, sizes, obstacles)
    assert all(box is not None for box in boxes)
    for a, b in combinations(boxes, 2):
        assert not plot_labels.boxes_overlap(a, b)
    for box in boxes:
        assert not plot_labels.boxes_overlap(box, obstacles[0])


def test_crowded_labels_move_outward():
    anchors = [(100, 100), (100, 100)]
    boxes = plot_labels.place_labels(anchors, [(40, 10), (40, 10)], first_distance=6)
    first, second = boxes
    assert first != second
    assert not plot_labels.boxes_overlap(first, second)


def test_labels_stay_inside_bounds():
    bounds = (0, 0, 120, 120)
    boxes = plot_labels.place_labels([(110, 60)], [(40, 10)], bounds=bounds)
    assert plot_labels.box_inside(boxes[0], bounds)
    # Not enough room to the right, so the label goes elsewhere
    assert boxes[0][2] <= 110


def test_returns_none_when_there_is_no_room():
    boxes = plot_labels.place_labels([(10, 10)], [(500, 500)], bounds=(0, 0, 50, 50))
    assert boxes == [None]


def test_result_is_deterministic():
    anchors = [(50 + 7 * i, 80 - 5 * i) for i in range(6)]
    sizes = [(30 + i, 10) for i in range(6)]
    assert plot_labels.place_labels(anchors, sizes) == plot_labels.place_labels(anchors, sizes)
