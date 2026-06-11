"""Random number generation utilities."""

from __future__ import annotations

import numpy as np


def make_rng(seed: int | None = None) -> np.random.Generator:
    """Create a numpy random Generator with optional seed."""
    return np.random.default_rng(seed)
