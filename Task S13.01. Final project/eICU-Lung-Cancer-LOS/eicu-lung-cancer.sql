# Enabling local CSV loading
SHOW GLOBAL VARIABLES LIKE 'local_infile';

SET GLOBAL local_infile = 1;

SHOW GLOBAL VARIABLES LIKE 'local_infile';

# Creating a local project database
CREATE DATABASE IF NOT EXISTS eicu_lung_cancer
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE eicu_lung_cancer;

# Creating the reduced APACHE table
DROP TABLE IF EXISTS apachepatientresult_selected;

CREATE TABLE apachepatientresult_selected
(
    patientunitstayid             INT         NOT NULL,
    apacheversion                 VARCHAR(5)  NOT NULL,
    acutephysiologyscore          INT         NULL,
    apachescore                   INT         NULL,
    predictedicumortality         VARCHAR(50) NULL,
    predictedhospitalmortality    VARCHAR(50) NULL,
    predictediculos               DOUBLE      NULL,

    INDEX idx_apr_patientunitstayid (patientunitstayid),
    INDEX idx_apr_apacheversion (apacheversion)
);

# Importing only the required fields
LOAD DATA LOCAL INFILE
'D:/Spain/Online Courses/10. Data Analysis Specialization/3. Python/Sprint 13/Assignment/eicu-lung-cancer-los/data/full/apachePatientResult.csv'
INTO TABLE apachepatientresult_selected
CHARACTER SET utf8mb4
FIELDS
    TERMINATED BY ','
    OPTIONALLY ENCLOSED BY '"'
    ESCAPED BY '"'
LINES
    TERMINATED BY '\n'
IGNORE 1 LINES
(
    @apachepatientresultsid,
    @patientunitstayid,
    @physicianspeciality,
    @physicianinterventioncategory,
    @acutephysiologyscore,
    @apachescore,
    @apacheversion,
    @predictedicumortality,
    @actualicumortality,
    @predictediculos,
    @actualiculos,
    @predictedhospitalmortality,
    @actualhospitalmortality,
    @predictedhospitallos,
    @actualhospitallos,
    @preopmi,
    @preopcardiaccath,
    @ptcawithin24h,
    @unabridgedunitlos,
    @unabridgedhosplos,
    @actualventdays,
    @predventdays,
    @unabridgedactualventdays
)
SET
    patientunitstayid =
        NULLIF(TRIM(@patientunitstayid), ''),

    apacheversion =
        NULLIF(TRIM(@apacheversion), ''),

    acutephysiologyscore =
        NULLIF(TRIM(@acutephysiologyscore), ''),

    apachescore =
        NULLIF(TRIM(@apachescore), ''),

    predictedicumortality =
        NULLIF(TRIM(@predictedicumortality), ''),

    predictedhospitalmortality =
        NULLIF(TRIM(@predictedhospitalmortality), ''),

    predictediculos =
        NULLIF(TRIM(@predictediculos), '');
        
        
# Creating the cohort ID table in MySQL        
USE eicu_lung_cancer;

DROP TABLE IF EXISTS lung_cancer_cohort_ids;

CREATE TABLE lung_cancer_cohort_ids
(
    patientunitstayid INT NOT NULL,

    PRIMARY KEY (patientunitstayid)
);

# Importing the ID-only CSV
LOAD DATA LOCAL INFILE
'D:/Spain/Online Courses/10. Data Analysis Specialization/3. Python/Sprint 13/Assignment/eicu-lung-cancer-los/private_data/reduced/lung_cancer_cohort_ids.csv'
INTO TABLE lung_cancer_cohort_ids
CHARACTER SET utf8mb4
FIELDS
    TERMINATED BY ','
    OPTIONALLY ENCLOSED BY '"'
LINES
    TERMINATED BY '\n'
