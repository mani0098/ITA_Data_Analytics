SELECT COUNT(*) AS imported_rows
FROM apachepatientresult_selected;
-----------------------------------------------------------
SELECT
    apacheversion,
    COUNT(*) AS number_of_rows,
    COUNT(DISTINCT patientunitstayid) AS unique_icu_stays
FROM apachepatientresult_selected
GROUP BY apacheversion
ORDER BY apacheversion;
-----------------------------------------------------------
SELECT
    COUNT(DISTINCT patientunitstayid) AS unique_icu_stays,
    COUNT(*) AS total_rows
FROM apachepatientresult_selected;
-----------------------------------------------------------
SELECT
    SUM(patientunitstayid IS NULL) AS missing_patientunitstayid,
    SUM(apacheversion IS NULL) AS missing_apacheversion,
    SUM(acutephysiologyscore IS NULL) AS missing_aps,
    SUM(apachescore IS NULL) AS missing_apache_score,
    SUM(predictedicumortality IS NULL) AS missing_predicted_icu_mortality,
    SUM(predictedhospitalmortality IS NULL)
        AS missing_predicted_hospital_mortality,
    SUM(predictediculos IS NULL) AS missing_predicted_icu_los
FROM apachepatientresult_selected;
-----------------------------------------------------------
SELECT *
FROM apachepatientresult_selected
LIMIT 10;
-----------------------------------------------------------
SELECT
    apacheversion,
    COUNT(*) AS total_rows,

    SUM(acutephysiologyscore < 0) AS negative_aps,
    SUM(apachescore < 0) AS negative_apache_score,
    SUM(predictediculos < 0) AS negative_predicted_icu_los,

    SUM(
        TRIM(predictedicumortality) = '-1'
    ) AS sentinel_predicted_icu_mortality,

    SUM(
        TRIM(predictedhospitalmortality) = '-1'
    ) AS sentinel_predicted_hospital_mortality,

    SUM(
        TRIM(predictedicumortality)
        NOT REGEXP '^[0-9]+(\\.[0-9]+)?$'
    ) AS nonnumeric_predicted_icu_mortality,

    SUM(
        TRIM(predictedhospitalmortality)
        NOT REGEXP '^[0-9]+(\\.[0-9]+)?$'
    ) AS nonnumeric_predicted_hospital_mortality

FROM apachepatientresult_selected
GROUP BY apacheversion
ORDER BY apacheversion;
-----------------------------------------------------------
SELECT DISTINCT apacheversion
FROM apachepatientresult_selected
ORDER BY apacheversion;
-----------------------------------------------------------
SELECT
    COUNT(*) AS matched_icu_stays,

    SUM(
        NOT (
            iv.acutephysiologyscore
            <=>
            iva.acutephysiologyscore
        )
    ) AS different_aps,

    SUM(
        NOT (
            iv.apachescore
            <=>
            iva.apachescore
        )
    ) AS different_apache_scores,

    SUM(
        NOT (
            iv.predictedicumortality
            <=>
            iva.predictedicumortality
        )
    ) AS different_predicted_icu_mortality,

    SUM(
        NOT (
            iv.predictedhospitalmortality
            <=>
            iva.predictedhospitalmortality
        )
    ) AS different_predicted_hospital_mortality,

    SUM(
        NOT (
            iv.predictediculos
            <=>
            iva.predictediculos
        )
    ) AS different_predicted_icu_los

FROM apachepatientresult_selected AS iv

INNER JOIN apachepatientresult_selected AS iva
    ON iv.patientunitstayid = iva.patientunitstayid

WHERE iv.apacheversion = 'IV'
  AND iva.apacheversion = 'IVa';
-----------------------------------------------------------
CREATE OR REPLACE VIEW apachepatientresult_iva AS

SELECT
    patientunitstayid,
    acutephysiologyscore,
    apachescore,

    CASE
        WHEN TRIM(predictedicumortality) = '-1'
            THEN NULL
        ELSE CAST(
            predictedicumortality AS DECIMAL(12, 10)
        )
    END AS predictedicumortality,

    CASE
        WHEN TRIM(predictedhospitalmortality) = '-1'
            THEN NULL
        ELSE CAST(
            predictedhospitalmortality AS DECIMAL(12, 10)
        )
    END AS predictedhospitalmortality,

    CASE
        WHEN predictediculos < 0
            THEN NULL
        ELSE predictediculos
    END AS predictediculos

FROM apachepatientresult_selected

