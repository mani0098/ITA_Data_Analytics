"""
Lung cancer cohort construction.

This module identifies confirmed primary lung cancer ICU stays from the eICU
diagnosis, admissionDx and patient tables. It also applies the analytical
inclusion and exclusion criteria and creates the prolonged-LOS outcome.

All column names are normalized to lowercase because the raw eICU CSV files
use lowercase column names.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

import numpy as np
import pandas as pd

from config.lung_cancer import (
    DEFINITE_LUNG_CANCER_ADMISSION_DIAGNOSES,
    EXCLUDED_DIAGNOSIS_PHRASES,
    MINIMUM_ADULT_AGE,
    MINUTES_PER_DAY,
    PRIMARY_LUNG_CANCER_DIAGNOSIS_PREFIXES,
    PRIMARY_LUNG_CANCER_ICD10_PREFIXES,
    PRIMARY_LUNG_CANCER_ICD9_PREFIXES,
    PROLONGED_ICU_LOS_DAYS,
)


def _normalize_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Return a copy with normalized lowercase column names.
    """

    normalized = dataframe.copy()
    normalized.columns = (
        normalized.columns
        .astype(str)
        .str.strip()
        .str.lower()
    )

    return normalized


def _require_columns(
    dataframe: pd.DataFrame,
    required_columns: Iterable[str],
    table_name: str,
) -> None:
    """
    Validate the presence of required columns.

    Raises
    ------
    KeyError
        If at least one required column is absent.
    """

    required = set(required_columns)
    missing = required.difference(dataframe.columns)

    if missing:
        missing_text = ", ".join(sorted(missing))
        raise KeyError(
            f"{table_name} is missing required columns: {missing_text}"
        )


def _normalize_text(series: pd.Series) -> pd.Series:
    """
    Normalize a text Series for case-insensitive matching.
    """

    return (
        series
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )


def _split_icd_codes(value: object) -> list[str]:
    """
    Split an eICU ICD field into individual normalized code tokens.

    eICU may store multiple comma-separated ICD-9 and ICD-10 codes in one
    string, for example: ``162.9, C34.90``.
    """

    if pd.isna(value):
        return []

    return [
        token.strip().upper()
        for token in re.split(r"[,;|]", str(value))
        if token.strip()
    ]


def _is_primary_lung_cancer_code(value: object) -> bool:
    """
    Return True when an ICD field contains a primary lung cancer code.
    """

    codes = _split_icd_codes(value)

    for code in codes:
        if any(
            code == prefix or code.startswith(f"{prefix}.")
            for prefix in PRIMARY_LUNG_CANCER_ICD9_PREFIXES
        ):
            return True

        if any(
            code == prefix or code.startswith(f"{prefix}.")
            for prefix in PRIMARY_LUNG_CANCER_ICD10_PREFIXES
        ):
            return True

    return False


def _matches_primary_diagnosis_text(text: pd.Series) -> pd.Series:
    """
    Match confirmed primary lung cancer diagnosis hierarchies.
    """

    result = pd.Series(False, index=text.index)

    for prefix in PRIMARY_LUNG_CANCER_DIAGNOSIS_PREFIXES:
        result |= text.str.startswith(prefix.lower())

    return result


def _contains_excluded_phrase(text: pd.Series) -> pd.Series:
    """
    Identify explicitly uncertain diagnosis descriptions.
    """

    result = pd.Series(False, index=text.index)

    for phrase in EXCLUDED_DIAGNOSIS_PHRASES:
        result |= text.str.contains(
            phrase.lower(),
            regex=False,
        )

    return result


