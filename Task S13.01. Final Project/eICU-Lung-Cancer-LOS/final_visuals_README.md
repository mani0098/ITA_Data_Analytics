# Final visual storytelling package

Run all commands from the project root (the folder that contains `config`, `outputs`, and `notebooks`).

## 1. Install once

```bat
python -m pip install -r final_visuals_requirements.txt
```

## 2. Recreate the private final-test prediction file

Figure 10 needs final test-set outcomes and probabilities. The aggregate metric files are not enough to reconstruct ROC and precision–recall curves.

```bat
python create_final_test_predictions.py
```

Expected output:

```text
outputs\splits\final_test_predictions_v001.csv
```

This row-level file has no patient identifier in the revised version, but it still contains individual outcomes and probabilities. Keep it private and local.

The script expects these existing project files:

```text
outputs\models\final_calibrated_logistic_model.joblib
outputs\models\secondary_calibrated_random_forest_model.joblib
outputs\models\model_feature_sets_v001.json
outputs\splits\train_test_split_manifest_v001.csv
data\reduced\modeling_cohort_v001.csv
```

The exact data path is resolved through `config.paths.REDUCED_DATA_DIR`.

## 3. Generate all figures

```bat
python final_visuals.py
```

The revised scorecard uses six spacious KPI cards in a 2 × 3 layout, avoiding the overlap created by the previous five bullet gauges.

Expected figure folder:

```text
outputs\figures\final_storytelling\
```

Figure 10 is created only when this file exists:

```text
outputs\splits\final_test_predictions_v001.csv
```

## 4. Open the Streamlit dashboard

```bat
python -m streamlit run streamlit_app.py
```

## 5. Static image export

HTML files are always produced. PNG and SVG export requires Kaleido and Chrome/Chromium.

```bat
python -m pip install --upgrade kaleido
plotly_get_chrome
```

Then rerun:

```bat
python final_visuals.py
```

## Important privacy rule

Do not upload the modeling cohort, split manifest, final test prediction file, or any other row-level eICU file. Only aggregate tables and final figures should leave the private local project folder.
