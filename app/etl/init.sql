-- Initial Metric Groups
INSERT OR IGNORE INTO metric_groups (group_id, name, description) VALUES
    ('body', 'Body Composition', 'Weight, BMI, and body composition metrics'),
    ('heart', 'Heart', 'Heart rate and related cardiovascular metrics'),
    ('sleep', 'Sleep', 'Sleep duration and quality metrics'),
    ('breathing', 'Breathing', 'Respiratory rate and blood oxygen metrics'),
    ('activity', 'Activity', 'Physical activity and movement metrics');

-- Initial Metrics
INSERT OR IGNORE INTO metrics (metric_id, group_id, name, unit, description) VALUES
    -- Body Composition
    ('weight', 'body', 'Weight', 'kg', 'Body weight'),
    ('height', 'body', 'Height', 'm', 'Body height'),
    ('bmi', 'body', 'BMI', 'kg/m²', 'Body Mass Index'),
    ('fat_ratio', 'body', 'Body Fat', '%', 'Body fat percentage'),
    ('fat_mass', 'body', 'Fat Mass', 'kg', 'Fat mass weight'),
    ('fat_free_mass', 'body', 'Fat Free Mass', 'kg', 'Mass without fat'),
    ('muscle_mass', 'body', 'Muscle Mass', 'kg', 'Total muscle mass'),
    ('bone_mass', 'body', 'Bone Mass', 'kg', 'Bone mass'),
    ('hydration', 'body', 'Hydration', 'kg', 'Body water content'),
    ('visceral_fat', 'body', 'Visceral Fat', 'index', 'Visceral fat rating'),
    ('bp_systolic', 'body', 'Systolic Blood Pressure', 'mmHg', 'Systolic blood pressure'),
    ('bp_diastolic', 'body', 'Diastolic Blood Pressure', 'mmHg', 'Diastolic blood pressure'),

    -- Heart
    ('hr_avg', 'heart', 'Average Heart Rate', 'bpm', 'Average heart rate'),
    ('hr_min', 'heart', 'Minimum Heart Rate', 'bpm', 'Minimum heart rate'),
    ('hr_max', 'heart', 'Maximum Heart Rate', 'bpm', 'Maximum heart rate'),
    ('rhr', 'heart', 'Resting Heart Rate', 'bpm', 'Resting heart rate'),
    ('hrv', 'heart', 'Heart Rate Variability', 'ms', 'Heart rate variability'),

    -- Sleep
    ('sleep_total', 'sleep', 'Total Sleep', 'minutes', 'Total sleep duration'),
    ('sleep_rem', 'sleep', 'REM Sleep', 'minutes', 'REM sleep duration'),
    ('sleep_deep', 'sleep', 'Deep Sleep', 'minutes', 'Deep sleep duration'),
    ('sleep_light', 'sleep', 'Light Sleep', 'minutes', 'Light sleep duration'),
    ('sleep_score', 'sleep', 'Sleep Score', 'score', 'Overall sleep quality score'),

    -- Breathing
    ('spo2_avg', 'breathing', 'Average SpO2', '%', 'Average blood oxygen saturation'),
    ('spo2_min', 'breathing', 'Minimum SpO2', '%', 'Minimum blood oxygen saturation'),
    ('resp_rate', 'breathing', 'Respiratory Rate', 'br/min', 'Breaths per minute'),

    -- Activity
    ('steps', 'activity', 'Steps', 'count', 'Daily step count'),
    ('intensity_mod', 'activity', 'Moderate Activity', 'minutes', 'Moderate intensity activity duration'),
    ('intensity_vig', 'activity', 'Vigorous Activity', 'minutes', 'Vigorous intensity activity duration'),
    ('calories_active', 'activity', 'Active Calories', 'kcal', 'Calories burned during activity'),
    ('body_battery', 'activity', 'Body Battery', 'score', 'Energy level score');

-- Initialize sync status
INSERT OR IGNORE INTO sync_status (source) VALUES 
    ('withings'),
    ('garmin');