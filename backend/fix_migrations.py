"""
fix_migrations.py
-----------------
Run this once to fix the InconsistentMigrationHistory error.
It will:
  1. Drop ALL tables in the database (including django_migrations).
  2. Re-run all migrations from scratch.
Usage:
    python fix_migrations.py
"""
import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import connection

print("==> Dropping all tables in the database...")
try:
    with connection.cursor() as cursor:
        # Get all table names
        cursor.execute("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public';
        """)
        tables = [row[0] for row in cursor.fetchall()]

        if not tables:
            print("    No tables found. Database is already clean.")
        else:
            # Drop all tables at once using CASCADE
            tables_str = ", ".join(f'"{t}"' for t in tables)
            cursor.execute(f"DROP TABLE IF EXISTS {tables_str} CASCADE;")
            print(f"    Dropped tables: {', '.join(tables)}")

    print("\n==> All tables dropped successfully.")
    print("==> Now run:  python manage.py migrate")

except Exception as e:
    print(f"\n[ERROR] {e}")
    sys.exit(1)
