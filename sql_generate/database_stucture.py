export_schema = """
\d wine_aisummaries
                                       Table "public.wine_aisummaries"
   Column   |           Type           | Collation | Nullable |                   Default                    
------------+--------------------------+-----------+----------+----------------------------------------------
 id         | integer                  |           | not null | nextval('wine_aisummaries_id_seq'::regclass)
 wine_id    | integer                  |           | not null | 
 summary    | text                     |           | not null | 
 created_at | timestamp with time zone |           |          | CURRENT_TIMESTAMP
Indexes:
    "wine_aisummaries_pkey" PRIMARY KEY, btree (id)
    "wine_aisummaries_wine_id_key" UNIQUE CONSTRAINT, btree (wine_id)
Foreign-key constraints:
    "wine_aisummaries_wine_id_fkey" FOREIGN KEY (wine_id) REFERENCES wine_table(id) ON DELETE CASCADE

\d wine_contact
                                 Table "public.wine_contact"
   Column   |           Type           | Collation | Nullable |           Default            
------------+--------------------------+-----------+----------+------------------------------
 id         | bigint                   |           | not null | generated always as identity
 user_id    | bigint                   |           |          | 
 first_name | text                     |           |          | 
 last_name  | text                     |           |          | 
 email      | text                     |           |          | 
 subject    | text                     |           |          | 
 message    | text                     |           |          | 
 timestamp  | timestamp with time zone |           |          | CURRENT_TIMESTAMP
Indexes:
    "wine_contact_pkey" PRIMARY KEY, btree (id)
Foreign-key constraints:
    "wine_contact_user_id_fkey" FOREIGN KEY (user_id) REFERENCES wine_users(id)

\d wine_notes;
                         Table "public.wine_notes"
  Column   |  Type   | Collation | Nullable |           Default            
-----------+---------+-----------+----------+------------------------------
 id        | integer |           | not null | generated always as identity
 note_text | text    |           | not null | 
 wine_id   | integer |           | not null | 
Indexes:
    "wine_notes_pkey" PRIMARY KEY, btree (id)
    "wine_notes_wine_id_key" UNIQUE CONSTRAINT, btree (wine_id)
Foreign-key constraints:
    "wine_notes_wine_id_fkey" FOREIGN KEY (wine_id) REFERENCES wine_table(id) ON DELETE CASCADE

\d wine_table
                                      Table "public.wine_table"
   Column    |          Type          | Collation | Nullable |                Default                 
-------------+------------------------+-----------+----------+----------------------------------------
 id          | integer                |           | not null | nextval('wine_table_id_seq'::regclass)
 name        | character varying(255) |           | not null | 
 producer    | character varying(255) |           |          | 
 grapes      | character varying(255) |           |          | 
 country     | character varying(100) |           |          | 
 region      | character varying(100) |           |          | 
 year        | integer                |           |          | 
 price       | numeric(10,2)          |           |          | 
 quantity    | integer                |           | not null | 0
 user_id     | integer                |           |          | 
 bottle_size | numeric(5,3)           |           |          | 
Indexes:
    "wine_table_pkey" PRIMARY KEY, btree (id)
    "idx_wine_table_user_id" btree (user_id)
Foreign-key constraints:
    "fk_user" FOREIGN KEY (user_id) REFERENCES wine_users(id) ON DELETE CASCADE
Referenced by:
    TABLE "wine_aisummaries" CONSTRAINT "wine_aisummaries_wine_id_fkey" FOREIGN KEY (wine_id) REFERENCES wine_table(id) ON DELETE CASCADE
    TABLE "wine_notes" CONSTRAINT "wine_notes_wine_id_fkey" FOREIGN KEY (wine_id) REFERENCES wine_table(id) ON DELETE CASCADE

\d wine_users
                                         Table "public.wine_users"
     Column     |           Type           | Collation | Nullable |                Default                 
----------------+--------------------------+-----------+----------+----------------------------------------
 id             | integer                  |           | not null | nextval('wine_users_id_seq'::regclass)
 username       | character varying(50)    |           | not null | 
 email          | character varying(100)   |           | not null | 
 password_hash  | character varying(255)   |           | not null | 
 created_at     | timestamp with time zone |           |          | CURRENT_TIMESTAMP
 has_proaccount | boolean                  |           |          | false
Indexes:
    "wine_users_pkey" PRIMARY KEY, btree (id)
    "wine_users_email_key" UNIQUE CONSTRAINT, btree (email)
    "wine_users_username_key" UNIQUE CONSTRAINT, btree (username)
Referenced by:
    TABLE "wine_table" CONSTRAINT "fk_user" FOREIGN KEY (user_id) REFERENCES wine_users(id) ON DELETE CASCADE
    TABLE "password_reset_tokens" CONSTRAINT "password_reset_tokens_user_id_fkey" FOREIGN KEY (user_id) REFERENCES wine_users(id)
    TABLE "wine_contact" CONSTRAINT "wine_contact_user_id_fkey" FOREIGN KEY (user_id) REFERENCES wine_users(id)
"""