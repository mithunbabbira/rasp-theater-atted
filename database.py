import sqlite3
from typing import Optional, Tuple

class DatabaseManager:
    def __init__(self, db_name: str = "fingerprint.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self) -> None:
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                position INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
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