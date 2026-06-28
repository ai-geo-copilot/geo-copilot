ALTER TABLE provider_configs
  ADD COLUMN IF NOT EXISTS timeout_seconds double precision NOT NULL DEFAULT 60.0;

ALTER TABLE provider_configs
  ADD COLUMN IF NOT EXISTS max_retries integer NOT NULL DEFAULT 2;

ALTER TABLE provider_configs
  ADD COLUMN IF NOT EXISTS max_tokens integer NOT NULL DEFAULT 4096;
