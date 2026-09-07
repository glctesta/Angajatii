import sys
import os
import pyodbc

# Ensure we can import from the root config_manager
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))

def get_raw_connection(database=None):
    """
    Returns a raw pyodbc connection using the configuration from config_manager.py.
    If database is provided, it connects to that specific database.
    """
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
        
    try:
        from config_manager import ConfigManager
        
        manager = ConfigManager(base_dir=root_dir)
        db_config = manager.get_db_config()
        
        if not db_config:
            return None
            
        server = db_config.get('server', '')
        username = db_config.get('username', '')
        password = db_config.get('password', '')
        driver = db_config.get('driver', 'ODBC Driver 17 for SQL Server')
        
        # Build connection string
        conn_str = f"DRIVER={{{driver}}};SERVER={server};"
        
        if database:
            conn_str += f"DATABASE={database};"
            
        if username and password:
            conn_str += f"UID={username};PWD={password};"
        else:
            conn_str += "Trusted_Connection=yes;"
            
        # Add timeout to fail fast if server is unreachable
        return pyodbc.connect(conn_str, timeout=10)
        
    except Exception as e:
        print(f"Error getting raw connection: {e}")
        return None

def check_database_exists(db_name='Employees'):
    """Checks if a specific database exists on the server."""
    conn = None
    try:
        # Connect to master database
        conn = get_raw_connection(database='master')
        if not conn:
            return False
            
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sys.databases WHERE name = ?", db_name)
        row = cursor.fetchone()
        
        return row is not None
        
    except Exception as e:
        print(f"Error checking if database exists: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

def execute_raw_sql(sql, params=None, database='master', fetch=False):
    """Executes a raw SQL statement, typically for administrative tasks."""
    conn = None
    try:
        conn = get_raw_connection(database=database)
        if not conn:
            return False, "Failed to connect to database server."
            
        # We need autocommit on for commands like CREATE DATABASE
        conn.autocommit = True
        cursor = conn.cursor()
        
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
            
        if fetch:
            rows = cursor.fetchall()
            return True, rows
            
        return True, "Success"
        
    except Exception as e:
        return False, str(e)
        
    finally:
        if conn:
            conn.close()
