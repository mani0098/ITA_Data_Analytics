# Sprint 13 — Final Project

### 🏥 Early Prediction of Prolonged ICU Stay in Lung Cancer Patients

## 📌 Overview

This capstone project integrates **data engineering, statistical analysis, and machine learning** to investigate whether information collected during the first 24 hours of intensive care can help predict prolonged ICU stays in patients with lung cancer.

Using the **eICU Collaborative Research Database (v2.0)**, the study develops and evaluates predictive models to identify patients at risk of remaining in intensive care for more than five days.

The project demonstrates an end-to-end analytical workflow, from clinical data extraction and preprocessing to predictive modeling, evaluation, and scientific communication.

## 🎯 Learning Objectives

- Integrate **Python, SQL, and machine learning** into a complete analytical workflow.
- Extract, clean, and integrate data from a complex relational healthcare database.
- Perform **exploratory data analysis (EDA)** and clinical feature engineering.
- Develop and evaluate predictive models using appropriate validation strategies.
- Create effective **data visualizations** to communicate analytical findings.
- Apply reproducibility, documentation, and responsible healthcare data management practices.

## 💻 Practical Assignment

The project follows five main stages:

| Stage | Focus | Key Tasks |
|---|---|---|
| 1 | Data Extraction & Cohort Definition | Identify lung cancer patients, define the 24-hour prediction landmark, and establish the prolonged-stay outcome (>5 days). |
| 2 | Data Preparation & Feature Engineering | Integrate laboratory measurements, vital signs, APACHE variables, and medical history; handle missing data and prevent information leakage. |
| 3 | Predictive Modeling | Train and optimize Logistic Regression and Random Forest models using patient-level splitting and cross-validation. |
| 4 | Model Evaluation | Assess discrimination, precision–recall performance, sensitivity, specificity, and probability calibration. |
| 5 | Visualization & Communication | Present the methodology, results, limitations, and clinical implications through a scientific report and presentation. |

## 📊 Key Results

The final modeling cohort included **1,389 ICU stays**, of which **286 (20.6%)** exceeded five days.

The selected model, a **calibrated L1-regularized Logistic Regression**, achieved the following results on an independent held-out test set of 278 ICU stays:

| Evaluation Metric | Result |
|:---|---|
| ROC-AUC | **0.724** |
| Average Precision (PR-AUC) | **0.412** |
| Sensitivity | **63.2%** |
| Specificity | **69.2%** |

These findings demonstrate moderate predictive discrimination using information available within the first 24 hours of ICU admission. Further external validation would be necessary before considering clinical application.

## 🛠️ Technologies & Skills

**Tools:** Python, SQL, MySQL, Jupyter Notebook

**Libraries:** pandas, NumPy, scikit-learn, Matplotlib, Plotly

**Concepts:** Healthcare Analytics · Data Engineering · Exploratory Data Analysis · Feature Engineering · Machine Learning · Classification · Cross-Validation · Model Evaluation · Data Visualization · Scientific Reporting

## 📂 Project Files

- [Final Presentation](Presentation.pdf) — Visual presentation of the research question, methodology, predictive modeling, results, and conclusions.
- [Four-Page Scientific Report](Four-Page%20Paper-Style%20Report.pdf) — Scientific documentation covering the study design, methodology, results, discussion, limitations, and references.

**Data availability:** The study uses the access-controlled eICU Collaborative Research Database. Patient-level data are not included in this repository due to data-use and privacy restrictions.
