import sqlite3

def fix_database():
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    
    # Check if transactions table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'")
    if cursor.fetchone():
        # Drop and recreate transactions table
        cursor.execute("DROP TABLE transactions")
        print("Dropped old transactions table")
    
    # Recreate transactions table with correct schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            description TEXT NOT NULL,
            date DATE NOT NULL,
            category_id INTEGER,
            type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
        )
    ''')
    print("Created new transactions table")
    
    conn.commit()
    conn.close()
    print("Database fixed successfully!")

if __name__ == "__main__":
    fix_database()