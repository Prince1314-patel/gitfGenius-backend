CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    relationship_type VARCHAR(100),
    birthday DATE,
    user_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS memories (
    id UUID PRIMARY KEY,
    content TEXT NOT NULL,
    contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL
);