WHERE apacheversion = 'IVa';
-----------------------------------------------------------
SELECT
    COUNT(*) AS rows_in_iva_view,
    COUNT(DISTINCT patientunitstayid) AS unique_icu_stays,

    SUM(acutephysiologyscore IS NULL) AS missing_aps,
    SUM(apachescore IS NULL) AS missing_apache_score,
    SUM(predictedicumortality IS NULL)
        AS missing_predicted_icu_mortality,
    SUM(predictedhospitalmortality IS NULL)
        AS missing_predicted_hospital_mortality,
    SUM(predictediculos IS NULL)
        AS missing_predicted_icu_los

FROM apachepatientresult_iva;
-----------------------------------------------------------
SELECT
    COUNT(*) AS cohort_rows,
    COUNT(DISTINCT patientunitstayid) AS unique_icu_stays
FROM lung_cancer_cohort_ids;
-----------------------------------------------------------
SELECT
    COUNT(*) AS total_lung_cancer_stays,

    COUNT(apr.patientunitstayid) AS stays_with_apache_iva,

    COUNT(*) - COUNT(apr.patientunitstayid)
        AS stays_without_apache_iva,

    ROUND(
        100.0
        * COUNT(apr.patientunitstayid)
        / COUNT(*),
        2
    ) AS apache_iva_coverage_percent

FROM lung_cancer_cohort_ids AS cohort

LEFT JOIN apachepatientresult_iva AS apr
    ON cohort.patientunitstayid =
       apr.patientunitstayid;
-----------------------------------------------------------
SELECT
    COUNT(*) AS rows_in_filtered_table,
    COUNT(DISTINCT patientunitstayid)
        AS unique_icu_stays
FROM apachepatientresult_iva_lung_cancer;
-----------------------------------------------------------
SELECT
    COUNT(*) AS total_rows,

    SUM(acutephysiologyscore IS NULL)
        AS missing_acutephysiologyscore,

    SUM(apachescore IS NULL)
        AS missing_apachescore,

    SUM(predictedicumortality IS NULL)
        AS missing_predictedicumortality,

    SUM(predictedhospitalmortality IS NULL)
        AS missing_predictedhospitalmortality,

    SUM(predictediculos IS NULL)
        AS missing_predictediculos

FROM apachepatientresult_iva_lung_cancer;
-----------------------------------------------------------
SELECT
    MIN(acutephysiologyscore) AS min_aps,
    MAX(acutephysiologyscore) AS max_aps,
    AVG(acutephysiologyscore) AS mean_aps,

    MIN(apachescore) AS min_apache,
    MAX(apachescore) AS max_apache,
    AVG(apachescore) AS mean_apache,

    MIN(predictediculos) AS min_predicted_icu_los,
    MAX(predictediculos) AS max_predicted_icu_los,
    AVG(predictediculos) AS mean_predicted_icu_los

FROM apachepatientresult_iva_lung_cancer;
-----------------------------------------------------------
SELECT
    COUNT(*) AS rows_imported,
    COUNT(DISTINCT patientunitstayid) AS unique_icu_stays
FROM lung_cancer_patient_outcomes;
-----------------------------------------------------------
SELECT
    CASE
        WHEN apr.patientunitstayid IS NULL
            THEN 'without_apache_iva'
        ELSE 'with_apache_iva'
    END AS apache_iva_group,

    COUNT(*) AS number_of_stays,

    SUM(
        CASE
            WHEN p.unitdischargeoffset > 5 * 1440
                THEN 1
            ELSE 0
        END
    ) AS prolonged_icu_los_n,

    ROUND(
        100.0 * AVG(
            CASE
                WHEN p.unitdischargeoffset > 5 * 1440
                    THEN 1
                ELSE 0
            END
        ),
        2
    ) AS prolonged_icu_los_percent,

    ROUND(
        AVG(p.unitdischargeoffset) / 1440,
        2
    ) AS mean_icu_los_days,

    ROUND(
        100.0 * AVG(
            CASE
                WHEN LOWER(TRIM(p.unitdischargestatus)) = 'expired'
                    THEN 1
                WHEN p.unitdischargestatus IS NULL
                    OR TRIM(p.unitdischargestatus) = ''
                    THEN NULL
                ELSE 0
            END
        ),
        2
    ) AS icu_mortality_percent,

    ROUND(
        100.0 * AVG(
            CASE
                WHEN LOWER(TRIM(p.hospitaldischargestatus)) = 'expired'
                    THEN 1
                WHEN p.hospitaldischargestatus IS NULL
                    OR TRIM(p.hospitaldischargestatus) = ''
                    THEN NULL
                ELSE 0
            END
        ),
        2
    ) AS hospital_mortality_percent

FROM lung_cancer_cohort_ids AS cohort

INNER JOIN lung_cancer_patient_outcomes AS p
    ON cohort.patientunitstayid =
       p.patientunitstayid

