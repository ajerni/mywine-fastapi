# Database schema information for SQL generation
SCHEMA = {
    "wine_users": {
        "columns": {
            "id": "SERIAL PRIMARY KEY",
            "username": "VARCHAR(255) NOT NULL",
            "email": "VARCHAR(255) NOT NULL",
            "has_proaccount": "BOOLEAN DEFAULT FALSE",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        },
        "description": "Stores user account information"
    },
    "wine_table": {
        "columns": {
            "id": "SERIAL PRIMARY KEY",
            "user_id": "INTEGER REFERENCES wine_users(id)",
            "name": "VARCHAR(255) NOT NULL",
            "producer": "VARCHAR(255)",
            "vintage": "INTEGER",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        },
        "description": "Stores wine entries created by users"
    },
    "wine_notes": {
        "columns": {
            "id": "SERIAL PRIMARY KEY",
            "wine_id": "INTEGER REFERENCES wine_table(id)",
            "note_text": "TEXT",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        },
        "description": "Stores tasting notes for wines"
    },
    "wine_aisummaries": {
        "columns": {
            "id": "SERIAL PRIMARY KEY",
            "wine_id": "INTEGER REFERENCES wine_table(id)",
            "summary_text": "TEXT",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        },
        "description": "Stores AI-generated summaries for wines"
    },
    "wine_contact": {
        "columns": {
            "id": "SERIAL PRIMARY KEY",
            "name": "VARCHAR(255)",
            "email": "VARCHAR(255)",
            "message": "TEXT",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        },
        "description": "Stores contact form submissions"
    }
}

# Relationships between tables
RELATIONSHIPS = [
    {
        "from": "wine_users",
        "to": "wine_table",
        "type": "one-to-many",
        "via": "user_id"
    },
    {
        "from": "wine_table",
        "to": "wine_notes",
        "type": "one-to-many",
        "via": "wine_id"
    },
    {
        "from": "wine_table",
        "to": "wine_aisummaries",
        "type": "one-to-many",
        "via": "wine_id"
    }
] 