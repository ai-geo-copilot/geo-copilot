CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY,
  email text NOT NULL UNIQUE,
  display_name text,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS conversation_threads (
  id uuid PRIMARY KEY,
  analysis_id uuid NOT NULL REFERENCES analyses(id),
  user_id uuid REFERENCES users(id),
  title text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS messages (
  id uuid PRIMARY KEY,
  thread_id uuid NOT NULL REFERENCES conversation_threads(id),
  sequence integer NOT NULL CHECK (sequence >= 0),
  role text NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content text NOT NULL,
  turn_json jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_messages_thread_sequence UNIQUE (thread_id, sequence)
);

CREATE TABLE IF NOT EXISTS provider_configs (
  id uuid PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES users(id),
  provider text NOT NULL,
  base_url text NOT NULL,
  model text NOT NULL,
  api_key_ciphertext text NOT NULL,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_provider_configs_user_provider UNIQUE (user_id, provider)
);

CREATE INDEX IF NOT EXISTS idx_conversation_threads_analysis_updated
  ON conversation_threads(analysis_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversation_threads_user_updated
  ON conversation_threads(user_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_thread_created
  ON messages(thread_id, created_at);
CREATE INDEX IF NOT EXISTS idx_provider_configs_user
  ON provider_configs(user_id);
