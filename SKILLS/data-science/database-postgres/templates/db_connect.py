#!/usr/bin/env python3
"""PostgreSQL connection template for Hermes Agent."""

import psycopg2
from psycopg2 import sql, extras
import sys
import os

def get_connection():
    """Establish connection using environment variables or direct params."""
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "host.docker.internal"),
        port=int(os.getenv("DB_PORT", 6432)),
        dbname=os.getenv("DB_NAME", "bigdata"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )
    return conn

def safe_query(sql_text, params=None, limit=None):
    """Execute SELECT query safely and return rows as dicts."""
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)
        if limit:
            sql_text += f" LIMIT {limit}"
        cur.execute(sql_text, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        cur.close()
        conn.close()

def execute_write(sql_text, params=None):
    """Execute INSERT/UPDATE/DELETE with transaction safety."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql_text, params)
        conn.commit()
        return cur.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    # Quick verification
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT current_database(), current_user, version()")
    row = cur.fetchone()
    print(f"Database: {row[0]}")
    print(f"User: {row[1]}")
    print(f"Version: {row[2][:80]}...")
    cur.close()
    conn.close()
