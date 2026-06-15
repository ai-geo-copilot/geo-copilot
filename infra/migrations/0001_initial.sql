CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS method_documents (
  id text PRIMARY KEY,
  source_type text NOT NULL,
  title text NOT NULL,
  source_url text,
  trust_level text NOT NULL,
  version text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS method_chunks (
  id text PRIMARY KEY,
  document_id text NOT NULL REFERENCES method_documents(id),
  chunk_text text NOT NULL,
  method_type text NOT NULL,
  page_type text NOT NULL,
  failure_type text,
  asset_type text,
  tags text[] NOT NULL DEFAULT '{}',
  embedding vector(1024),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS analyses (
  id uuid PRIMARY KEY,
  input_url text NOT NULL,
  final_url text,
  status text NOT NULL,
  language text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz,
  error_code text
);

CREATE TABLE IF NOT EXISTS page_evidence_packs (
  analysis_id uuid PRIMARY KEY REFERENCES analyses(id),
  evidence_json jsonb NOT NULL,
  raw_html_path text,
  clean_text_path text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS retrieval_traces (
  id bigserial PRIMARY KEY,
  analysis_id uuid NOT NULL REFERENCES analyses(id),
  query_json jsonb NOT NULL,
  retrieved_chunk_ids text[] NOT NULL DEFAULT '{}',
  scores_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS diagnoses (
  analysis_id uuid PRIMARY KEY REFERENCES analyses(id),
  model text NOT NULL,
  prompt_pack_json jsonb NOT NULL,
  response_json jsonb NOT NULL,
  validated_report_json jsonb NOT NULL,
  usage_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
