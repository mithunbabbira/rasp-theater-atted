import sqlite3
from typing import Optional, Tuple
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name: str = "fingerprint.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self) -> None:
        """Initialize the database with required tables and add new columns if needed"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                position INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check if last_present_date column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add last_present_date column if it doesn't exist
        if 'last_present_date' not in columns:
            cursor.execute('''
                ALTER TABLE users
                ADD COLUMN last_present_date TEXT
            ''')
            print("Added last_present_date column to users table")
        
        conn.commit()
        conn.close()

    def add_user(self, position: int, name: str, phone: str) -> bool:
        """Add a new user to the database"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (position, name, phone)
                VALUES (?, ?, ?)
            ''', (position, name, phone))
            
            conn.commit()
            conn.close()
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
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            current_date = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                UPDATE users 
                SET last_present_date = ? 
                WHERE position = ?
            ''', (current_date, position))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating last present date: {e}")
            return False

    def get_user(self, position: int) -> Optional[Tuple[str, str]]:
        """Get user details by position"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT name, phone FROM users WHERE position = ?', (position,))
        result = cursor.fetchone()
        
        conn.close()
        return result if result else None

    def delete_user(self, position: int) -> bool:
        """Delete a user from the database"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM users WHERE position = ?', (position,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False

    def get_absent_users(self) -> list[tuple[int, str]]:
        """Get list of users who haven't marked attendance today"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            current_date = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT position, name 
                FROM users 
                WHERE last_present_date != ? OR last_present_date IS NULL
            ''', (current_date,))
            
            absent_users = cursor.fetchall()
            conn.close()
            return absent_users
            
        except Exception as e:
            print(f"Error getting absent users: {e}")
            return []
  