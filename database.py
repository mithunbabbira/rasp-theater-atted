import sqlite3
from typing import Optional, Tuple
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name: str = "fingerprint.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.init_db()

    def init_db(self) -> None:
        """Initialize the database with required tables and add new columns if needed"""
        # Create table if it doesn't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                position INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check if last_present_date column exists
        self.cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in self.cursor.fetchall()]
        
        # Add last_present_date column if it doesn't exist
        if 'last_present_date' not in columns:
            self.cursor.execute('''
                ALTER TABLE users
                ADD COLUMN last_present_date TEXT
            ''')
            print("Added last_present_date column to users table")
        
        self.conn.commit()

    def add_user(self, position: int, name: str, phone: str) -> bool:
        """Add a new user to the database"""
        try:
            self.cursor.execute('''
                INSERT INTO users (position, name, phone)
                VALUES (?, ?, ?)
            ''', (position, name, phone))
            
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            print(f"Position {position} already exists in database")
            return False
        except Exception as e:
            print(f"Error adding user: {e}")
            return False

    def update_last_present_date(self, position: int) -> bool:
        """Update the last present date for a user"""
        try:
            current_date = datetime.now().strftime('%Y-%m-%d')
            self.cursor.execute('''
                UPDATE users 
                SET last_present_date = ? 
                WHERE position = ?
            ''', (current_date, position))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating last present date: {e}")
            return False

    def get_user(self, position: int) -> Optional[Tuple[str, str]]:
        """Get user details by position"""
        self.cursor.execute('SELECT name, phone FROM users WHERE position = ?', (position,))
        result = self.cursor.fetchone()
        return result if result else None

    def delete_user(self, position: int) -> bool:
        """Delete a user from the database"""
        try:
            self.cursor.execute('DELETE FROM users WHERE position = ?', (position,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False

    def get_absent_users(self) -> list[tuple[int, str]]:
        """Get list of users who haven't marked attendance today"""
        try:
            current_date = datetime.now().strftime('%Y-%m-%d')
            self.cursor.execute('''
                SELECT position, name 
                FROM users 
                WHERE last_present_date != ? OR last_present_date IS NULL
            ''', (current_date,))
            
            return self.cursor.fetchall()
            
        except Exception as e:
            print(f"Error getting absent users: {e}")
            return []

    def get_random_user(self) -> Optional[Tuple[str, str]]:
        """Get a random user from the database"""
        try:
            self.cursor.execute("""
                SELECT name, phone 
                FROM users 
                ORDER BY RANDOM() 
                LIMIT 1
            """)
            return self.cursor.fetchone()
        except Exception as e:
            print(f"Error getting random user: {e}")
            return None

    def __del__(self):
        """Cleanup database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()
  