LEFT JOIN apachepatientresult_iva AS apr
    ON cohort.patientunitstayid =
       apr.patientunitstayid

GROUP BY
    CASE
        WHEN apr.patientunitstayid IS NULL
            THEN 'without_apache_iva'
        ELSE 'with_apache_iva'
    END

ORDER BY apache_iva_group;
-----------------------------------------------------------
SELECT COUNT(*)
FROM lung_cancer_patient_outcomes;
-----------------------------------------------------------
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT patientunitstayid) AS unique_icu_stays,

    MIN(unitdischargeoffset) AS minimum_icu_offset,
    MAX(unitdischargeoffset) AS maximum_icu_offset,

    ROUND(
        AVG(unitdischargeoffset),
        2
    ) AS mean_icu_offset_minutes,

    ROUND(
        AVG(unitdischargeoffset) / 1440,
        2
    ) AS mean_icu_los_days

FROM lung_cancer_patient_outcomes;
-----------------------------------------------------------
SELECT
    unitdischargestatus,
    COUNT(*) AS number_of_stays
FROM lung_cancer_patient_outcomes
GROUP BY unitdischargestatus
ORDER BY number_of_stays DESC;
-----------------------------------------------------------
SELECT
    hospitaldischargestatus,
    COUNT(*) AS number_of_stays
FROM lung_cancer_patient_outcomes
GROUP BY hospitaldischargestatus
ORDER BY number_of_stays DESC;
-----------------------------------------------------------
SELECT
    COUNT(*) AS imported_rows,

    COUNT(DISTINCT patientunitstayid)
        AS unique_icu_stays,

    COUNT(*) -
    COUNT(DISTINCT patientunitstayid)
        AS duplicate_rows

FROM apachepredvar_selected_raw;
-----------------------------------------------------------
SELECT
    patientunitstayid,
    COUNT(*) AS row_count
FROM apachepredvar_selected_raw
GROUP BY patientunitstayid
HAVING COUNT(*) > 1
ORDER BY row_count DESC
LIMIT 20;
-----------------------------------------------------------
SELECT
    MIN(admitsource) AS min_admitsource,
    MAX(admitsource) AS max_admitsource,

    MIN(meds) AS min_meds,
    MAX(meds) AS max_meds,

    MIN(verbal) AS min_verbal,
    MAX(verbal) AS max_verbal,

    MIN(motor) AS min_motor,
    MAX(motor) AS max_motor,

    MIN(eyes) AS min_eyes,
    MAX(eyes) AS max_eyes,

    MIN(ventday1) AS min_ventday1,
    MAX(ventday1) AS max_ventday1,

    MIN(oobventday1) AS min_oobventday1,
    MAX(oobventday1) AS max_oobventday1,

    MIN(oobintubday1) AS min_oobintubday1,
    MAX(oobintubday1) AS max_oobintubday1

FROM apachepredvar_selected_raw;
-----------------------------------------------------------
SELECT
    COUNT(*) AS total_rows,

    SUM(admitsource NOT BETWEEN 1 AND 8)
        AS invalid_admitsource,

    SUM(meds NOT IN (-1, 0, 1))
        AS invalid_meds,

    SUM(verbal NOT BETWEEN 1 AND 5)
        AS invalid_verbal,

    SUM(motor NOT BETWEEN 1 AND 6)
        AS invalid_motor,

    SUM(eyes NOT BETWEEN 1 AND 4)
        AS invalid_eyes,

    SUM(aids NOT IN (0, 1))
        AS invalid_aids,

    SUM(hepaticfailure NOT IN (0, 1))
        AS invalid_hepaticfailure,

    SUM(lymphoma NOT IN (0, 1))
        AS invalid_lymphoma,

    SUM(metastaticcancer NOT IN (0, 1))
        AS invalid_metastaticcancer,

    SUM(leukemia NOT IN (0, 1))
        AS invalid_leukemia,

    SUM(immunosuppression NOT IN (0, 1))
        AS invalid_immunosuppression,

    SUM(cirrhosis NOT IN (0, 1))
        AS invalid_cirrhosis,

    SUM(diabetes NOT IN (0, 1))
        AS invalid_diabetes,

    SUM(electivesurgery NOT IN (0, 1))
        AS invalid_electivesurgery,

    SUM(activetx NOT IN (0, 1))
        AS invalid_activetx,

    SUM(readmit NOT IN (0, 1))
        AS invalid_readmit,

    SUM(ventday1 NOT IN (0, 1))
        AS invalid_ventday1,

    SUM(oobventday1 NOT IN (0, 1))
        AS invalid_oobventday1,

    SUM(oobintubday1 NOT IN (0, 1))
        AS invalid_oobintubday1,

    SUM(pao2 < 0)
        AS negative_pao2,

    SUM(fio2 < 0)
        AS negative_fio2,

    SUM(creatinine < 0)
        AS negative_creatinine

