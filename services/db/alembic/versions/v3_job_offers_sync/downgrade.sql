DROP INDEX IF EXISTS uq_job_offers_url_hash;
ALTER TABLE job_offers DROP COLUMN IF EXISTS synced_at;
ALTER TABLE job_offers DROP COLUMN IF EXISTS published_at;
ALTER TABLE job_offers DROP COLUMN IF EXISTS url_hash;
