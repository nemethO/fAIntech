# fAIntech Database Schema

## Overview
SQLite (dev) / PostgreSQL (prod) relational database with 7 tables.

---

## Tables

### users
| Column        | Type         | Constraints       |
|---------------|--------------|-------------------|
| id            | INTEGER      | PK, AUTO          |
| name          | VARCHAR(100) | NOT NULL           |
| email         | VARCHAR(120) | NOT NULL, UNIQUE   |
| password_hash | VARCHAR(128) | NOT NULL (bcrypt)  |
| created_at    | DATETIME     | DEFAULT now()      |
| updated_at    | DATETIME     | DEFAULT now()      |

### accounts
| Column       | Type        | Constraints              |
|--------------|-------------|--------------------------|
| id           | INTEGER     | PK, AUTO                 |
| user_id      | INTEGER     | FK → users.id, NOT NULL  |
| bank_name    | VARCHAR(50) | NOT NULL (OTP/Revolut/Erste) |
| account_name | VARCHAR(100)| Display name             |
| currency     | VARCHAR(3)  | DEFAULT 'HUF'            |
| created_at   | DATETIME    | DEFAULT now()            |

### categories
| Column     | Type        | Constraints                    |
|------------|-------------|--------------------------------|
| id         | INTEGER     | PK, AUTO                       |
| user_id    | INTEGER     | FK → users.id, NULLABLE (NULL = system default) |
| name       | VARCHAR(50) | NOT NULL                       |
| icon       | VARCHAR(10) | Emoji                          |
| color      | VARCHAR(7)  | Hex color (#FF6B6B)            |
| is_default | BOOLEAN     | DEFAULT false                  |

**Default categories (seeded):**
| Name            | Icon | Color   |
|-----------------|------|---------|
| Elelmiszer      | 🛒   | #22c55e |
| Etterem         | 🍽️   | #f97316 |
| Kozlekedes      | 🚗   | #3b82f6 |
| Szorakozas      | 🎬   | #a78bfa |
| Vasarlas        | 🛍️   | #ec4899 |
| Kozuzemi dijak  | ⚡   | #06b6d4 |
| Lakhatas        | 🏠   | #eab308 |
| Egeszseg        | 🏥   | #ef4444 |
| Egyeb           | 🔮   | #6b7280 |

### transactions
| Column                  | Type         | Constraints                   |
|-------------------------|--------------|-------------------------------|
| id                      | INTEGER      | PK, AUTO                      |
| user_id                 | INTEGER      | FK → users.id, NOT NULL       |
| account_id              | INTEGER      | FK → accounts.id, NOT NULL    |
| import_id               | INTEGER      | FK → imports.id, NULLABLE     |
| category_id             | INTEGER      | FK → categories.id, NULLABLE  |
| date                    | DATE         | NOT NULL                      |
| amount                  | FLOAT        | NOT NULL                      |
| currency                | VARCHAR(3)   | DEFAULT 'HUF'                 |
| partner                 | VARCHAR(200) | Payee/merchant name            |
| description             | TEXT         | Kozlemeny/memo                 |
| transaction_hash        | VARCHAR(64)  | UNIQUE (SHA-256 for dedup)     |
| is_income               | BOOLEAN      | DEFAULT false                  |
| ai_category_confidence  | FLOAT        | NULLABLE (0.0-1.0)            |
| manually_categorized    | BOOLEAN      | DEFAULT false                  |
| created_at              | DATETIME     | DEFAULT now()                  |

### budgets
| Column        | Type        | Constraints                                       |
|---------------|-------------|---------------------------------------------------|
| id            | INTEGER     | PK, AUTO                                          |
| user_id       | INTEGER     | FK → users.id, NOT NULL                           |
| category_id   | INTEGER     | FK → categories.id, NOT NULL                      |
| monthly_limit | FLOAT       | NOT NULL                                          |
| year_month    | VARCHAR(7)  | NOT NULL (YYYY-MM)                                |
| created_at    | DATETIME    | DEFAULT now()                                     |
| **UNIQUE**    |             | (user_id, category_id, year_month)                |

### imports
| Column            | Type         | Constraints                   |
|-------------------|--------------|-------------------------------|
| id                | INTEGER      | PK, AUTO                      |
| user_id           | INTEGER      | FK → users.id, NOT NULL       |
| account_id        | INTEGER      | FK → accounts.id, NOT NULL    |
| filename          | VARCHAR(255) | NOT NULL                      |
| file_type         | VARCHAR(10)  | NOT NULL (CSV/PDF)            |
| bank_type         | VARCHAR(50)  | NOT NULL (OTP/Revolut/Erste)  |
| status            | VARCHAR(20)  | DEFAULT 'pending'             |
| records_total     | INTEGER      | DEFAULT 0                     |
| records_imported  | INTEGER      | DEFAULT 0                     |
| records_duplicate | INTEGER      | DEFAULT 0                     |
| created_at        | DATETIME     | DEFAULT now()                 |

### chat_messages
| Column       | Type        | Constraints                  |
|--------------|-------------|------------------------------|
| id           | INTEGER     | PK, AUTO                     |
| user_id      | INTEGER     | FK → users.id, NOT NULL      |
| role         | VARCHAR(20) | NOT NULL (user/assistant)    |
| content      | TEXT        | NOT NULL                     |
| context_data | JSON        | NULLABLE (RAG context used)  |
| created_at   | DATETIME    | DEFAULT now()                |

---

## Relationships
```
users 1──N accounts
users 1──N transactions
users 1──N categories
users 1──N budgets
users 1──N imports
users 1──N chat_messages

accounts 1──N transactions
accounts 1──N imports

categories 1──N transactions
categories 1──N budgets

imports 1──N transactions
```

## Indexes (to add for performance)
- `transactions.user_id + transactions.date` (dashboard queries)
- `transactions.transaction_hash` (dedup lookups)
- `transactions.user_id + transactions.category_id` (analytics)
- `budgets.user_id + budgets.year_month` (budget page)