IGNORE 1 LINES
(
    @patientunitstayid
)
SET
    patientunitstayid =
        CAST(
            TRIM(
                REPLACE(
                    @patientunitstayid,
                    '\r',
                    ''
                )
            )
            AS UNSIGNED
        );
        
# Creating the lung-cancer APACHE table        
DROP TABLE IF EXISTS apachepatientresult_iva_lung_cancer;

CREATE TABLE apachepatientresult_iva_lung_cancer AS

SELECT
    cohort.patientunitstayid,
    apr.acutephysiologyscore,
    apr.apachescore,
    apr.predictedicumortality,
    apr.predictedhospitalmortality,
    apr.predictediculos

FROM lung_cancer_cohort_ids AS cohort

INNER JOIN apachepatientresult_iva AS apr
    ON cohort.patientunitstayid =
       apr.patientunitstayid;

# Adding an index       
ALTER TABLE apachepatientresult_iva_lung_cancer
ADD PRIMARY KEY (patientunitstayid);


# Creating the reduced patient table in MySQL
USE eicu_lung_cancer;

DROP TABLE IF EXISTS lung_cancer_patient_outcomes;

CREATE TABLE lung_cancer_patient_outcomes
(
    patientunitstayid          INT         NOT NULL,
    unitdischargeoffset        INT         NULL,
    unitdischargestatus        VARCHAR(50) NULL,
    hospitaldischargestatus    VARCHAR(50) NULL,

    PRIMARY KEY (patientunitstayid)
);

# Importing the reduced CSV
LOAD DATA LOCAL INFILE
'D:/Spain/Online Courses/10. Data Analysis Specialization/3. Python/Sprint 13/Assignment/eicu-lung-cancer-los/private_data/reduced/lung_cancer_patient_outcomes.csv'
INTO TABLE lung_cancer_patient_outcomes
CHARACTER SET utf8mb4
FIELDS
    TERMINATED BY ','
    OPTIONALLY ENCLOSED BY '"'
LINES
    TERMINATED BY '\n'
IGNORE 1 LINES
(
    @patientunitstayid,
    @unitdischargeoffset,
    @unitdischargestatus,
    @hospitaldischargestatus
)
SET
    patientunitstayid =
        CAST(TRIM(REPLACE(@patientunitstayid, '\r', '')) AS UNSIGNED),

    unitdischargeoffset =
        NULLIF(TRIM(REPLACE(@unitdischargeoffset, '\r', '')), ''),

    unitdischargestatus =
        NULLIF(TRIM(REPLACE(@unitdischargestatus, '\r', '')), ''),

    hospitaldischargestatus =
        NULLIF(TRIM(REPLACE(@hospitaldischargestatus, '\r', '')), '');
        
        
# Clearing the incorrectly imported MySQL rows
USE eicu_lung_cancer;

TRUNCATE TABLE lung_cancer_patient_outcomes;


# Reloading the corrected CSV
LOAD DATA LOCAL INFILE
'D:/Spain/Online Courses/10. Data Analysis Specialization/3. Python/Sprint 13/Assignment/eicu-lung-cancer-los/private_data/reduced/lung_cancer_patient_outcomes.csv'
INTO TABLE lung_cancer_patient_outcomes
CHARACTER SET utf8mb4
FIELDS
    TERMINATED BY ','
    OPTIONALLY ENCLOSED BY '"'
LINES
    TERMINATED BY '\n'
IGNORE 1 LINES
(
    @patientunitstayid,
    @unitdischargeoffset,
    @unitdischargestatus,
    @hospitaldischargestatus
)
SET
    patientunitstayid =
        CAST(
            TRIM(
                REPLACE(@patientunitstayid, '\r', '')
            )
            AS UNSIGNED
        ),

    unitdischargeoffset =
        NULLIF(
            TRIM(
                REPLACE(@unitdischargeoffset, '\r', '')
            ),
            ''
        ),

    unitdischargestatus =
        NULLIF(
            TRIM(
                REPLACE(@unitdischargestatus, '\r', '')
            ),
            ''
        ),

    hospitaldischargestatus =
        NULLIF(
            TRIM(
                REPLACE(@hospitaldischargestatus, '\r', '')
            ),
            ''
        );
        
        
