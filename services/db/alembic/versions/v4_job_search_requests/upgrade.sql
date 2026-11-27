DO $$ BEGIN
  CREATE TYPE job_search_status_enum AS ENUM ('PENDING', 'OK', 'FAILED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS job_search_requests (
    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query VARCHAR(200) NOT NULL,
    category scraper_category_enum NOT NULL,
    page INT NOT NULL DEFAULT 1 CHECK (page >= 1),
    num_pages INT NOT NULL DEFAULT 1 CHECK (num_pages BETWEEN 1 AND 5),
    date_posted VARCHAR(20),
    country VARCHAR(10),
    language VARCHAR(100),
    location VARCHAR(200),
    fields JSONB,
    guidelines JSONB NOT NULL DEFAULT '[]'::jsonb,
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    jsearch_request_id VARCHAR(100),
    jsearch_status VARCHAR(20),
    cursor VARCHAR(200),
    status job_search_status_enum NOT NULL DEFAULT 'PENDING',
    total_found INT NOT NULL DEFAULT 0,
    inserted INT NOT NULL DEFAULT 0,
    updated INT NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_job_search_requests_created_at
    ON job_search_requests (created_at DESC);