FROM apachepredvar_selected_raw;
-----------------------------------------------------------
SELECT
    admitsource,
    COUNT(*) AS number_of_stays

FROM apachepredvar_selected_raw

GROUP BY admitsource

ORDER BY admitsource;
-----------------------------------------------------------
SELECT
    admitdiagnosis,
    COUNT(*) AS number_of_stays

FROM apachepredvar_selected_raw

GROUP BY admitdiagnosis

ORDER BY number_of_stays DESC

LIMIT 20;
-----------------------------------------------------------
CREATE OR REPLACE VIEW apachepredvar_clean AS

SELECT
    patientunitstayid,

    CASE
        WHEN admitsource BETWEEN 1 AND 8
            THEN admitsource
        ELSE NULL
    END AS admitsource,

    NULLIF(
        NULLIF(TRIM(admitdiagnosis), ''),
        '-1'
    ) AS admitdiagnosis,

    CASE
        WHEN meds IN (0, 1)
            THEN meds
        ELSE NULL
    END AS meds,

    CASE
        WHEN verbal BETWEEN 1 AND 5
            THEN verbal
        ELSE NULL
    END AS verbal,

    CASE
        WHEN motor BETWEEN 1 AND 6
            THEN motor
        ELSE NULL
    END AS motor,

    CASE
        WHEN eyes BETWEEN 1 AND 4
            THEN eyes
        ELSE NULL
    END AS eyes,

    CASE
        WHEN meds = 0
         AND verbal BETWEEN 1 AND 5
         AND motor BETWEEN 1 AND 6
         AND eyes BETWEEN 1 AND 4
            THEN verbal + motor + eyes
        ELSE NULL
    END AS gcs_total,

    CASE WHEN aids IN (0, 1)
        THEN aids ELSE NULL END AS aids,

    CASE WHEN hepaticfailure IN (0, 1)
        THEN hepaticfailure ELSE NULL END
        AS hepaticfailure,

    CASE WHEN lymphoma IN (0, 1)
        THEN lymphoma ELSE NULL END
        AS lymphoma,

    CASE WHEN metastaticcancer IN (0, 1)
        THEN metastaticcancer ELSE NULL END
        AS metastaticcancer,

    CASE WHEN leukemia IN (0, 1)
        THEN leukemia ELSE NULL END
        AS leukemia,

    CASE WHEN immunosuppression IN (0, 1)
        THEN immunosuppression ELSE NULL END
        AS immunosuppression,

    CASE WHEN cirrhosis IN (0, 1)
        THEN cirrhosis ELSE NULL END
        AS cirrhosis,

    CASE WHEN diabetes IN (0, 1)
        THEN diabetes ELSE NULL END
        AS diabetes,

    CASE WHEN midur IN (0, 1)
        THEN midur ELSE NULL END
        AS myocardial_infarction_6m,

    CASE WHEN electivesurgery IN (0, 1)
        THEN electivesurgery ELSE NULL END
        AS elective_surgery,

    CASE WHEN activetx IN (0, 1)
        THEN activetx ELSE NULL END
        AS active_treatment,

    CASE WHEN readmit IN (0, 1)
        THEN readmit ELSE NULL END
        AS readmission,

    CASE WHEN ventday1 IN (0, 1)
        THEN ventday1 ELSE NULL END
        AS vent_worst_rr_day1,

    CASE WHEN oobventday1 IN (0, 1)
        THEN oobventday1 ELSE NULL END
        AS ventilated_day1,

    CASE WHEN oobintubday1 IN (0, 1)
        THEN oobintubday1 ELSE NULL END
        AS intubated_day1,

    CASE
        WHEN oobventday1 = 1
         AND oobintubday1 = 0
            THEN 1
        WHEN oobventday1 IN (0, 1)
         AND oobintubday1 IN (0, 1)
            THEN 0
        ELSE NULL
    END AS noninvasive_ventilation_day1,

    CASE
        WHEN pao2 > 0
            THEN pao2
        ELSE NULL
    END AS pao2,

    CASE
        WHEN fio2 >= 0
            THEN fio2
        ELSE NULL
    END AS fio2,

    CASE
        WHEN creatinine >= 0
            THEN creatinine
        ELSE NULL
    END AS creatinine,

    CASE
        WHEN day1meds IN (0, 1)
            THEN day1meds
        ELSE NULL
    END AS day1meds,

    CASE
        WHEN day1verbal BETWEEN 1 AND 5
            THEN day1verbal
        ELSE NULL
    END AS day1verbal,

    CASE
        WHEN day1motor BETWEEN 1 AND 6
            THEN day1motor
        ELSE NULL
    END AS day1motor,

    CASE
        WHEN day1eyes BETWEEN 1 AND 4
            THEN day1eyes
        ELSE NULL
    END AS day1eyes,

    CASE
        WHEN day1meds = 0
         AND day1verbal BETWEEN 1 AND 5
         AND day1motor BETWEEN 1 AND 6
         AND day1eyes BETWEEN 1 AND 4
            THEN day1verbal
               + day1motor
               + day1eyes
        ELSE NULL
    END AS day1_gcs_total,

    CASE
        WHEN day1pao2 > 0
            THEN day1pao2
        ELSE NULL
    END AS day1pao2,

    CASE
        WHEN day1fio2 >= 0
            THEN day1fio2
        ELSE NULL
    END AS day1fio2

