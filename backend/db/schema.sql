-- VayuSense Database Schema
-- TimescaleDB (PostgreSQL with time-series extensions)

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS postgis;

-- ── AQI Readings (from CPCB / OpenAQ) ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS aqi_readings (
    time            TIMESTAMPTZ     NOT NULL,
    station_id      VARCHAR(64)     NOT NULL,
    station_name    VARCHAR(256),
    city            VARCHAR(64)     NOT NULL,
    ward            VARCHAR(128),
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION,
    pm25            DOUBLE PRECISION,   -- µg/m³
    pm10            DOUBLE PRECISION,   -- µg/m³
    no2             DOUBLE PRECISION,   -- µg/m³
    so2             DOUBLE PRECISION,   -- µg/m³
    co              DOUBLE PRECISION,   -- mg/m³
    o3              DOUBLE PRECISION,   -- µg/m³
    aqi             INTEGER,            -- Computed AQI (CPCB method)
    aqi_category    VARCHAR(32),        -- Good / Satisfactory / Moderate / etc.
    raw_data        JSONB
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('aqi_readings', 'time', if_not_exists => TRUE);

-- Continuous aggregate: hourly station averages
CREATE MATERIALIZED VIEW IF NOT EXISTS aqi_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    station_id, city, ward, latitude, longitude,
    AVG(pm25)  AS avg_pm25,
    AVG(pm10)  AS avg_pm10,
    AVG(no2)   AS avg_no2,
    AVG(so2)   AS avg_so2,
    AVG(aqi)   AS avg_aqi,
    MAX(aqi)   AS max_aqi
FROM aqi_readings
GROUP BY bucket, station_id, city, ward, latitude, longitude
WITH NO DATA;

-- ── Satellite Data (Sentinel-5P / MODIS) ───────────────────────────────────
CREATE TABLE IF NOT EXISTS satellite_data (
    time            TIMESTAMPTZ     NOT NULL,
    city            VARCHAR(64)     NOT NULL,
    grid_lat        DOUBLE PRECISION NOT NULL,  -- 1km grid cell center lat
    grid_lon        DOUBLE PRECISION NOT NULL,  -- 1km grid cell center lon
    no2_column      DOUBLE PRECISION,           -- tropospheric NO₂ mol/m²
    aod_550nm       DOUBLE PRECISION,           -- Aerosol Optical Depth at 550nm
    so2_column      DOUBLE PRECISION,           -- SO₂ column mol/m²
    co_column       DOUBLE PRECISION,           -- CO column mol/m²
    fire_detected   BOOLEAN DEFAULT FALSE,      -- VIIRS fire hotspot
    source          VARCHAR(32)                 -- 'sentinel5p', 'modis', 'viirs'
);

SELECT create_hypertable('satellite_data', 'time', if_not_exists => TRUE);

-- ── Weather Data (Open-Meteo) ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS weather_data (
    time                TIMESTAMPTZ     NOT NULL,
    city                VARCHAR(64)     NOT NULL,
    temperature_2m      DOUBLE PRECISION,   -- °C
    relative_humidity   DOUBLE PRECISION,   -- %
    wind_speed_10m      DOUBLE PRECISION,   -- km/h
    wind_direction_10m  DOUBLE PRECISION,   -- degrees (0=N, 90=E)
    precipitation       DOUBLE PRECISION,   -- mm
    boundary_layer_h    DOUBLE PRECISION,   -- Atmospheric boundary layer height (m)
    is_forecast         BOOLEAN DEFAULT FALSE
);

SELECT create_hypertable('weather_data', 'time', if_not_exists => TRUE);

-- ── AQI Forecasts (Model Output) ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS aqi_forecasts (
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    forecast_time       TIMESTAMPTZ     NOT NULL,   -- time being forecasted
    city                VARCHAR(64)     NOT NULL,
    ward                VARCHAR(128),
    grid_lat            DOUBLE PRECISION,
    grid_lon            DOUBLE PRECISION,
    predicted_aqi       DOUBLE PRECISION NOT NULL,
    predicted_pm25      DOUBLE PRECISION,
    confidence_lower    DOUBLE PRECISION,
    confidence_upper    DOUBLE PRECISION,
    model_version       VARCHAR(32)
);

SELECT create_hypertable('aqi_forecasts', 'forecast_time', if_not_exists => TRUE);

-- ── Source Attribution (Model Output) ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS source_attributions (
    time                TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    city                VARCHAR(64)     NOT NULL,
    ward                VARCHAR(128)    NOT NULL,
    current_aqi         INTEGER,
    vehicles_pct        DOUBLE PRECISION,   -- % contribution
    construction_pct    DOUBLE PRECISION,
    industrial_pct      DOUBLE PRECISION,
    burning_pct         DOUBLE PRECISION,   -- biomass/stubble burning
    dust_pct            DOUBLE PRECISION,   -- road/soil dust
    long_range_pct      DOUBLE PRECISION,   -- regional transport
    top_source          VARCHAR(128),       -- human-readable top source
    top_source_loc      VARCHAR(256),       -- specific location if known
    confidence          DOUBLE PRECISION,   -- 0-1
    satellite_validated BOOLEAN DEFAULT FALSE
);

SELECT create_hypertable('source_attributions', 'time', if_not_exists => TRUE);

-- ── Emission Sources Registry ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS emission_sources (
    id              SERIAL PRIMARY KEY,
    city            VARCHAR(64)     NOT NULL,
    ward            VARCHAR(128),
    source_type     VARCHAR(64),    -- 'construction', 'industrial', 'vehicle_corridor', etc.
    name            VARCHAR(256)    NOT NULL,
    latitude        DOUBLE PRECISION NOT NULL,
    longitude       DOUBLE PRECISION NOT NULL,
    reg_id          VARCHAR(64),    -- Official registration ID
    last_inspected  DATE,
    inspection_count INTEGER DEFAULT 0,
    active          BOOLEAN DEFAULT TRUE,
    notes           TEXT
);

-- ── Enforcement Actions (Agent Output) ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS enforcement_actions (
    id              SERIAL PRIMARY KEY,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    city            VARCHAR(64)     NOT NULL,
    source_id       INTEGER REFERENCES emission_sources(id),
    priority_rank   INTEGER,        -- 1 = highest priority
    impact_score    DOUBLE PRECISION,
    projected_improvement_pct DOUBLE PRECISION,  -- % AQI drop if actioned
    evidence_brief  TEXT,           -- LLM-generated brief
    legal_basis     TEXT,
    optimal_time    VARCHAR(64),
    status          VARCHAR(32) DEFAULT 'pending'  -- pending/actioned/dismissed
);

-- ── Wards Reference ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS wards (
    id              SERIAL PRIMARY KEY,
    city            VARCHAR(64)     NOT NULL,
    ward_name       VARCHAR(128)    NOT NULL,
    ward_code       VARCHAR(32),
    centroid_lat    DOUBLE PRECISION,
    centroid_lon    DOUBLE PRECISION,
    population      INTEGER,
    area_km2        DOUBLE PRECISION,
    schools_count   INTEGER DEFAULT 0,
    hospitals_count INTEGER DEFAULT 0,
    boundary        JSONB           -- GeoJSON polygon
);

-- ── Citizen Alerts Log ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS citizen_alerts (
    id              SERIAL PRIMARY KEY,
    sent_at         TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    city            VARCHAR(64)     NOT NULL,
    ward            VARCHAR(128),
    language        VARCHAR(32),
    channel         VARCHAR(32),    -- 'whatsapp', 'sms', 'push'
    message         TEXT,
    aqi_at_send     INTEGER,
    forecast_aqi    INTEGER,
    recipients_count INTEGER DEFAULT 0
);

-- ── Indexes ──────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_aqi_city_time ON aqi_readings(city, time DESC);
CREATE INDEX IF NOT EXISTS idx_aqi_station ON aqi_readings(station_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_forecast_city ON aqi_forecasts(city, forecast_time);
CREATE INDEX IF NOT EXISTS idx_attribution_city ON source_attributions(city, time DESC);
CREATE INDEX IF NOT EXISTS idx_sources_city ON emission_sources(city, source_type);

-- ── Seed Delhi Wards (key ones for demo) ────────────────────────────────────
INSERT INTO wards (city, ward_name, centroid_lat, centroid_lon, population, schools_count, hospitals_count)
VALUES
    ('Delhi', 'Dwarka', 28.5921, 77.0460, 350000, 42, 8),
    ('Delhi', 'Rohini', 28.7495, 77.0574, 420000, 58, 12),
    ('Delhi', 'Connaught Place', 28.6315, 77.2167, 45000, 8, 6),
    ('Delhi', 'Anand Vihar', 28.6469, 77.3158, 95000, 12, 4),
    ('Delhi', 'Okhla', 28.5494, 77.2750, 180000, 22, 5),
    ('Delhi', 'Punjabi Bagh', 28.6682, 77.1309, 210000, 31, 7),
    ('Delhi', 'R.K. Puram', 28.5625, 77.1741, 165000, 28, 9),
    ('Delhi', 'Shahdara', 28.6680, 77.2888, 280000, 38, 10)
ON CONFLICT DO NOTHING;

-- ── Seed Delhi Emission Sources (demo data) ──────────────────────────────────
INSERT INTO emission_sources (city, ward, source_type, name, latitude, longitude, reg_id, last_inspected)
VALUES
    ('Delhi', 'Dwarka', 'construction', 'NH-48 Airport Expansion Site', 28.5721, 77.0756, 'DL-CONST-2847', '2026-06-15'),
    ('Delhi', 'Anand Vihar', 'vehicle_corridor', 'Anand Vihar Truck Terminal', 28.6469, 77.3158, 'DL-TERM-0112', '2026-05-20'),
    ('Delhi', 'Okhla', 'industrial', 'Okhla Industrial Area Phase-II', 28.5394, 77.2681, 'DL-IND-0445', '2026-06-01'),
    ('Delhi', 'Rohini', 'construction', 'Rohini Sector 34 Housing Project', 28.7612, 77.0389, 'DL-CONST-3102', '2026-07-01'),
    ('Delhi', 'Shahdara', 'industrial', 'Shahdara Industrial Cluster', 28.6750, 77.2950, 'DL-IND-0231', '2026-04-10')
ON CONFLICT DO NOTHING;
