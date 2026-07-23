"""Recreate the private final-test prediction file required for ROC/PR plots.

Run this script from the project root after the final calibrated models have
already been fitted and saved. The output contains row-level outcomes and
probabilities, so it must remain local and must not be uploaded.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from config.paths import OUTPUT_DIR, REDUCED_DATA_DIR


TARGET_COLUMN = "prolonged_icu_los"

MODEL_COHORT_FILE = REDUCED_DATA_DIR / "modeling_cohort_v001.csv"
SPLIT_MANIFEST_FILE = OUTPUT_DIR / "splits" / "train_test_split_manifest_v001.csv"
FEATURE_SET_FILE = OUTPUT_DIR / "models" / "model_feature_sets_v001.json"
MODEL_LOCK_FILE = OUTPUT_DIR / "models" / "final_model_lock_v001.json"
PRIMARY_MODEL_FILE = OUTPUT_DIR / "models" / "final_calibrated_logistic_model.joblib"
SECONDARY_MODEL_FILE = OUTPUT_DIR / "models" / "secondary_calibrated_random_forest_model.joblib"
OUTPUT_FILE = OUTPUT_DIR / "splits" / "final_test_predictions_v001.csv"


REQUIRED_FILES = {
    "modeling cohort": MODEL_COHORT_FILE,
    "sealed split manifest": SPLIT_MANIFEST_FILE,
    "feature-set definition": FEATURE_SET_FILE,
    "primary fitted model": PRIMARY_MODEL_FILE,
    "secondary fitted model": SECONDARY_MODEL_FILE,
}

missing_files = [f"{name}: {path}" for name, path in REQUIRED_FILES.items() if not path.exists()]
if missing_files:
    raise FileNotFoundError(
        "The prediction file cannot be recreated because these files are missing:\n"
        + "\n".join(missing_files)
    )


def prepare_feature_frame(
    dataframe: pd.DataFrame,
    feature_columns: list[str],
    categorical_columns: list[str],
) -> pd.DataFrame:
    """Select columns and reproduce the categorical formatting used in training."""
    feature_frame = dataframe.loc[:, feature_columns].copy()

    for column in categorical_columns:
        feature_frame[column] = (
            feature_frame[column]
            .map(lambda value: str(value) if pd.notna(value) else np.nan)
            .astype("object")
        )

    return feature_frame


modeling_cohort = pd.read_csv(MODEL_COHORT_FILE, low_memory=False)
split_manifest = pd.read_csv(SPLIT_MANIFEST_FILE, low_memory=False)

for dataframe in (modeling_cohort, split_manifest):
    dataframe["patientunitstayid"] = pd.to_numeric(
        dataframe["patientunitstayid"], errors="raise"
    ).astype("int64")

if "split" not in split_manifest.columns:
    raise KeyError("The split manifest does not contain a 'split' column.")

with FEATURE_SET_FILE.open("r", encoding="utf-8") as file:
    feature_definition = json.load(file)

model_b_definition = feature_definition["model_b"]
model_b_features = list(model_b_definition["features"])
model_b_numeric = list(model_b_definition["numeric_features"])
model_b_categorical = list(model_b_definition["categorical_features"])

missing_features = sorted(set(model_b_features).difference(modeling_cohort.columns))
if missing_features:
    raise KeyError(
        "The modeling cohort is missing required Model B features:\n"
        + "\n".join(missing_features)
    )

test_ids = (
    split_manifest.loc[
        split_manifest["split"].astype(str).str.lower().eq("test"),
        ["patientunitstayid"],
    ]
    .drop_duplicates()
)

if len(test_ids) != 278:
    raise ValueError(f"Expected 278 test stays, but found {len(test_ids):,}.")

test_data = test_ids.merge(
    modeling_cohort,
    on="patientunitstayid",
    how="left",
    validate="one_to_one",
)

if test_data[TARGET_COLUMN].isna().any():
    raise ValueError("One or more test IDs were not found in the modeling cohort.")

# Reproduce the numeric normalization performed in the modelling notebook.
# The raw eICU age field can contain the anonymized string '> 89'. During
# training it was mapped to 90 before the train/test split. Reading the frozen
# cohort from disk restores the original text value, so we must apply the same
# deterministic conversion before using the saved preprocessing pipeline.
test_data = test_data.replace([np.inf, -np.inf], np.nan)

possible_age_columns = [
    column
    for column in test_data.columns
    if column.lower() in {"age", "patient_age", "age_numeric"}
]

for age_column in possible_age_columns:
    age_text = (
        test_data[age_column]
        .astype("string")
        .str.strip()
        .replace({"> 89": "90", ">89": "90"})
    )
    test_data[age_column] = pd.to_numeric(age_text, errors="coerce")

# Enforce the feature types saved with the modelling definition. This is a
# deterministic format restoration, not model fitting or test-set tuning.
for column in model_b_numeric:
    if column in test_data.columns:
        test_data[column] = pd.to_numeric(test_data[column], errors="coerce")

X_test = prepare_feature_frame(
    dataframe=test_data,
    feature_columns=model_b_features,
    categorical_columns=model_b_categorical,
)
y_test = pd.to_numeric(test_data[TARGET_COLUMN], errors="raise").astype("int8")

primary_model = joblib.load(PRIMARY_MODEL_FILE)
secondary_model = joblib.load(SECONDARY_MODEL_FILE)

primary_probability = primary_model.predict_proba(X_test)[:, 1]
secondary_probability = secondary_model.predict_proba(X_test)[:, 1]

primary_threshold = 0.195239
secondary_threshold = 0.208464

if MODEL_LOCK_FILE.exists():
    with MODEL_LOCK_FILE.open("r", encoding="utf-8") as file:
        model_lock = json.load(file)
    primary_threshold = float(model_lock["primary_model"]["threshold"])
    secondary_threshold = float(model_lock["secondary_model"]["threshold"])

# The plotting script only needs these five columns. No patient identifiers are
# written, which minimizes exposure while preserving the final ROC/PR curves.
final_predictions = pd.DataFrame(
    {
        "observed_outcome": y_test.to_numpy(),
        "primary_probability": primary_probability,
        "primary_prediction": (primary_probability >= primary_threshold).astype("int8"),
        "secondary_probability": secondary_probability,
        "secondary_prediction": (secondary_probability >= secondary_threshold).astype("int8"),
    }
)

assert len(final_predictions) == 278
assert int(final_predictions["observed_outcome"].sum()) == 57
assert np.isfinite(final_predictions[["primary_probability", "secondary_probability"]]).all().all()

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
final_predictions.to_csv(OUTPUT_FILE, index=False)

print("Final test prediction file created successfully.")
print(f"Rows: {len(final_predictions):,}")
print(f"Positive outcomes: {int(final_predictions['observed_outcome'].sum()):,}")
print(f"Saved to: {OUTPUT_FILE}")
print("Keep this row-level file private and local.")