FROM apachepredvar_selected_raw;
-----------------------------------------------------------
SELECT
    COUNT(*) AS total_lung_cancer_stays,

    COUNT(apv.patientunitstayid)
        AS stays_with_apache_pred_var,

    COUNT(*) -
    COUNT(apv.patientunitstayid)
        AS stays_without_apache_pred_var,

    ROUND(
        100.0
        * COUNT(apv.patientunitstayid)
        / COUNT(*),
        2
    ) AS coverage_percent

FROM lung_cancer_cohort_ids AS cohort

LEFT JOIN apachepredvar_lung_cancer AS apv
    ON cohort.patientunitstayid =
       apv.patientunitstayid;
-----------------------------------------------------------
SELECT
    COUNT(*) AS total_rows,

    SUM(admitsource IS NULL)
        AS missing_admitsource,

    SUM(admitdiagnosis IS NULL)
        AS missing_admitdiagnosis,

    SUM(gcs_total IS NULL)
        AS missing_gcs_total,

    SUM(aids IS NULL)
        AS missing_aids,

    SUM(hepaticfailure IS NULL)
        AS missing_hepaticfailure,

    SUM(lymphoma IS NULL)
        AS missing_lymphoma,

    SUM(metastaticcancer IS NULL)
        AS missing_metastaticcancer,

    SUM(leukemia IS NULL)
        AS missing_leukemia,

    SUM(immunosuppression IS NULL)
        AS missing_immunosuppression,

    SUM(cirrhosis IS NULL)
        AS missing_cirrhosis,

    SUM(diabetes IS NULL)
        AS missing_diabetes,

    SUM(elective_surgery IS NULL)
        AS missing_elective_surgery,

    SUM(active_treatment IS NULL)
        AS missing_active_treatment,

    SUM(readmission IS NULL)
        AS missing_readmission,

    SUM(ventilated_day1 IS NULL)
        AS missing_ventilated_day1,

    SUM(intubated_day1 IS NULL)
        AS missing_intubated_day1,

    SUM(pao2 IS NULL)
        AS missing_pao2,

    SUM(fio2 IS NULL)
        AS missing_fio2,

    SUM(creatinine IS NULL)
        AS missing_creatinine,

    SUM(day1_gcs_total IS NULL)
        AS missing_day1_gcs_total,

    SUM(day1pao2 IS NULL)
        AS missing_day1pao2,

    SUM(day1fio2 IS NULL)
        AS missing_day1fio2

FROM apachepredvar_lung_cancer;
-----------------------------------------------------------
SELECT
    COUNT(*) AS total_rows,

    SUM(
        gcs_total IS NOT NULL
        AND day1_gcs_total IS NOT NULL
    ) AS both_gcs_available,

    SUM(
        gcs_total IS NOT NULL
        AND day1_gcs_total IS NOT NULL
        AND gcs_total = day1_gcs_total
    ) AS identical_gcs,

    SUM(
        gcs_total IS NOT NULL
        AND day1_gcs_total IS NOT NULL
        AND gcs_total <> day1_gcs_total
    ) AS different_gcs

FROM apachepredvar_lung_cancer;
-----------------------------------------------------------
SELECT
    MIN(pao2) AS min_pao2,
    MAX(pao2) AS max_pao2,

    MIN(fio2) AS min_fio2,
    MAX(fio2) AS max_fio2,

    MIN(day1pao2) AS min_day1pao2,
    MAX(day1pao2) AS max_day1pao2,

    MIN(day1fio2) AS min_day1fio2,
    MAX(day1fio2) AS max_day1fio2,

    MIN(creatinine) AS min_creatinine,
    MAX(creatinine) AS max_creatinine

