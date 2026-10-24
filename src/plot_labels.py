"""Place text labels next to points without overlapping each other or other obstacles.

Pure geometry in pixel coordinates, so it can be tested without drawing anything.
A box is (x0, y0, x1, y1) with x0 < x1 and y0 < y1; pixel y grows upward, as in Matplotlib.
"""

# Directions tried around each point, in order of preference (right first, then clockwise-ish)
DIRECTIONS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]


def boxes_overlap(a, b):
    """True if two boxes share any area."""
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def box_inside(inner, outer):
    """True if box `inner` lies completely inside box `outer`."""
    return inner[0] >= outer[0] and inner[1] >= outer[1] and inner[2] <= outer[2] and inner[3] <= outer[3]


def candidate_box(anchor, size, direction, distance):
    """Box of the given size placed `distance` pixels from the anchor in one direction."""
    ax, ay = anchor
    width, height = size
    dx, dy = direction
    # Horizontal position: to the right, to the left, or centered on the point
    if dx > 0:
        x0 = ax + distance
    elif dx < 0:
        x0 = ax - distance - width
    else:
        x0 = ax - width / 2
    # Vertical position: above, below, or centered on the point
    if dy > 0:
        y0 = ay + distance
    elif dy < 0:
        y0 = ay - distance - height
    else:
        y0 = ay - height / 2
    return (x0, y0, x0 + width, y0 + height)


def annotate_without_overlap(ax, xs, ys, texts, obstacle_xs=(), obstacle_ys=(), obstacle_radius=6,
                             extra_obstacles=(), fontsize=8, color="#0b0b0b", line_color="#898781"):
    """Label points on a Matplotlib axes so no two labels overlap.

    xs, ys, texts: the points to label, most important first (data coordinates).
    obstacle_xs, obstacle_ys: other markers that labels must not cover (data coordinates).
    extra_obstacles: pixel boxes to avoid as well (e.g. a legend inside the axes).
    Returns (drawn text artists, texts that could not be placed).
    """
    figure = ax.figure
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    # A light, slightly transparent box behind each label keeps it readable over dense points
    text_style = {"fontsize": fontsize, "color": color,
                  "bbox": {"boxstyle": "square,pad=0.15", "facecolor": "#fcfcfb", "edgecolor": "none", "alpha": 0.85}}

    anchors = [tuple(p) for p in ax.transData.transform(list(zip(xs, ys)))]
    sizes = []
    for text in texts:
        probe = ax.text(0, 0, text, **text_style)
        extent = probe.get_window_extent(renderer)
        # Extra pixels leave room for the background box padding
        sizes.append((extent.width + 6, extent.height + 6))
        probe.remove()

    marker_boxes = [
        (px - obstacle_radius, py - obstacle_radius, px + obstacle_radius, py + obstacle_radius)
        for px, py in ax.transData.transform(list(zip(obstacle_xs, obstacle_ys)))
    ] if len(obstacle_xs) else []
    plot_area = ax.get_window_extent(renderer)
    bounds = (plot_area.x0, plot_area.y0, plot_area.x1, plot_area.y1)

    boxes = place_labels(anchors, sizes, marker_boxes + list(extra_obstacles), bounds)

    drawn, skipped = [], []
    to_data = ax.transData.inverted()
    for (x, y), text, box in zip(zip(xs, ys), texts, boxes):
        if box is None:
            skipped.append(text)
            continue
        text_x, text_y = to_data.transform((box[0] + 3, box[1] + 3))
        artist = ax.annotate(
            text, xy=(x, y), xytext=(text_x, text_y), textcoords="data", **text_style,
            ha="left", va="bottom", zorder=6,
            arrowprops={"arrowstyle": "-", "color": line_color, "linewidth": 0.6, "shrinkA": 0, "shrinkB": 3},
        )
        drawn.append(artist)
    return drawn, skipped


def text_boxes_overlap(artists):
    """After drawing, check the real text boxes: True if any two labels overlap."""
    from matplotlib.text import Text

    if not artists:
        return False
    # Annotation positions are only computed when the figure is drawn
    artists[0].figure.canvas.draw()
    renderer = artists[0].figure.canvas.get_renderer()
    boxes = []
    for artist in artists:
        # Text.get_window_extent measures only the text; an Annotation's own extent also covers its leader line
        extent = Text.get_window_extent(artist, renderer)
        boxes.append((extent.x0, extent.y0, extent.x1, extent.y1))
    return any(boxes_overlap(a, b) for i, a in enumerate(boxes) for b in boxes[i + 1:])


def place_labels(anchors, sizes, obstacles=(), bounds=None, first_distance=6, step=8, max_rings=15):
    """Choose a box for each label, in the order given (put the most important labels first).

    anchors: (x, y) pixel position of each labelled point.
    sizes: (width, height) of each label in pixels.
    obstacles: boxes that labels must not cover (markers, legend, ...).
    bounds: optional box that every label must stay inside (e.g. the plot area).
    Returns a list with one box per label, or None where no free spot was found.
    """
    placed = []
    result = []
    for anchor, size in zip(anchors, sizes):
        chosen = None
        for ring in range(max_rings):
            distance = first_distance + ring * step
            for direction in DIRECTIONS:
                box = candidate_box(anchor, size, direction, distance)
                if bounds is not None and not box_inside(box, bounds):
                    continue
                if any(boxes_overlap(box, other) for other in placed):
                    continue
                if any(boxes_overlap(box, other) for other in obstacles):
                    continue
                chosen = box
                break
            if chosen is not None:
                break
        result.append(chosen)
        if chosen is not None:
            placed.append(chosen)
    return result
