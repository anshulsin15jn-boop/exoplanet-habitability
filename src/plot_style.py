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
SHADE_DARK = "#e1e0d9"  # slightly darker neutral, for a band nested inside SHADE
RING = TEXT_PRIMARY  # outline that marks highlighted points (candidates)

# Diverging star-temperature colors: red = cooler than the Sun, neutral = Sun-like, blue = hotter
TEFF_COOL = "#d03b3b"
TEFF_NEUTRAL = "#e8e6e0"
TEFF_HOT = "#1c5cab"
SUN_TEFF = 5772.0  # K, IAU 2015 Resolution B3


def teff_colormap():
    """Colormap and norm for stellar temperature, centered on the Sun (2500-7500 K, clipped)."""
    from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

    cmap = LinearSegmentedColormap.from_list("teff", [TEFF_COOL, TEFF_NEUTRAL, TEFF_HOT])
    norm = TwoSlopeNorm(vmin=2500.0, vcenter=SUN_TEFF, vmax=7500.0)
    return cmap, norm


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
