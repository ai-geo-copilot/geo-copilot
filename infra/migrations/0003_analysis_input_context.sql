ALTER TABLE analyses
  ADD COLUMN IF NOT EXISTS input_context jsonb;