# Creating the reduced raw MySQL table for apachePredVar
USE eicu_lung_cancer;

DROP TABLE IF EXISTS apachepredvar_selected_raw;

CREATE TABLE apachepredvar_selected_raw
(
    patientunitstayid      INT         NOT NULL,

    admitsource            SMALLINT    NULL,
    admitdiagnosis         VARCHAR(20) NULL,

    meds                   SMALLINT    NULL,
    verbal                 SMALLINT    NULL,
    motor                  SMALLINT    NULL,
    eyes                   SMALLINT    NULL,

    aids                   SMALLINT    NULL,
    hepaticfailure         SMALLINT    NULL,
    lymphoma               SMALLINT    NULL,
    metastaticcancer       SMALLINT    NULL,
    leukemia               SMALLINT    NULL,
    immunosuppression      SMALLINT    NULL,
    cirrhosis              SMALLINT    NULL,
    diabetes               SMALLINT    NULL,
    midur                  SMALLINT    NULL,

    electivesurgery        SMALLINT    NULL,
    activetx               SMALLINT    NULL,
    readmit                SMALLINT    NULL,

    ventday1               SMALLINT    NULL,
    oobventday1            SMALLINT    NULL,
    oobintubday1           SMALLINT    NULL,

    pao2                   DOUBLE      NULL,
    fio2                   DOUBLE      NULL,
    creatinine             DOUBLE      NULL,

    day1meds               SMALLINT    NULL,
    day1verbal             SMALLINT    NULL,
    day1motor              SMALLINT    NULL,
    day1eyes               SMALLINT    NULL,
    day1pao2               DOUBLE      NULL,
    day1fio2               DOUBLE      NULL,

    INDEX idx_apv_patientunitstayid (patientunitstayid)
);


# Importing apachePredVar.csv
LOAD DATA LOCAL INFILE
'D:/Spain/Online Courses/10. Data Analysis Specialization/3. Python/Sprint 13/Assignment/eicu-lung-cancer-los/data/full/apachePredVar.csv'
INTO TABLE apachepredvar_selected_raw
CHARACTER SET utf8mb4

FIELDS
    TERMINATED BY ','
    OPTIONALLY ENCLOSED BY '"'
    ESCAPED BY '"'

LINES
    TERMINATED BY '\n'

IGNORE 1 LINES

(
    @apachepredvarid,
    @patientunitstayid,
    @sicuday,
    @saps3day1,
    @saps3today,
    @saps3yesterday,
    @gender,
    @teachtype,
    @region,
    @bedcount,
    @admitsource,
    @graftcount,
    @meds,
    @verbal,
    @motor,
    @eyes,
    @age,
    @admitdiagnosis,
    @thrombolytics,
    @diedinhospital,
    @aids,
    @hepaticfailure,
    @lymphoma,
    @metastaticcancer,
    @leukemia,
    @immunosuppression,
    @cirrhosis,
    @electivesurgery,
    @activetx,
    @readmit,
    @ima,
    @midur,
    @ventday1,
    @oobventday1,
    @oobintubday1,
    @diabetes,
    @managementsystem,
    @var03hspxlos,
    @pao2,
    @fio2,
    @ejectfx,
    @creatinine,
    @dischargelocation,
    @visitnumber,
    @amilocation,
    @day1meds,
    @day1verbal,
    @day1motor,
    @day1eyes,
    @day1pao2,
    @day1fio2
)

