-- NutriTrack Database Schema
-- Run: sqlite3 nutritrack.db < database/schema.sql
-- (Flask-Migrate handles this automatically — this is for reference)

CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    name            TEXT,
    role            TEXT DEFAULT 'user',
    is_verified     BOOLEAN DEFAULT 0,
    verification_token TEXT,
    verification_sent_at DATETIME,
    reset_token     TEXT,
    reset_token_expiry DATETIME,
    age             INTEGER,
    gender          TEXT,
    height_cm       REAL,
    weight_kg       REAL,
    activity_level  TEXT DEFAULT 'moderate',
    goal            TEXT DEFAULT 'maintain',
    target_weight_kg REAL,
    target_days     INTEGER,
    profile_complete BOOLEAN DEFAULT 0,
    is_active       BOOLEAN DEFAULT 1,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login      DATETIME
);

CREATE TABLE IF NOT EXISTS food_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    log_date    DATE NOT NULL,
    meal_type   TEXT DEFAULT 'any',
    raw_input   TEXT NOT NULL,
    food_items  JSON,
    calories    REAL DEFAULT 0,
    protein_g   REAL DEFAULT 0,
    carbs_g     REAL DEFAULT 0,
    fat_g       REAL DEFAULT 0,
    fiber_g     REAL DEFAULT 0,
    sugar_g     REAL DEFAULT 0,
    sodium_mg   REAL DEFAULT 0,
    potassium_mg REAL DEFAULT 0,
    calcium_mg  REAL DEFAULT 0,
    iron_mg     REAL DEFAULT 0,
    vitamin_c_mg REAL DEFAULT 0,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nutrient_cache (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    food_name       TEXT NOT NULL UNIQUE,
    usda_fdc_id     INTEGER,
    calories_per_100g REAL DEFAULT 0,
    protein_per_100g  REAL DEFAULT 0,
    carbs_per_100g    REAL DEFAULT 0,
    fat_per_100g      REAL DEFAULT 0,
    fiber_per_100g    REAL DEFAULT 0,
    sugar_per_100g    REAL DEFAULT 0,
    sodium_per_100g   REAL DEFAULT 0,
    potassium_per_100g REAL DEFAULT 0,
    calcium_per_100g  REAL DEFAULT 0,
    iron_per_100g     REAL DEFAULT 0,
    vitamin_c_per_100g REAL DEFAULT 0,
    cached_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_food_logs_user_date ON food_logs(user_id, log_date);
CREATE INDEX IF NOT EXISTS idx_nutrient_cache_name ON nutrient_cache(food_name);
