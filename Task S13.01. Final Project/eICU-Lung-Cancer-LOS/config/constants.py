"""
Project-wide immutable constants.

This module contains constants that should never change during the execution
of the project.

Author:
    Mani Rezaeirad

Project:
    Early Prediction of Prolonged ICU Stay in Lung Cancer Patients
"""

from __future__ import annotations

# =============================================================================
# PROJECT
# =============================================================================

PROJECT_NAME: str = "eICU_LungCancer_LOS"

PROJECT_VERSION: str = "0.1.0"

AUTHOR: str = "Mani Rezaeirad"

DESCRIPTION: str = (
    "Early Prediction of Prolonged ICU Length of Stay in Lung Cancer Patients"
)

# =============================================================================
# DATABASE
# =============================================================================

PATIENT_STAY_ID = "patientUnitStayID"

PATIENT_ID = "uniquepid"

# =============================================================================
# RANDOMNESS
# =============================================================================

DEFAULT_RANDOM_STATE: int = 42

# =============================================================================
# PERFORMANCE
# =============================================================================

DEFAULT_CHUNK_SIZE: int = 100_000

# =============================================================================
# DATE FORMATS
# =============================================================================

DATE_FORMAT: str = "%Y-%m-%d"

DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

# =============================================================================
# TIME
# =============================================================================

MINUTES_PER_DAY: int = 1440
HOURS_PER_DAY: int = 24