SET
    patientunitstayid =
        CAST(
            TRIM(
                REPLACE(
                    @patientunitstayid,
                    '\r',
                    ''
                )
            )
            AS UNSIGNED
        ),

    admitsource =
        NULLIF(
            TRIM(@admitsource),
            ''
        ),

    admitdiagnosis =
        NULLIF(
            TRIM(@admitdiagnosis),
            ''
        ),

    meds =
        NULLIF(TRIM(@meds), ''),

    verbal =
        NULLIF(TRIM(@verbal), ''),

    motor =
        NULLIF(TRIM(@motor), ''),

    eyes =
        NULLIF(TRIM(@eyes), ''),

    aids =
        NULLIF(TRIM(@aids), ''),

    hepaticfailure =
        NULLIF(TRIM(@hepaticfailure), ''),

    lymphoma =
        NULLIF(TRIM(@lymphoma), ''),

    metastaticcancer =
        NULLIF(TRIM(@metastaticcancer), ''),

    leukemia =
        NULLIF(TRIM(@leukemia), ''),

    immunosuppression =
        NULLIF(TRIM(@immunosuppression), ''),

    cirrhosis =
        NULLIF(TRIM(@cirrhosis), ''),

    diabetes =
        NULLIF(TRIM(@diabetes), ''),

    midur =
        NULLIF(TRIM(@midur), ''),

    electivesurgery =
        NULLIF(TRIM(@electivesurgery), ''),

    activetx =
        NULLIF(TRIM(@activetx), ''),

    readmit =
        NULLIF(TRIM(@readmit), ''),

    ventday1 =
        NULLIF(TRIM(@ventday1), ''),

    oobventday1 =
        NULLIF(TRIM(@oobventday1), ''),

    oobintubday1 =
        NULLIF(TRIM(@oobintubday1), ''),

    pao2 =
        NULLIF(TRIM(@pao2), ''),

    fio2 =
        NULLIF(TRIM(@fio2), ''),

    creatinine =
        NULLIF(TRIM(@creatinine), ''),

    day1meds =
        NULLIF(TRIM(@day1meds), ''),

    day1verbal =
        NULLIF(TRIM(@day1verbal), ''),

    day1motor =
        NULLIF(TRIM(@day1motor), ''),

    day1eyes =
        NULLIF(TRIM(@day1eyes), ''),

    day1pao2 =
        NULLIF(TRIM(@day1pao2), ''),

    day1fio2 =
        NULLIF(
            TRIM(
                REPLACE(
                    @day1fio2,
                    '\r',
                    ''
                )
            ),
            ''
        );
        
        
# Filtering to the lung-cancer cohort
DROP TABLE IF EXISTS apachepredvar_lung_cancer;

CREATE TABLE apachepredvar_lung_cancer AS

SELECT
    apv.*

FROM lung_cancer_cohort_ids AS cohort

INNER JOIN apachepredvar_clean AS apv
    ON cohort.patientunitstayid =
       apv.patientunitstayid;
       
       
# Adding the key
ALTER TABLE apachepredvar_lung_cancer
ADD PRIMARY KEY (patientunitstayid);


# Creating the raw reduced MySQL table for apacheApsVar
USE eicu_lung_cancer;

DROP TABLE IF EXISTS apacheapsvar_selected_raw;

CREATE TABLE apacheapsvar_selected_raw
(
    patientunitstayid  INT      NOT NULL,

    intubated          SMALLINT NULL,
    vent               SMALLINT NULL,
    dialysis           SMALLINT NULL,

    eyes               SMALLINT NULL,
    motor              SMALLINT NULL,
    verbal             SMALLINT NULL,
    meds               SMALLINT NULL,

    urine              DOUBLE   NULL,
    wbc                DOUBLE   NULL,
    temperature        DOUBLE   NULL,
    respiratoryrate    DOUBLE   NULL,
    sodium             DOUBLE   NULL,
    heartrate          DOUBLE   NULL,
    meanbp             DOUBLE   NULL,
    ph                 DOUBLE   NULL,
    hematocrit         DOUBLE   NULL,
    creatinine         DOUBLE   NULL,
    albumin            DOUBLE   NULL,
    pao2               DOUBLE   NULL,
    pco2               DOUBLE   NULL,
    bun                DOUBLE   NULL,
    glucose            DOUBLE   NULL,
    bilirubin          DOUBLE   NULL,
    fio2               DOUBLE   NULL,

    INDEX idx_aav_patientunitstayid (patientunitstayid)
);


