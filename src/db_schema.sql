CREATE TABLE IF NOT EXISTS channels
(
    id            INTEGER PRIMARY KEY,
    channel_id    INTEGER,
    channel_url   TEXT,
    channel_title TEXT,
    channel_name  TEXT UNIQUE,
    user_count    INTEGER,
    date          TIMESTAMPTZ(0) NOT NULL,
    scam          BOOLEAN,
    has_link      BOOLEAN,
    fake          BOOLEAN
);



CREATE TABLE IF NOT EXISTS messages
(
    id                                INTEGER PRIMARY KEY,
    message_id                        INTEGER,
    channel_id                        INTEGER,
    channel_name                      TEXT,
    message_date                      TIMESTAMPTZ(0) DEFAULT NULL,
    message_pinned                    BOOLEAN        DEFAULT FALSE,
    message_text                      TEXT           DEFAULT NULL,
    message_media                     BOOLEAN        DEFAULT FALSE,
    message_views                     INTEGER        DEFAULT 0,
    message_forwards                  INTEGER        DEFAULT 0,
    message_edit_date                 TIMESTAMPTZ(0) DEFAULT NULL,
    url_in_message                    TEXT           DEFAULT NULL,
    message_fwd_from                  BOOLEAN        DEFAULT FALSE,
    message_fwd_from_date             TIMESTAMPTZ(0) DEFAULT NULL,
    message_fwd_from_channel_id       INTEGER        DEFAULT 0,
    message_fwd_from_channel_username TEXT           DEFAULT NULL,
    message_fwd_from_channel_link     TEXT           DEFAULT NULL,
    last_processed_message_id         INTEGER        DEFAULT 0,
    UNIQUE (message_id, channel_id)

);



CREATE TABLE IF NOT EXISTS images
(
    id           INTEGER PRIMARY KEY,
    channel_id   INTEGER,
    channel_name TEXT,
    message_id   INTEGER,
    photo_id     INTEGER,
    image_data   BLOB
);


CREATE TABLE IF NOT EXISTS reactions
(
    id             INTEGER PRIMARY KEY,
    message_id     INTEGER,
    channel_id     INTEGER,
    channel_name   TEXT,
    emoticon       TEXT    DEFAULT NULL,
    emoticon_count INTEGER DEFAULT NULL,
    FOREIGN KEY (message_id, channel_id) REFERENCES messages (message_id, channel_id)
);

CREATE TABLE IF NOT EXISTS documents
(
    id           INTEGER PRIMARY KEY,
    message_id   INTEGER,
    channel_id   INTEGER,
    channel_name TEXT,
    mime_type    TEXT,
    file_name    TEXT,
    file_blob    BLOB
)
