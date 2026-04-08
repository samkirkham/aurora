"""
Smooth static MRI contours in aurora_template.npz.

Applies Gaussian smoothing to palate, pharyngeal_wall, and jaw contours
to round off angular edges from manual editing. Leaves tongue_upper and
tongue_lower untouched (model-generated, already smooth).
"""

import numpy as np
from scipy.ndimage import gaussian_filter1d
from pathlib import Path


DATA_PATH = Path(__file__).parent.parent / "data" / "aurora_template.npz"

# Sigma in units of point-spacing (not mm). sigma=1 smooths over ~3 neighbours.
SMOOTH_PARAMS = {
    "palate": {"sigma": 1.0},
    "pharyngeal_wall": {"sigma": 1.0},
    "jaw": {"sigma": 1.0},
}


def smooth_contour(pts, sigma):
    """Smooth a (N, 2) contour with a 1D Gaussian filter on each axis.

    Pins the first and last points to their original positions.
    """
    x_smooth = gaussian_filter1d(pts[:, 0], sigma=sigma, mode="nearest")
    y_smooth = gaussian_filter1d(pts[:, 1], sigma=sigma, mode="nearest")
    x_smooth[0], y_smooth[0] = pts[0, 0], pts[0, 1]
    x_smooth[-1], y_smooth[-1] = pts[-1, 0], pts[-1, 1]
    return np.column_stack([x_smooth, y_smooth])


def main():
    template = np.load(DATA_PATH, allow_pickle=True)
    contours = template["contours"].item()

    # Preserve all other fields from the npz
    other_fields = {k: template[k] for k in template.files if k != "contours"}

    print("Smoothing contours:")
    for name, params in SMOOTH_PARAMS.items():
        original = contours[name]
        smoothed = smooth_contour(original, sigma=params["sigma"])
        delta = np.linalg.norm(smoothed - original, axis=1)
        print(f"  {name}: {len(original)} pts, max shift = {delta.max():.3f} mm, "
              f"mean shift = {delta.mean():.3f} mm")
        contours[name] = smoothed

    # Save back
    np.savez(DATA_PATH, contours=contours, **other_fields)
    print(f"\nSaved to {DATA_PATH}")


if __name__ == "__main__":
    main()
