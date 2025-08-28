"""
Create test admin account
"""

from sqlalchemy import create_engine, text
import hashlib

# Simple SQLite database
DATABASE_URL = "sqlite:///./cert_fast_test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def simple_hash(password: str) -> str:
    """Simple hash for testing (not for production)"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_tables_and_admin():
    # Create tables with simple SQL
    with engine.connect() as conn:
        # Create users table
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(255) UNIQUE NOT NULL,
                username VARCHAR(100) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                full_name VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'student',
                is_active BOOLEAN DEFAULT 1,
                is_verified BOOLEAN DEFAULT 0,
                avatar_url VARCHAR(500),
                bio TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """
        conn.execute(text(create_table_sql))
        
        # Check if admin already exists
        result = conn.execute(text("SELECT COUNT(*) FROM users WHERE username = 'admin'")).fetchone()
        
        if result[0] == 0:
            # Create admin user
            hashed_password = simple_hash("admin123!")
            insert_sql = """
                INSERT INTO users (email, username, hashed_password, full_name, role, is_active, is_verified)
                VALUES (:email, :username, :password, :full_name, :role, :is_active, :is_verified)
            """
            conn.execute(text(insert_sql), {
                "email": "admin@certfast.com",
                "username": "admin", 
                "password": hashed_password,
                "full_name": "System Admin",
                "role": "admin",
                "is_active": True,
                "is_verified": True
            })
            conn.commit()
            print("Admin account created successfully!")
            print("Email: admin@certfast.com")
            print("Username: admin")
            print("Password: admin123!")
        else:
            print("Admin account already exists.")
            print("Email: admin@certfast.com")
            print("Username: admin")
            print("Password: admin123!")

if __name__ == "__main__":
    create_tables_and_admin()