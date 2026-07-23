"""
Frequently used database column names.

Keeping column names centralized prevents spelling mistakes and makes
future refactoring considerably easier.
"""

from __future__ import annotations

# =============================================================================
# IDENTIFIERS
# =============================================================================

PATIENT_ID = "patientUnitStayID"

UNIQUE_PID = "uniquepid"

HOSPITAL_ID = "hospitalid"

# =============================================================================
# DEMOGRAPHICS
# =============================================================================

AGE = "age"

GENDER = "gender"

ETHNICITY = "ethnicity"

ADMISSION_HEIGHT = "admissionheight"

ADMISSION_WEIGHT = "admissionweight"

# =============================================================================
# OUTCOMES
# =============================================================================

UNIT_DISCHARGE_OFFSET = "unitDischargeOffset"

HOSPITAL_DISCHARGE_OFFSET = "hospitalDischargeOffset"

HOSPITAL_LOS = "hospitalDischargeOffset"

UNIT_DISCHARGE_STATUS = "unitDischargeStatus"

HOSPITAL_DISCHARGE_STATUS = "hospitalDischargeStatus"

MORTALITY = "hospitalDischargeStatus"

# =============================================================================
# APACHE
# =============================================================================

APACHE_IV = "apacheIVa"

APACHE_IV_PROB = "predictedHospitalMortality"

# =============================================================================
# ADMISSION
# =============================================================================

ADMISSION_SOURCE = "admissionSource"

ADMISSION_TYPE = "admissionType"