CREATE TABLE tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    access_token TEXT,
    refresh_token TEXT,
    expires_at INTEGER
);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE sync_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    measurement_type TEXT NOT NULL,  -- 'weight', 'blood_pressure'
    last_sync TIMESTAMP NOT NULL,
    last_update INTEGER NOT NULL,     -- Withings lastupdate timestamp
    UNIQUE(measurement_type)
);
CREATE TABLE measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    withings_id INTEGER,              -- Withings measurement ID
    date TIMESTAMP NOT NULL,          -- Measurement timestamp
    type INTEGER NOT NULL,            -- Withings measure type
    value REAL NOT NULL,             -- Actual measurement value
    unit INTEGER,                    -- Measurement unit from Withings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(withings_id, type)        -- Prevent duplicate measurements
);
CREATE VIEW v_measurements AS
SELECT 
    m.id,
    m.withings_id,
    m.date,
    m.type,
    m.value,
    CASE m.type
        WHEN 1 THEN 'Weight'
        WHEN 4 THEN 'Height'
        WHEN 5 THEN 'Fat Free Mass'
        WHEN 6 THEN 'Fat Ratio'
        WHEN 8 THEN 'Fat Mass Weight'
        WHEN 9 THEN 'Diastolic BP'
        WHEN 10 THEN 'Systolic BP'
        WHEN 11 THEN 'Heart Rate'
        WHEN 76 THEN 'Muscle Mass'
        WHEN 77 THEN 'Hydration'
        WHEN 88 THEN 'Bone Mass'
        WHEN 170 THEN 'Visceral Fat'
        WHEN 226 THEN 'Basal Metabolic Rate'
        WHEN 227 THEN 'Skin Conductance'
        ELSE 'Unknown'
    END as measure_name,
    CASE m.type
        WHEN 1 THEN 'kg'
        WHEN 4 THEN 'm'
        WHEN 5 THEN 'kg'
        WHEN 6 THEN '%'
        WHEN 8 THEN 'kg'
        WHEN 9 THEN 'mmHg'
        WHEN 10 THEN 'mmHg'
        WHEN 11 THEN 'bpm'
        WHEN 76 THEN 'kg'
        WHEN 77 THEN 'kg'
        WHEN 88 THEN 'kg'
        WHEN 170 THEN 'index'
        WHEN 226 THEN 'kcal'
        WHEN 227 THEN 'µS'
        ELSE 'unknown'
    END as display_unit,
    m.created_at
FROM measurements m
/* v_measurements(id,withings_id,date,type,value,measure_name,display_unit,created_at) */;
CREATE VIEW v_latest_measurements AS
WITH latest_dates AS (
    SELECT type, MAX(date) as max_date
    FROM measurements
    GROUP BY type
)
SELECT 
    vm.*
FROM v_measurements vm
JOIN latest_dates ld ON vm.type = ld.type AND vm.date = ld.max_date
/* v_latest_measurements(id,withings_id,date,type,value,measure_name,display_unit,created_at)  */;
