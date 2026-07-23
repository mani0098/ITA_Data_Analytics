"""
Clinical definitions for the primary lung cancer cohort.

The cohort is intentionally conservative. It identifies confirmed primary
malignant neoplasms of the bronchus or lung and excludes secondary malignant
neoplasms located in the lung.

Project:
    Early Prediction of Prolonged ICU Stay in Lung Cancer Patients
"""

from __future__ import annotations

# -----------------------------------------------------------------------------
# Primary lung cancer codes
# -----------------------------------------------------------------------------

# ICD-9 category 162:
# Malignant neoplasm of trachea, bronchus and lung.
PRIMARY_LUNG_CANCER_ICD9_PREFIXES: tuple[str, ...] = (
    "162",
)

# ICD-10-CM category C34:
# Malignant neoplasm of bronchus and lung.
PRIMARY_LUNG_CANCER_ICD10_PREFIXES: tuple[str, ...] = (
    "C34",
)

# -----------------------------------------------------------------------------
# Structured diagnosis hierarchy
# -----------------------------------------------------------------------------

PRIMARY_LUNG_CANCER_DIAGNOSIS_PREFIXES: tuple[str, ...] = (
    "oncology|chest tumors|primary lung cancer",
    (
        "pulmonary|disorders of lung parenchyma|"
        "malignancy|primary lung cancer"
    ),
)

# -----------------------------------------------------------------------------
# Definite admission diagnoses
# -----------------------------------------------------------------------------

DEFINITE_LUNG_CANCER_ADMISSION_DIAGNOSES: tuple[str, ...] = (
    "thoracotomy for lung cancer",
)

# -----------------------------------------------------------------------------
# Explicit exclusions
# -----------------------------------------------------------------------------

EXCLUDED_DIAGNOSIS_PHRASES: tuple[str, ...] = (
    "biopsy pending",
    "mesothelioma",
)

# Secondary malignant neoplasm of the lung; not confirmed primary lung cancer.
EXCLUDED_SECONDARY_LUNG_CODES: tuple[str, ...] = (
    "197",
    "C78.0",
)

# -----------------------------------------------------------------------------
# Outcome
# -----------------------------------------------------------------------------

PROLONGED_ICU_LOS_DAYS: float = 5.0
MINIMUM_ADULT_AGE: float = 18.0
MINUTES_PER_DAY: int = 1440