"""
Datum definition for free network adjustment.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DatumType(Enum):
    """Types of datum definition."""
    FIXED_POINTS = "fixed_points"          # Classical: some points fixed
    MINIMUM_CONSTRAINTS = "min_constraints" # Free network with minimum constraints
    INNER_CONSTRAINTS = "inner_constraints" # Free network with inner constraints


@dataclass
class DatumDefinition:
    """
    Defines the datum (reference frame) for the adjustment.
    
    For a free network adjustment, the datum defect must be handled either by:
    - Fixing some coordinates (classical approach)
    - Applying minimum constraints
    - Using inner constraints (Helmert transformation)
    """
    
    datum_type: DatumType = DatumType.FIXED_POINTS
    
    # For minimum constraints: which parameters to constrain
    constrain_translations: bool = True  # Fix center of gravity
    constrain_rotation: bool = True      # Fix orientation
    constrain_scale: bool = False        # Usually not constrained in local networks