def build_lung_cancer_evidence(
    diagnosis: pd.DataFrame,
    admission_dx: pd.DataFrame,
    patient: pd.DataFrame,
) -> pd.DataFrame:
    """
    Construct a row-level audit table of lung cancer evidence.

    Parameters
    ----------
    diagnosis
        Raw eICU diagnosis table.

    admission_dx
        Raw eICU admissionDx table.

    patient
        Raw eICU patient table.

    Returns
    -------
    pandas.DataFrame
        One or more evidence rows for every candidate ICU stay.
    """

    diagnosis = _normalize_columns(diagnosis)
    admission_dx = _normalize_columns(admission_dx)
    patient = _normalize_columns(patient)

    _require_columns(
        diagnosis,
        {
            "patientunitstayid",
            "diagnosisstring",
            "icd9code",
        },
        "diagnosis",
    )

    _require_columns(
        admission_dx,
        {"patientunitstayid"},
        "admissionDx",
    )

    _require_columns(
        patient,
        {
            "patientunitstayid",
            "apacheadmissiondx",
        },
        "patient",
    )

    # -------------------------------------------------------------------------
    # Diagnosis evidence
    # -------------------------------------------------------------------------

    diagnosis_text = _normalize_text(
        diagnosis["diagnosisstring"]
    )

    code_match = diagnosis["icd9code"].map(
        _is_primary_lung_cancer_code
    )

    text_match = _matches_primary_diagnosis_text(
        diagnosis_text
    )

    uncertain_match = _contains_excluded_phrase(
        diagnosis_text
    )

    diagnosis_mask = (
        (code_match | text_match)
        & ~uncertain_match
    )

    diagnosis_evidence = diagnosis.loc[
        diagnosis_mask,
        [
            "patientunitstayid",
            "diagnosisstring",
            "icd9code",
        ],
    ].copy()

    diagnosis_evidence["evidence_source"] = "diagnosis"
    diagnosis_evidence["evidence_text"] = (
        diagnosis_evidence["diagnosisstring"]
    )
    diagnosis_evidence["evidence_code"] = (
        diagnosis_evidence["icd9code"]
    )

    matched_code = code_match.loc[
        diagnosis_evidence.index
    ]

    matched_text = text_match.loc[
        diagnosis_evidence.index
    ]

    diagnosis_evidence["evidence_rule"] = np.select(
        [
            matched_code & matched_text,
            matched_code,
            matched_text,
        ],
        [
            "primary_icd_and_text",
            "primary_icd",
            "primary_diagnosis_text",
        ],
        default="unknown",
    )

    diagnosis_evidence = diagnosis_evidence[
        [
            "patientunitstayid",
            "evidence_source",
            "evidence_rule",
            "evidence_text",
            "evidence_code",
        ]
    ]

    # -------------------------------------------------------------------------
    # admissionDx evidence
    # -------------------------------------------------------------------------

    admission_columns = [
        column
        for column in (
            "admitdxtext",
            "admitdxname",
            "admitdxpath",
        )
        if column in admission_dx.columns
    ]

    admission_mask = pd.Series(
        False,
        index=admission_dx.index,
    )

    for column in admission_columns:
        normalized = _normalize_text(
            admission_dx[column]
        )

        for diagnosis_name in (
            DEFINITE_LUNG_CANCER_ADMISSION_DIAGNOSES
        ):
            admission_mask |= normalized.eq(
                diagnosis_name.lower()
            )

    admission_evidence = admission_dx.loc[
        admission_mask
    ].copy()

    if "admitdxtext" in admission_evidence:
        admission_text = admission_evidence[
            "admitdxtext"
        ]
    elif "admitdxname" in admission_evidence:
        admission_text = admission_evidence[
            "admitdxname"
        ]
    else:
        admission_text = admission_evidence[
            "admitdxpath"
        ]

    admission_evidence = pd.DataFrame(
        {
            "patientunitstayid": (
                admission_evidence["patientunitstayid"]
            ),
            "evidence_source": "admission_dx",
            "evidence_rule": (
                "definite_lung_cancer_admission"
            ),
            "evidence_text": admission_text,
            "evidence_code": pd.NA,
        }
    )

    # -------------------------------------------------------------------------
    # Patient APACHE admission diagnosis evidence
    # -------------------------------------------------------------------------

    apache_text = _normalize_text(
        patient["apacheadmissiondx"]
    )

    apache_mask = pd.Series(
        False,
        index=patient.index,
    )

    for diagnosis_name in (
        DEFINITE_LUNG_CANCER_ADMISSION_DIAGNOSES
    ):
        apache_mask |= apache_text.eq(
            diagnosis_name.lower()
        )

    apache_evidence = pd.DataFrame(
        {
            "patientunitstayid": patient.loc[
                apache_mask,
                "patientunitstayid",
            ],
            "evidence_source": (
                "patient_apache_admission"
            ),
            "evidence_rule": (
                "definite_lung_cancer_admission"
            ),
            "evidence_text": patient.loc[
                apache_mask,
                "apacheadmissiondx",
            ],
            "evidence_code": pd.NA,
        }
    )

    # -------------------------------------------------------------------------
    # Combined audit table
    # -------------------------------------------------------------------------

    evidence = pd.concat(
        [
            diagnosis_evidence,
            admission_evidence,
            apache_evidence,
        ],
        ignore_index=True,
    )

    evidence = (
        evidence
        .drop_duplicates()
        .sort_values(
            [
                "patientunitstayid",
                "evidence_source",
                "evidence_rule",
            ]
        )
        .reset_index(drop=True)
    )

    return evidence


def _parse_age(age: pd.Series) -> pd.Series:
    """
    Convert eICU age values to numeric years.

    eICU masks ages above 89 as ``> 89``. These values are represented as
    90 for analysis, while preserving the original age column.
    """

    normalized = (
        age
        .astype("string")
        .str.strip()
        .replace(
            {
                "> 89": "90",
                ">89": "90",
            }
        )
    )

    return pd.to_numeric(
        normalized,
        errors="coerce",
    )