FROM apachepredvar_lung_cancer;
-----------------------------------------------------------
SELECT
    COUNT(*) AS total_rows,

    SUM(
        NOT (pao2 <=> day1pao2)
    ) AS different_pao2_including_nulls,

    SUM(
        NOT (fio2 <=> day1fio2)
    ) AS different_fio2_including_nulls

FROM apachepredvar_lung_cancer;
-----------------------------------------------------------
CREATE OR REPLACE VIEW apachepredvar_model_features AS

SELECT
    patientunitstayid,

    -- Categorical admission variables
    admitsource,
    admitdiagnosis,

    -- Neurologic status
    meds AS gcs_unscorable_due_to_medication,
    verbal AS gcs_verbal,
    motor AS gcs_motor,
    eyes AS gcs_eyes,
    gcs_total,

    -- Chronic conditions
    aids,
    hepaticfailure,
    lymphoma,
    metastaticcancer,
    leukemia,
    immunosuppression,
    cirrhosis,
    diabetes,
    myocardial_infarction_6m,

    -- Admission and treatment characteristics
    elective_surgery,

    CASE
        WHEN elective_surgery IS NULL THEN 1
        ELSE 0
    END AS elective_surgery_missing,

    active_treatment,
    readmission,

    -- Respiratory support
    vent_worst_rr_day1,
    ventilated_day1,
    intubated_day1,
    noninvasive_ventilation_day1,

    -- APACHE-day oxygenation
    pao2,

    CASE
        WHEN fio2 BETWEEN 21 AND 100
            THEN fio2 / 100.0

        WHEN fio2 BETWEEN 0.21 AND 1.00
            THEN fio2

        ELSE NULL
    END AS fio2_fraction,

    CASE
        WHEN pao2 > 0
         AND fio2 BETWEEN 21 AND 100
            THEN pao2 / (fio2 / 100.0)

        WHEN pao2 > 0
         AND fio2 BETWEEN 0.21 AND 1.00
            THEN pao2 / fio2

        ELSE NULL
    END AS pao2_fio2_ratio,

    creatinine

FROM apachepredvar_lung_cancer;
-----------------------------------------------------------
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT patientunitstayid) AS unique_icu_stays,

    SUM(gcs_total IS NULL) AS missing_gcs_total,
    SUM(elective_surgery IS NULL) AS missing_elective_surgery,
    SUM(pao2_fio2_ratio IS NULL) AS missing_pao2_fio2_ratio,
    SUM(creatinine IS NULL) AS missing_creatinine,

    MIN(fio2_fraction) AS minimum_fio2_fraction,
    MAX(fio2_fraction) AS maximum_fio2_fraction,

    MIN(pao2_fio2_ratio) AS minimum_pao2_fio2_ratio,
    MAX(pao2_fio2_ratio) AS maximum_pao2_fio2_ratio

FROM apachepredvar_model_features;
-----------------------------------------------------------
SELECT
    COUNT(*) AS imported_rows,

    COUNT(DISTINCT patientunitstayid)
        AS unique_icu_stays,

    COUNT(*) -
    COUNT(DISTINCT patientunitstayid)
        AS duplicate_rows

FROM apacheapsvar_selected_raw;
-----------------------------------------------------------
SELECT
    patientunitstayid,
    COUNT(*) AS row_count

FROM apacheapsvar_selected_raw

GROUP BY patientunitstayid

HAVING COUNT(*) > 1

ORDER BY row_count DESC

LIMIT 20;
-----------------------------------------------------------
SELECT
    COUNT(*) AS total_rows,

    SUM(intubated NOT IN (0, 1))
        AS invalid_intubated,

    SUM(vent NOT IN (0, 1))
        AS invalid_vent,

    SUM(dialysis NOT IN (0, 1))
        AS invalid_dialysis,

    SUM(meds NOT IN (-1, 0, 1))
        AS invalid_meds,

    SUM(eyes NOT BETWEEN 1 AND 4)
        AS unavailable_or_invalid_eyes,

    SUM(motor NOT BETWEEN 1 AND 6)
        AS unavailable_or_invalid_motor,

    SUM(verbal NOT BETWEEN 1 AND 5)
        AS unavailable_or_invalid_verbal,

    SUM(urine = -1)
        AS sentinel_urine,

    SUM(wbc = -1)
        AS sentinel_wbc,

    SUM(temperature = -1)
        AS sentinel_temperature,

    SUM(respiratoryrate = -1)
        AS sentinel_respiratoryrate,

    SUM(sodium = -1)
        AS sentinel_sodium,

    SUM(heartrate = -1)
        AS sentinel_heartrate,

    SUM(meanbp = -1)
        AS sentinel_meanbp,

    SUM(ph = -1)
        AS sentinel_ph,

    SUM(hematocrit = -1)
        AS sentinel_hematocrit,

    SUM(creatinine = -1)
        AS sentinel_creatinine,

    SUM(albumin = -1)
        AS sentinel_albumin,

    SUM(pao2 = -1)
        AS sentinel_pao2,

    SUM(pco2 = -1)
        AS sentinel_pco2,

    SUM(bun = -1)
        AS sentinel_bun,

    SUM(glucose = -1)
        AS sentinel_glucose,

    SUM(bilirubin = -1)
        AS sentinel_bilirubin,

    SUM(fio2 = -1)
        AS sentinel_fio2

