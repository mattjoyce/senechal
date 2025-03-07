CREATE TABLE metric_groups (
    group_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE metrics (
    metric_id TEXT PRIMARY KEY,
    group_id TEXT NOT NULL,
    name TEXT NOT NULL,
    unit TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES metric_groups(group_id)
);
CREATE TABLE summaries (
    period_type TEXT NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    metric_id TEXT NOT NULL,
    avg_value REAL,
    min_value REAL,
    max_value REAL,
    sample_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (period_type, period_start, metric_id),
    FOREIGN KEY (metric_id) REFERENCES metrics(metric_id)
);
CREATE TABLE sync_status (
    source TEXT PRIMARY KEY,
    last_sync TIMESTAMP,
    last_success TIMESTAMP,
    error_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE VIEW v_latest_summaries AS
WITH latest_updates AS (
    SELECT 
        period_type,
        metric_id,
        MAX(period_start) as latest_period
    FROM summaries
    GROUP BY period_type, metric_id
)
SELECT 
    s.*,
    m.name as metric_name,
    m.unit,
    m.group_id,
    g.name as group_name
FROM summaries s
JOIN latest_updates lu 
    ON s.period_type = lu.period_type 
    AND s.metric_id = lu.metric_id 
    AND s.period_start = lu.latest_period
JOIN metrics m ON s.metric_id = m.metric_id
JOIN metric_groups g ON m.group_id = g.group_id
/* v_latest_summaries(period_type,period_start,period_end,metric_id,avg_value,min_value,max_value,sample_count,created_at,last_updated,metric_name,unit,group_id,group_name) */
/* v_latest_summaries(period_type,period_start,period_end,metric_id,avg_value,min_value,max_value,sample_count,created_at,last_updated,metric_name,unit,group_id,group_name) */;
CREATE TABLE source_updates (
    source TEXT NOT NULL,           -- 'withings', 'garmin'
    period_type TEXT NOT NULL,      -- 'day', 'week', 'month', 'year'
    period_start DATE NOT NULL,     -- Start of period
    period_end DATE NOT NULL,       -- End of period
    raw_data_updated TIMESTAMP,     -- When source data was last updated
    summary_updated TIMESTAMP,      -- When we last calculated summary
    needs_update BOOLEAN DEFAULT 1, -- Flag for pending recalculation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (source, period_type, period_start)
);
CREATE INDEX idx_source_updates_needs_update 
ON source_updates(needs_update) 
WHERE needs_update = 1;
CREATE INDEX idx_source_updates_period 
ON source_updates(period_type, period_start, period_end);
CREATE VIEW v_pending_updates AS
SELECT 
    source,
    period_type,
    period_start,
    period_end,
    raw_data_updated,
    summary_updated
FROM source_updates
WHERE needs_update = 1
ORDER BY period_start ASC
/* v_pending_updates(source,period_type,period_start,period_end,raw_data_updated,summary_updated) */
/* v_pending_updates(source,period_type,period_start,period_end,raw_data_updated,summary_updated) */;
CREATE TABLE sync_metadata (
    source TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (source, key)
);
