
-- ENUMS --
CREATE TYPE rol_enum AS ENUM(
    'USER',
    'ADMIN',
    'DEVELOPER'
);

CREATE TYPE channel_kind_enum AS ENUM(
    'WELCOME',
    'MUSIC',
    'SCRAPER',
    'GITHUB'
);

CREATE TYPE scraper_category_enum AS ENUM (
    'DESARROLLO_SOFTWARE',
    'DATOS_IA',
    'CIBERSEGURIDAD',
    'CLOUD_DEVOPS'
);


-- Discord Core --
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    user_name VARCHAR(50) NOT NULL,
    is_banned BOOLEAN NOT NULL DEFAULT FALSE,
    rol rol_enum NOT NULL DEFAULT 'USUARIO',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS guilds (
    guild_id BIGINT PRIMARY KEY,
    guild_name VARCHAR(100) NOT NULL,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS channels (
    channel_id BIGINT PRIMARY KEY,
    channel_name VARCHAR(100) NOT NULL,
    guild_id BIGINT NOT NULL,
    kind channel_kind_enum DEFAULT NULL,
    scraper_category scraper_category_enum DEFAULT NULL,
    ai_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_channels_guild_id
        FOREIGN KEY (guild_id)
        REFERENCES guilds(guild_id)
        ON DELETE CASCADE,
    CONSTRAINT chk_channel_scraper_category CHECK (
        (kind = 'SCRAPER' AND scraper_category IS NOT NULL) OR 
        (kind IS DISTINCT FROM 'SCRAPER' AND scraper_category IS NULL)
    )
);


-- Music --
CREATE TABLE IF NOT EXISTS tracks (
    track_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    track_name VARCHAR(255) NOT NULL,
    artist VARCHAR(100) NOT NULL DEFAULT 'Desconocido',
    duration_seconds INT NOT NULL DEFAULT 0,
    track_url TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS playlists (
    playlist_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    playlist_name VARCHAR(100) NOT NULL,
    description TEXT DEFAULT '',
    guild_id BIGINT NOT NULL,
    is_public BOOLEAN NOT NULL DEFAULT TRUE,
    created_by BIGINT NOT NULL,
    last_updated_by BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_playlists_guild_id
        FOREIGN KEY (guild_id)
        REFERENCES guilds(guild_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_playlists_created_by
        FOREIGN KEY (created_by)
        REFERENCES users(user_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_playlists_last_updated_by
        FOREIGN KEY (last_updated_by)
        REFERENCES users(user_id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS playlists_tracks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    playlist_id UUID NOT NULL,
    track_id UUID NOT NULL,
    position INT NOT NULL,
    CONSTRAINT fk_playlists_tracks_playlist_id
        FOREIGN KEY (playlist_id)
        REFERENCES playlists(playlist_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_playlists_tracks_track_id
        FOREIGN KEY (track_id)
        REFERENCES tracks(track_id)
        ON DELETE CASCADE,
    CONSTRAINT uq_playlists_track_position
        UNIQUE (playlist_id, position)
);