FROM apacheapsvar_selected_raw;
-----------------------------------------------------------
CREATE OR REPLACE VIEW apacheapsvar_clean AS

SELECT
    patientunitstayid,

    CASE
        WHEN intubated IN (0, 1)
            THEN intubated
        ELSE NULL
    END AS intubated,

    CASE
        WHEN vent IN (0, 1)
            THEN vent
        ELSE NULL
    END AS ventilated,

    CASE
        WHEN dialysis IN (0, 1)
            THEN dialysis
        ELSE NULL
    END AS dialysis,

    CASE
        WHEN meds IN (0, 1)
            THEN meds
        ELSE NULL
    END AS gcs_unscorable_due_to_medication,

    CASE
        WHEN eyes BETWEEN 1 AND 4
            THEN eyes
        ELSE NULL
    END AS gcs_eyes,

    CASE
        WHEN motor BETWEEN 1 AND 6
            THEN motor
        ELSE NULL
    END AS gcs_motor,

    CASE
        WHEN verbal BETWEEN 1 AND 5
            THEN verbal
        ELSE NULL
    END AS gcs_verbal,

    CASE
        WHEN meds = 0
         AND eyes BETWEEN 1 AND 4
         AND motor BETWEEN 1 AND 6
         AND verbal BETWEEN 1 AND 5
            THEN eyes + motor + verbal
        ELSE NULL
    END AS gcs_total,

    NULLIF(urine, -1)
        AS urine_output,

    NULLIF(wbc, -1)
        AS wbc,

    NULLIF(temperature, -1)
        AS temperature,

    NULLIF(respiratoryrate, -1)
        AS respiratory_rate,

    NULLIF(sodium, -1)
        AS sodium,

    NULLIF(heartrate, -1)
        AS heart_rate,

    NULLIF(meanbp, -1)
        AS mean_arterial_pressure,

    NULLIF(ph, -1)
        AS ph,

    NULLIF(hematocrit, -1)
        AS hematocrit,

    NULLIF(creatinine, -1)
        AS creatinine,

    NULLIF(albumin, -1)
        AS albumin,

    NULLIF(pao2, -1)
        AS pao2,

    NULLIF(pco2, -1)
        AS pco2,

    NULLIF(bun, -1)
        AS bun,

    NULLIF(glucose, -1)
        AS glucose,

    NULLIF(bilirubin, -1)
        AS bilirubin,

    CASE
        WHEN fio2 BETWEEN 21 AND 100
            THEN fio2 / 100.0

        WHEN fio2 BETWEEN 0.21 AND 1.00
            THEN fio2

        ELSE NULL
    END AS fio2_fraction,

    CASE
        WHEN pao2 > 0
         AND fio2 BETWEEN 21 AND 100
            THEN pao2 / (fio2 / 100.0)

        WHEN pao2 > 0
         AND fio2 BETWEEN 0.21 AND 1.00
            THEN pao2 / fio2

        ELSE NULL
    END AS pao2_fio2_ratio

FROM apacheapsvar_selected_raw;
-----------------------------------------------------------
SELECT
    COUNT(*) AS total_lung_cancer_stays,

    COUNT(aps.patientunitstayid)
        AS stays_with_apache_aps_var,

    COUNT(*) -
    COUNT(aps.patientunitstayid)
        AS stays_without_apache_aps_var,

    ROUND(
        100.0
        * COUNT(aps.patientunitstayid)
        / COUNT(*),
        2
    ) AS coverage_percent

FROM lung_cancer_cohort_ids AS cohort

LEFT JOIN apacheapsvar_lung_cancer AS aps
    ON cohort.patientunitstayid =
       aps.patientunitstayid;
