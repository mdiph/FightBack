# db/database.py

import sqlite3
import os

DB_PATH = 'data/fightback.db'

def setup_database():
    os.makedirs('data', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        discord_id TEXT UNIQUE,
        username TEXT,
        points INTEGER DEFAULT 0,
        rank TEXT DEFAULT 'Bronze'
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        winner_id TEXT,
        loser_id TEXT,
        winner_score INTEGER,
        loser_score INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        approved BOOLEAN DEFAULT 0,
        winner_points_gained INTEGER,
        loser_points_lost INTEGER
    )
    ''')

    conn.commit()
    conn.close()

    # Make sure rank column exists even if DB already created
    ensure_rank_column_exists()


def get_connection():
    return sqlite3.connect(DB_PATH, timeout=10)


# Helper function to execute queries safely
def execute_query(query, params=None):
    """Helper function to execute queries safely and ensure database connection is managed properly."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor
    except sqlite3.OperationalError as e:
        print(f"❌ Error executing query: {e}")
        conn.rollback()
    finally:
        conn.close()

# Function to reset the database (clear players and matches tables)
def reset_database():
    """Ensures the database has the correct structure and clears all data."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check if 'rank' column exists in 'players' table
        cursor.execute("PRAGMA table_info(players);")
        columns = [col[1] for col in cursor.fetchall()]  # Extract column names

        if "rank" not in columns:
            print("⚠️ 'rank' column is missing! Adding it now...")
            cursor.execute("ALTER TABLE players ADD COLUMN rank TEXT DEFAULT 'Bronze';")
            conn.commit()
            print("✅ 'rank' column added successfully!")

        # Clear match history
        cursor.execute("DELETE FROM matches")
        print("✅ Match history cleared!")

        # Reset player leaderboard: set points to 0 and rank to Bronze
        cursor.execute("UPDATE players SET points = 0, rank = 'Bronze'")
        print("✅ Player leaderboard reset: all players set to 0 points and Bronze rank.")

        conn.commit()
        print("✅ Database reset successfully!")

    except sqlite3.OperationalError as e:
        print(f"❌ Error in reset_database function: {e}")
    finally:
        conn.close()

def ensure_rank_column_exists():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(players)")
    columns = [col[1] for col in cursor.fetchall()]
    if "rank" not in columns:
        cursor.execute("ALTER TABLE players ADD COLUMN rank TEXT DEFAULT 'Bronze'")
        conn.commit()
    conn.close()