def build_analytic_lung_cancer_cohort(
    patient: pd.DataFrame,
    evidence: pd.DataFrame,
    prolonged_los_days: float = PROLONGED_ICU_LOS_DAYS,
    keep_one_stay_per_patient: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Build the patient-level analytical cohort.

    Inclusion criteria
    ------------------
    - Confirmed primary lung cancer evidence.
    - Age of at least 18 years.
    - Positive, nonmissing ICU discharge offset.
    - One eligible ICU stay per unique patient when requested.

    Returns
    -------
    cohort
        Final analytical cohort.

    flow
        Cohort-selection counts for reporting and visualization.
    """

    patient = _normalize_columns(patient)
    evidence = _normalize_columns(evidence)

    _require_columns(
        patient,
        {
            "patientunitstayid",
            "uniquepid",
            "age",
            "unitdischargeoffset",
            "unitvisitnumber",
        },
        "patient",
    )

    _require_columns(
        evidence,
        {
            "patientunitstayid",
            "evidence_source",
        },
        "evidence",
    )

    candidate_ids = (
        evidence["patientunitstayid"]
        .dropna()
        .drop_duplicates()
    )

    cohort = patient.loc[
        patient["patientunitstayid"].isin(
            candidate_ids
        )
    ].copy()

    flow_records: list[dict[str, object]] = [
        {
            "step": "Confirmed lung cancer candidate ICU stays",
            "n": len(cohort),
        }
    ]

    # Evidence-source flags
    source_flags = pd.crosstab(
        evidence["patientunitstayid"],
        evidence["evidence_source"],
    ).gt(0).astype("int8")

    source_flags.columns = [
        f"source_{column}"
        for column in source_flags.columns
    ]

    cohort = cohort.merge(
        source_flags,
        left_on="patientunitstayid",
        right_index=True,
        how="left",
        validate="one_to_one",
    )

    source_columns = [
        column
        for column in cohort.columns
        if column.startswith("source_")
    ]

    cohort[source_columns] = (
        cohort[source_columns]
        .fillna(0)
        .astype("int8")
    )

    # Derived variables
    cohort["age_years"] = _parse_age(
        cohort["age"]
    )

    cohort["icu_los_days"] = (
        pd.to_numeric(
            cohort["unitdischargeoffset"],
            errors="coerce",
        )
        / MINUTES_PER_DAY
    )

    # Adults
    cohort = cohort.loc[
        cohort["age_years"].ge(
            MINIMUM_ADULT_AGE
        )
    ].copy()

    flow_records.append(
        {
            "step": "Adults aged 18 years or older",
            "n": len(cohort),
        }
    )

    # Valid LOS
    cohort = cohort.loc[
        cohort["icu_los_days"].notna()
        & cohort["icu_los_days"].gt(0)
    ].copy()

    flow_records.append(
        {
            "step": "Positive nonmissing ICU LOS",
            "n": len(cohort),
        }
    )

    # Keep one eligible ICU stay per patient
    if keep_one_stay_per_patient:
        cohort["_unitvisitnumber_numeric"] = (
            pd.to_numeric(
                cohort["unitvisitnumber"],
                errors="coerce",
            )
            .fillna(np.inf)
        )

        cohort = cohort.sort_values(
            [
                "uniquepid",
                "_unitvisitnumber_numeric",
                "patientunitstayid",
            ]
        )

        repeated_patient = (
            cohort["uniquepid"].notna()
            & cohort.duplicated(
                "uniquepid",
                keep="first",
            )
        )

        cohort = cohort.loc[
            ~repeated_patient
        ].copy()

        cohort = cohort.drop(
            columns="_unitvisitnumber_numeric"
        )

    flow_records.append(
        {
            "step": "One eligible ICU stay per patient",
            "n": len(cohort),
        }
    )

    # Primary outcome
    cohort["prolonged_icu_los"] = (
        cohort["icu_los_days"]
        .gt(prolonged_los_days)
        .astype("int8")
    )

    # Sensitivity thresholds
    for threshold in (3, 5, 7):
        cohort[
            f"icu_los_gt_{threshold}d"
        ] = (
            cohort["icu_los_days"]
            .gt(threshold)
            .astype("int8")
        )

    # Mortality variables
    if "unitdischargestatus" in cohort.columns:
        cohort["icu_mortality"] = (
            _normalize_text(
                cohort["unitdischargestatus"]
            )
            .eq("expired")
            .astype("int8")
        )

    if "hospitaldischargestatus" in cohort.columns:
        cohort["hospital_mortality"] = (
            _normalize_text(
                cohort["hospitaldischargestatus"]
            )
            .eq("expired")
            .astype("int8")
        )

    cohort = (
        cohort
        .sort_values("patientunitstayid")
        .reset_index(drop=True)
    )

    flow = pd.DataFrame(flow_records)

    return cohort, flow