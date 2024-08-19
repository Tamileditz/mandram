# database_setup.py
import sqlite3

def create_db():
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    # Create user table
    cursor.execute('''
        CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    name TEXT NOT NULL,
    designation TEXT NOT NULL,
    permission TEXT NOT NULL
)
    ''')
    # Insert a sample user (username: admin, password: password)
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password, name, designation, permission)
        VALUES ('admin', 'admin123', 'Administrator', 'admin', 'full')
    ''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_db()
 