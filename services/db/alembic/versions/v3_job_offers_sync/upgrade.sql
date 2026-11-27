DELETE FROM job_offers a
USING job_offers b
WHERE a.offer_id > b.offer_id
  AND a.offer_url = b.offer_url;

ALTER TABLE job_offers ADD COLUMN IF NOT EXISTS url_hash VARCHAR(32);
UPDATE job_offers SET url_hash = md5(offer_url) WHERE url_hash IS NULL;
ALTER TABLE job_offers ALTER COLUMN url_hash SET NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_job_offers_url_hash ON job_offers (url_hash);

ALTER TABLE job_offers ADD COLUMN IF NOT EXISTS published_at TIMESTAMPTZ;
ALTER TABLE job_offers ADD COLUMN IF NOT EXISTS synced_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