# Importing apacheApsVar.csv
LOAD DATA LOCAL INFILE
'D:/Spain/Online Courses/10. Data Analysis Specialization/3. Python/Sprint 13/Assignment/eicu-lung-cancer-los/data/full/apacheApsVar.csv'

INTO TABLE apacheapsvar_selected_raw

CHARACTER SET utf8mb4

FIELDS
    TERMINATED BY ','
    OPTIONALLY ENCLOSED BY '"'
    ESCAPED BY '"'

LINES
    TERMINATED BY '\n'

IGNORE 1 LINES

(
    @apacheapsvarid,
    @patientunitstayid,
    @intubated,
    @vent,
    @dialysis,
    @eyes,
    @motor,
    @verbal,
    @meds,
    @urine,
    @wbc,
    @temperature,
    @respiratoryrate,
    @sodium,
    @heartrate,
    @meanbp,
    @ph,
    @hematocrit,
    @creatinine,
    @albumin,
    @pao2,
    @pco2,
    @bun,
    @glucose,
    @bilirubin,
    @fio2
)

SET
    patientunitstayid =
        CAST(
            TRIM(
                REPLACE(
                    @patientunitstayid,
                    '\r',
                    ''
                )
            )
            AS UNSIGNED
        ),

    intubated =
        NULLIF(TRIM(@intubated), ''),

    vent =
        NULLIF(TRIM(@vent), ''),

    dialysis =
        NULLIF(TRIM(@dialysis), ''),

    eyes =
        NULLIF(TRIM(@eyes), ''),

    motor =
        NULLIF(TRIM(@motor), ''),

    verbal =
        NULLIF(TRIM(@verbal), ''),

    meds =
        NULLIF(TRIM(@meds), ''),

    urine =
        NULLIF(TRIM(@urine), ''),

    wbc =
        NULLIF(TRIM(@wbc), ''),

    temperature =
        NULLIF(TRIM(@temperature), ''),

    respiratoryrate =
        NULLIF(TRIM(@respiratoryrate), ''),

    sodium =
        NULLIF(TRIM(@sodium), ''),

    heartrate =
        NULLIF(TRIM(@heartrate), ''),

    meanbp =
        NULLIF(TRIM(@meanbp), ''),

    ph =
        NULLIF(TRIM(@ph), ''),

    hematocrit =
        NULLIF(TRIM(@hematocrit), ''),

    creatinine =
        NULLIF(TRIM(@creatinine), ''),

    albumin =
        NULLIF(TRIM(@albumin), ''),

    pao2 =
        NULLIF(TRIM(@pao2), ''),

    pco2 =
        NULLIF(TRIM(@pco2), ''),

    bun =
        NULLIF(TRIM(@bun), ''),

    glucose =
        NULLIF(TRIM(@glucose), ''),

    bilirubin =
        NULLIF(TRIM(@bilirubin), ''),

    fio2 =
        NULLIF(
            TRIM(
                REPLACE(
                    @fio2,
                    '\r',
                    ''
                )
            ),
            ''
        );
        
        
# Filtering to the lung-cancer cohort
DROP TABLE IF EXISTS apacheapsvar_lung_cancer;

CREATE TABLE apacheapsvar_lung_cancer AS

SELECT
    aps.*

FROM lung_cancer_cohort_ids AS cohort

INNER JOIN apacheapsvar_clean AS aps
    ON cohort.patientunitstayid =
       aps.patientunitstayid;
       
       
# Adding the primary key
ALTER TABLE apacheapsvar_lung_cancer
ADD PRIMARY KEY (patientunitstayid);


# 