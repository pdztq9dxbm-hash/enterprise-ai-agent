import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

def setup_database():
    """Setup PostgreSQL database and tables"""
    
    # Connect to PostgreSQL
    try:
        conn = psycopg2.connect(
            host="localhost",
            user="postgres",
            password="postgres",  
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create database
        print("Creating database...")
        cursor.execute("DROP DATABASE IF EXISTS ai_agent_db")
        cursor.execute("CREATE DATABASE ai_agent_db")
        print("✓ Database created")
        
        cursor.close()
        conn.close()
        
        # Connect to new database
        conn = psycopg2.connect(
            host="localhost",
            user="postgres",
            password="postgres",
            database="ai_agent_db"
        )
        cursor = conn.cursor()
        
        # Create users table
        print("Creating tables...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)
        
        # Create query logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_logs (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL,
                session_id VARCHAR(255) NOT NULL,
                query TEXT NOT NULL,
                response TEXT,
                intent VARCHAR(100),
                success BOOLEAN,
                execution_time FLOAT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Create permissions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS permissions (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL,
                permission VARCHAR(100) NOT NULL,
                resource VARCHAR(255),
                granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Create documents table (for unstructured data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                doc_id VARCHAR(100) UNIQUE NOT NULL,
                title VARCHAR(255),
                content TEXT,
                metadata JSONB,
                created_by VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert demo user
        print("Inserting demo data...")
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        demo_password = pwd_context.hash("demo123")
        
        cursor.execute("""
            INSERT INTO users (user_id, name, email, password_hash, role)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
        """, ("user_001", "Demo User", "demo@example.com", demo_password, "user"))
        
        # Insert demo permissions
        cursor.execute("""
            INSERT INTO permissions (user_id, permission, resource)
            VALUES 
                ('user_001', 'read', '*'),
                ('user_001', 'write', '*')
            ON CONFLICT DO NOTHING
        """)
        
        # Insert sample documents
        cursor.execute("""
            INSERT INTO documents (doc_id, title, content, metadata)
            VALUES 
                ('doc_001', 'Company Handbook', 'This is the company handbook...', '{"category": "HR", "public": true}'),
                ('doc_002', 'Q3 Report', 'Q3 financial report...', '{"category": "Finance", "quarter": "Q3"}')
            ON CONFLICT (doc_id) DO NOTHING
        """)
        
        conn.commit()
        print("✓ Tables created and demo data inserted")
        
        cursor.close()
        conn.close()
        
        print("\n✓ Database setup complete!")
        print("\nDemo credentials:")
        print("Email: demo@example.com")
        print("Password: demo123")
        
    except Exception as e:
        print(f"Error setting up database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_database()