-----------------------------------------------------------
SELECT
    MIN(urine_output) AS min_urine,
    MAX(urine_output) AS max_urine,

    MIN(wbc) AS min_wbc,
    MAX(wbc) AS max_wbc,

    MIN(temperature) AS min_temperature,
    MAX(temperature) AS max_temperature,

    MIN(respiratory_rate) AS min_respiratory_rate,
    MAX(respiratory_rate) AS max_respiratory_rate,

    MIN(sodium) AS min_sodium,
    MAX(sodium) AS max_sodium,

    MIN(heart_rate) AS min_heart_rate,
    MAX(heart_rate) AS max_heart_rate,

    MIN(mean_arterial_pressure) AS min_mean_bp,
    MAX(mean_arterial_pressure) AS max_mean_bp,

    MIN(ph) AS min_ph,
    MAX(ph) AS max_ph,

    MIN(hematocrit) AS min_hematocrit,
    MAX(hematocrit) AS max_hematocrit,

    MIN(creatinine) AS min_creatinine,
    MAX(creatinine) AS max_creatinine,

    MIN(albumin) AS min_albumin,
    MAX(albumin) AS max_albumin,

    MIN(pao2) AS min_pao2,
    MAX(pao2) AS max_pao2,

    MIN(pco2) AS min_pco2,
    MAX(pco2) AS max_pco2,

    MIN(bun) AS min_bun,
    MAX(bun) AS max_bun,

    MIN(glucose) AS min_glucose,
    MAX(glucose) AS max_glucose,

    MIN(bilirubin) AS min_bilirubin,
    MAX(bilirubin) AS max_bilirubin,

    MIN(fio2_fraction) AS min_fio2_fraction,
    MAX(fio2_fraction) AS max_fio2_fraction,

    MIN(pao2_fio2_ratio) AS min_pf_ratio,
    MAX(pao2_fio2_ratio) AS max_pf_ratio

FROM apacheapsvar_lung_cancer;
-----------------------------------------------------------
SELECT
    COUNT(*) AS stays_in_both_tables,

    SUM(
        aps.gcs_total IS NOT NULL
        AND pred.gcs_total IS NOT NULL
    ) AS both_gcs_available,

    SUM(
        aps.gcs_total IS NOT NULL
        AND pred.gcs_total IS NOT NULL
        AND aps.gcs_total = pred.gcs_total
    ) AS identical_gcs,

    SUM(
        aps.gcs_total IS NOT NULL
        AND pred.gcs_total IS NOT NULL
        AND aps.gcs_total <> pred.gcs_total
    ) AS different_gcs,

    SUM(
        aps.creatinine IS NOT NULL
        AND pred.creatinine IS NOT NULL
    ) AS both_creatinine_available,

    ROUND(
        AVG(
            CASE
                WHEN aps.creatinine IS NOT NULL
                 AND pred.creatinine IS NOT NULL
                    THEN ABS(
                        aps.creatinine -
                        pred.creatinine
                    )
                ELSE NULL
            END
        ),
        4
    ) AS mean_absolute_creatinine_difference,

    SUM(
        aps.pao2_fio2_ratio IS NOT NULL
        AND pred.pao2_fio2_ratio IS NOT NULL
    ) AS both_pf_ratio_available,

    ROUND(
        AVG(
            CASE
                WHEN aps.pao2_fio2_ratio IS NOT NULL
                 AND pred.pao2_fio2_ratio IS NOT NULL
                    THEN ABS(
                        aps.pao2_fio2_ratio -
                        pred.pao2_fio2_ratio
                    )
                ELSE NULL
            END
        ),
        4
    ) AS mean_absolute_pf_ratio_difference

FROM apacheapsvar_lung_cancer AS aps

INNER JOIN apachepredvar_model_features AS pred
    ON aps.patientunitstayid =
       pred.patientunitstayid;
-----------------------------------------------------------
SELECT
    CASE
        WHEN aps.patientunitstayid IS NOT NULL
         AND pred.patientunitstayid IS NOT NULL
            THEN 'both_tables'

        WHEN aps.patientunitstayid IS NOT NULL
         AND pred.patientunitstayid IS NULL
            THEN 'aps_only'

        WHEN aps.patientunitstayid IS NULL
         AND pred.patientunitstayid IS NOT NULL
            THEN 'pred_only'

        ELSE 'neither_table'
    END AS availability_group,

    COUNT(*) AS number_of_stays

FROM lung_cancer_cohort_ids AS cohort

LEFT JOIN apacheapsvar_lung_cancer AS aps
    ON cohort.patientunitstayid =
       aps.patientunitstayid

LEFT JOIN apachepredvar_lung_cancer AS pred
    ON cohort.patientunitstayid =
       pred.patientunitstayid

GROUP BY availability_group

ORDER BY availability_group;
-----------------------------------------------------------

-----------------------------------------------------------

-----------------------------------------------------------

-----------------------------------------------------------

-----------------------------------------------------------

-----------------------------------------------------------

-----------------------------------------------------------

-----------------------------------------------------------

-----------------------------------------------------------

-----------------------------------------------------------

-----------------------------------------------------------

-----------------------------------------------------------
