CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL, 
    email VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE templates (
    id SERIAL PRIMARY KEY,
    author_id INTEGER NOT NULL REFERENCES users(id),
    title VARCHAR(100) NOT NULL,
    title_page_path VARCHAR(255) NOT NULL,
    preview_path VARCHAR(255),
    default_font_face VARCHAR(50) DEFAULT 'Times New Roman',
    default_font_size INTEGER DEFAULT 14,
    default_indent_left REAL DEFAULT 0,
    default_indent_first_line REAL DEFAULT 0,
    default_line_spacing REAL DEFAULT 1.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL REFERENCES users(id),
    template_id INTEGER REFERENCES templates(id),
    title VARCHAR(100) NOT NULL,
    xml_path VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    session_token VARCHAR(128) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL
);
