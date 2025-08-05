CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- === CHANNELS ===
CREATE TABLE IF NOT EXISTS channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),                  -- Internal ID
    original_channel_id BIGINT UNIQUE,                              -- Telegram ID FK
    channel_url TEXT,
    username TEXT,
    title TEXT,
    participants_count INT,
    date TIMESTAMPTZ,
    scam BOOLEAN,
    verified BOOLEAN,
    fake BOOLEAN,
    has_link BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON COLUMN channels.original_channel_id IS
'Primary external identifier for Telegram channel, referenced as a foreign key by other tables. Every message must belong to a known Telegram channel';

-- === FUNCTION FOR updated_at ===
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = CURRENT_TIMESTAMP;
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- === CHANNEL STATE ===
CREATE TABLE channel_state (
    original_channel_id BIGINT PRIMARY KEY REFERENCES channels(original_channel_id) ON DELETE CASCADE,
    last_processed_message_id BIGINT,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- === MESSAGES ===
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    original_message_id BIGINT NOT NULL,
    original_channel_id BIGINT NOT NULL,

    channel_username TEXT,
    date TIMESTAMPTZ,
    message TEXT,
    message_eng TEXT,
    lang_code TEXT,
    ts_config regconfig DEFAULT 'simple',

    message_search TSVECTOR GENERATED ALWAYS AS (
        to_tsvector(ts_config, coalesce(message, ''))
    ) STORED,
    message_search_end TSVECTOR GENERATED ALWAYS AS (
        to_tsvector(ts_config, coalesce(message_eng, ''))
    ) STORED,

    pinned BOOLEAN DEFAULT FALSE,
    views INT DEFAULT 0,
    forwards INT DEFAULT 0,
    edit_date TIMESTAMPTZ,
    url_in_message TEXT,

    fwd_from TEXT,
    fwd_from_date TIMESTAMPTZ,
    fwd_from_channel_id BIGINT,
    fwd_from_channel_username TEXT,
    fwd_from_channel_link TEXT,
    fwd_from_id TEXT,
    media JSONB,

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (original_message_id, original_channel_id),

    CONSTRAINT fk_messages_channel
        FOREIGN KEY (original_channel_id)
        REFERENCES channels(original_channel_id)
        ON DELETE CASCADE
);

-- === SEARCH INDEXES ===
CREATE INDEX IF NOT EXISTS idx_message_search ON messages USING GIN (message_search);
CREATE INDEX IF NOT EXISTS idx_message_search_end ON messages USING GIN (message_search_end);


-- === REACTIONS ===
CREATE TABLE IF NOT EXISTS reactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    original_message_id BIGINT NOT NULL,
    original_channel_id BIGINT NOT NULL,

    emoticon TEXT NOT NULL,
    emoticon_base64 TEXT,
    document_id BIGINT,
    emoticon_count INT DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_reactions_message FOREIGN KEY (original_message_id, original_channel_id)
        REFERENCES messages(original_message_id, original_channel_id)
        ON DELETE CASCADE
);


-- === TRIGGERS ===
CREATE TRIGGER set_updated_at_channels
BEFORE UPDATE ON channels
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER set_updated_at_messages
BEFORE UPDATE ON messages
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER set_updated_at_channel_state
BEFORE UPDATE ON channel_state
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER set_updated_at_reactions
BEFORE UPDATE ON reactions
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();

