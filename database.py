import sqlite3
from datetime import datetime, date
from contextlib import contextmanager
import json
from functools import lru_cache
from collections import defaultdict

class Database:
    def __init__(self, db_path="finance.db"):
        self.db_path = db_path
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA cache_size = 10000")  # Increase cache
        conn.execute("PRAGMA temp_store = MEMORY")  # Use memory for temp
        conn.execute("PRAGMA synchronous = NORMAL")  # Faster writes
        conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
        try:
            yield conn
        finally:
            conn.close()
    
    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Categories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                    color TEXT DEFAULT '#3b82f6',
                    icon TEXT DEFAULT '📌'
                )
            ''')
            
            # Transactions table with indexes for fast queries
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
            
            # Create indexes for lightning-fast queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date_type ON transactions(date, type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_categories_type ON categories(type)")
            
            # Budget settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER,
                    monthly_limit REAL NOT NULL,
                    month INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
                    UNIQUE(category_id, month, year)
                )
            ''')
            
            # User preferences table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            ''')
            
            # Insert default categories if none exist
            cursor.execute("SELECT COUNT(*) as count FROM categories")
            if cursor.fetchone()['count'] == 0:
                default_categories = [
                    ('Salary', 'income', '#10b981', '💵'),
                    ('Freelance', 'income', '#10b981', '💻'),
                    ('Investment', 'income', '#10b981', '📈'),
                    ('Food', 'expense', '#ef4444', '🍔'),
                    ('Transport', 'expense', '#3b82f6', '🚗'),
                    ('Shopping', 'expense', '#8b5cf6', '🛍️'),
                    ('Entertainment', 'expense', '#f59e0b', '🎬'),
                    ('Bills', 'expense', '#06b6d4', '💡'),
                    ('Healthcare', 'expense', '#ec4899', '🏥'),
                    ('Education', 'expense', '#14b8a6', '📚')
                ]
                cursor.executemany(
                    "INSERT INTO categories (name, type, color, icon) VALUES (?, ?, ?, ?)",
                    default_categories
                )
            
            conn.commit()
    
    # CREATE - Fast insert with batch support
    def add_transaction(self, amount, description, date_str, category_id, trans_type):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions (amount, description, date, category_id, type)
                VALUES (?, ?, ?, ?, ?)
            ''', (abs(amount), description, date_str, category_id, trans_type))
            conn.commit()
            self._clear_cache()  # Clear cache on data change
            return cursor.lastrowid
    
    # READ - Optimized with caching
    @lru_cache(maxsize=128)
    def _get_cached_transactions(self, params_hash):
        """Internal cached method for transactions"""
        return None  # Placeholder for actual cache implementation
    
    def get_transactions(self, trans_id=None, start_date=None, end_date=None, trans_type=None, limit=100):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Optimized query with limited columns
            if trans_id:
                query = '''
                    SELECT t.id, t.amount, t.description, t.date, t.type, 
                           c.name as category_name, c.color, c.icon
                    FROM transactions t
                    LEFT JOIN categories c ON t.category_id = c.id
                    WHERE t.id = ?
                    LIMIT 1
                '''
                cursor.execute(query, (trans_id,))
                return dict(cursor.fetchone()) if cursor.fetchone() else None
            
            query = '''
                SELECT t.id, t.amount, t.description, t.date, t.type, 
                       c.name as category_name, c.color, c.icon
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE 1=1
            '''
            params = []
            
            if start_date:
                query += " AND t.date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND t.date <= ?"
                params.append(end_date)
            if trans_type:
                query += " AND t.type = ?"
                params.append(trans_type)
            
            query += f" ORDER BY t.date DESC LIMIT {limit}"
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    # UPDATE
    def update_transaction(self, trans_id, amount=None, description=None, date=None, category_id=None, trans_type=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []
            
            if amount is not None:
                updates.append("amount = ?")
                params.append(abs(amount))
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            if date is not None:
                updates.append("date = ?")
                params.append(date)
            if category_id is not None:
                updates.append("category_id = ?")
                params.append(category_id)
            if trans_type is not None:
                updates.append("type = ?")
                params.append(trans_type)
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            
            if updates:
                query = f"UPDATE transactions SET {', '.join(updates)} WHERE id = ?"
                params.append(trans_id)
                cursor.execute(query, params)
                conn.commit()
                self._clear_cache()
                return cursor.rowcount
            return 0
    
    # DELETE - Fast deletion
    def delete_transaction(self, trans_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ?", (trans_id,))
            conn.commit()
            self._clear_cache()
            return cursor.rowcount
    
    # CATEGORY CRUD with caching
    @lru_cache(maxsize=32)
    def get_categories(self, category_id=None, type_filter=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if category_id:
                cursor.execute("SELECT * FROM categories WHERE id = ? LIMIT 1", (category_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
            elif type_filter:
                cursor.execute("SELECT * FROM categories WHERE type = ? ORDER BY name", (type_filter,))
            else:
                cursor.execute("SELECT * FROM categories ORDER BY type, name")
            return [dict(row) for row in cursor.fetchall()]
    
    def add_category(self, name, type_val, color, icon):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO categories (name, type, color, icon) VALUES (?, ?, ?, ?)",
                (name, type_val, color, icon)
            )
            conn.commit()
            self.get_categories.cache_clear()  # Clear cache
            return cursor.lastrowid
    
    def update_category(self, category_id, name=None, type_val=None, color=None, icon=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if type_val is not None:
                updates.append("type = ?")
                params.append(type_val)
            if color is not None:
                updates.append("color = ?")
                params.append(color)
            if icon is not None:
                updates.append("icon = ?")
                params.append(icon)
            
            if updates:
                query = f"UPDATE categories SET {', '.join(updates)} WHERE id = ?"
                params.append(category_id)
                cursor.execute(query, params)
                conn.commit()
                self.get_categories.cache_clear()
                return cursor.rowcount
            return 0
    
    def delete_category(self, category_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM transactions WHERE category_id = ?", (category_id,))
            if cursor.fetchone()['count'] > 0:
                cursor.execute("UPDATE transactions SET category_id = NULL WHERE category_id = ?", (category_id,))
            cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            conn.commit()
            self.get_categories.cache_clear()
            return cursor.rowcount
    
    # Optimized financial summaries
    def get_monthly_summary(self, year, month):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year+1}-01-01"
            else:
                end_date = f"{year}-{month+1:02d}-01"
            
            cursor.execute('''
                SELECT 
                    type,
                    COALESCE(SUM(amount), 0) as total
                FROM transactions
                WHERE date >= ? AND date < ?
                GROUP BY type
            ''', (start_date, end_date))
            
            result = {row['type']: row['total'] for row in cursor.fetchall()}
            return {
                'income': result.get('income', 0),
                'expense': result.get('expense', 0)
            }
    
    def get_category_breakdown(self, year, month):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year+1}-01-01"
            else:
                end_date = f"{year}-{month+1:02d}-01"
            
            cursor.execute('''
                SELECT 
                    c.id,
                    c.name,
                    c.color,
                    c.icon,
                    COALESCE(SUM(t.amount), 0) as total
                FROM categories c
                LEFT JOIN transactions t ON t.category_id = c.id 
                    AND t.date >= ? AND t.date < ? AND t.type = 'expense'
                WHERE c.type = 'expense'
                GROUP BY c.id
                ORDER BY total DESC
                LIMIT 10
            ''', (start_date, end_date))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def set_budget(self, category_id, monthly_limit, month, year):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO budgets (category_id, monthly_limit, month, year)
                VALUES (?, ?, ?, ?)
            ''', (category_id, monthly_limit, month, year))
            conn.commit()
    
    def get_budgets(self, month, year):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT b.*, c.name, c.color, c.icon
                FROM budgets b
                JOIN categories c ON b.category_id = c.id
                WHERE b.month = ? AND b.year = ?
            ''', (month, year))
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_budget(self, budget_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
            conn.commit()
            return cursor.rowcount
    
    def get_setting(self, key, default=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ? LIMIT 1", (key,))
            row = cursor.fetchone()
            if row:
                return json.loads(row['value'])
            return default
    
    def set_setting(self, key, value):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, json.dumps(value))
            )
            conn.commit()
    
    def export_all_transactions(self):
        return self.get_transactions(limit=10000)
    
    def delete_all_transactions(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions")
            conn.commit()
            self._clear_cache()
            return cursor.rowcount
    
    def _clear_cache(self):
        """Clear all cached data"""
        self.get_categories.cache_clear()
        if hasattr(self, '_get_cached_transactions'):
            self._get_cached_transactions.cache_clear()