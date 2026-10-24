"""Shared colors and Matplotlib settings so every figure in the project looks the same.

Series colors come in a fixed order (blue, orange, aqua) that was checked for
colorblind-safe contrast on the light background.
"""

import matplotlib as mpl

SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
TEXT_MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]  # blue, orange, aqua: use in this order
SHADE = "#f0efec"  # light neutral for shaded regions


def apply_style():
    """Set Matplotlib defaults: light surface, thin recessive axes and grid, readable text."""
    mpl.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "axes.edgecolor": AXIS,
        "axes.labelcolor": TEXT_PRIMARY,
        "axes.titlecolor": TEXT_PRIMARY,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "axes.axisbelow": True,
        "xtick.color": TEXT_SECONDARY,
        "ytick.color": TEXT_SECONDARY,
        "legend.frameon": False,
        "legend.labelcolor": TEXT_PRIMARY,
        "font.family": "sans-serif",
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
    })
