"""
Database creation and initialization module.
Creates the 'Employees' database from scratch and all required tables.
"""
import os
import sys
import urllib.parse

import pyodbc
import sqlalchemy as sa
from flask import current_app

from app.extensions import db

# Ensure project root in path
_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)


def _get_raw_connection(database: str = 'master') -> pyodbc.Connection:
    """Get a raw pyodbc connection using encrypted credentials."""
    from config_manager import ConfigManager

    manager = ConfigManager(
        key_file=os.path.join(_root_dir, 'encryption_key.key'),
        config_file=os.path.join(_root_dir, 'db_config.enc')
    )
    config = manager.load_config()

    server = config.get('server', 'localhost')
    username = config.get('username', '')
    password = config.get('password', '')

    # Find available driver
    drivers = [
        'ODBC Driver 18 for SQL Server',
        'ODBC Driver 17 for SQL Server',
        'SQL Server',
    ]
    driver = None
    available_drivers = pyodbc.drivers()
    for d in drivers:
        if d in available_drivers:
            driver = d
            break

    if driver is None:
        raise RuntimeError("Nessun driver SQL Server trovato. Installare un ODBC driver.")

    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
        "Encrypt=yes;"
        "Connection Timeout=30;"
    )

    conn = pyodbc.connect(conn_str, autocommit=True)
    return conn


def check_database_exists(db_name: str = 'Employees') -> bool:
    """Check if the database exists on the SQL Server."""
    try:
        conn = _get_raw_connection('master')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sys.databases WHERE name = ?", db_name
        )
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        print(f"[Installer] Error checking database: {e}")
        return False


def create_database(db_name: str = 'Employees') -> None:
    """Create the database if it doesn't exist."""
    if check_database_exists(db_name):
        print(f"[Installer] Database '{db_name}' già esistente.")
        return

    try:
        conn = _get_raw_connection('master')
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE [{db_name}]")
        conn.close()
        print(f"[Installer] ✅ Database '{db_name}' creato con successo.")
    except Exception as e:
        print(f"[Installer] ❌ Errore nella creazione del database: {e}")
        raise


def create_schemas() -> None:
    """Create required schemas (app, Geo) in the Employees database."""
    schemas = ['app', 'Geo']
    with db.engine.connect() as conn:
        for schema in schemas:
            conn.execute(sa.text(f"""
                IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = '{schema}')
                BEGIN
                    EXEC('CREATE SCHEMA [{schema}]');
                END
            """))
            conn.commit()
            print(f"[Installer] ✅ Schema '{schema}' verificato/creato.")


def create_tables() -> None:
    """Create all tables from SQLAlchemy models."""
    # Import all models to register them
    import app.models  # noqa: F401

    db.create_all()
    print("[Installer] ✅ Tutte le tabelle create con successo.")


def init_db(seed: bool = True) -> None:
    """
    Full installation:
    1. Create database
    2. Create schemas
    3. Create tables
    4. Seed initial data
    """
    print("[Installer] === Inizio installazione ===")

    # Step 1: Create database
    create_database()

    # Step 2: Create schemas
    create_schemas()

    # Step 3: Create tables
    create_tables()

    # Step 4: Seed data
    if seed:
        from installer.seed_data import seed_database
        print("[Installer] Inserimento dati iniziali...")
        seed_database()
        print("[Installer] ✅ Dati iniziali inseriti.")

    print("[Installer] === Installazione completata ===")
