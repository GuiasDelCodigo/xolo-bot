
-- ENUMS --
CREATE TYPE job_modality_enum AS ENUM (
    'PRESENCIAL',
    'REMOTO',
    'HIBRIDO',
    'NO ESPECIFICADO'
);

CREATE TYPE chat_context_type_enum AS ENUM (
    'DM',
    'CHANNEL'
);

CREATE TYPE chat_message_role_enum AS ENUM (
    'USER',
    'ADMIN',
    'BOT'
);


-- Scraper --
CREATE TABLE IF NOT EXISTS job_offers (
    offer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category scraper_category_enum NOT NULL,
    source VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL,
    company VARCHAR(100) NOT NULL,
    offer_location VARCHAR(100) NOT NULL DEFAULT 'No especificada',
    modality job_modality_enum NOT NULL DEFAULT 'NO ESPECIFICADO',
    salary FLOAT DEFAULT NULL,
    offer_url TEXT NOT NULL
);


-- AI Chatbot --
CREATE TABLE IF NOT EXISTS ai_conversation (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context_type chat_context_type_enum NOT NULL,
    user_id BIGINT,
    channel_id BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_ai_conversation_user_id
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_ai_conversation_channel_id
        FOREIGN KEY (channel_id)
        REFERENCES channels(channel_id)
        ON DELETE CASCADE,
    CONSTRAINT chk_ai_conversation_context CHECK (
        (context_type = 'DM' AND user_id IS NOT NULL AND channel_id IS NULL) OR
        (context_type = 'CHANNEL' AND channel_id IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS chat_messages (
    messages_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL,
    author_user_id BIGINT,
    role chat_message_role_enum NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_chat_messages_conversation_id
        FOREIGN KEY (conversation_id)
        REFERENCES ai_conversation(conversation_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_chat_messages_author_user_id
        FOREIGN KEY (author_user_id)
        REFERENCES users(user_id)
        ON DELETE SET NULL
);
