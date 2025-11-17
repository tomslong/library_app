"""
Simple script to view the contents of library.db database
"""
import sqlite3
from tabulate import tabulate


def view_database(db_path='instance/library.db'):
    """Display all data from the library database"""
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("LIBRARY DATABASE CONTENTS")
    print("=" * 80)
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        print(f"\n{'=' * 80}")
        print(f"TABLE: {table_name}")
        print('=' * 80)
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Get all data from table
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        if rows:
            # Print as formatted table
            try:
                print(tabulate(rows, headers=columns, tablefmt='grid'))
            except ImportError:
                # If tabulate not installed, print simple format
                print("Columns:", ", ".join(columns))
                for row in rows:
                    print(row)
        else:
            print("(Empty table)")
        
        print(f"\nTotal rows: {len(rows)}")
    
    conn.close()
    print("\n" + "=" * 80)


def query_database(query, db_path='instance/library.db'):
    """Execute a custom SQL query"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Get column names from cursor description
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            print("\nQuery Results:")
            print("=" * 80)
            try:
                print(tabulate(results, headers=columns, tablefmt='grid'))
            except ImportError:
                print("Columns:", ", ".join(columns))
                for row in results:
                    print(row)
            print(f"\nRows returned: {len(results)}")
        else:
            print("Query executed successfully")
            conn.commit()
    except sqlite3.Error as e:
        print(f"Error: {e}")
    finally:
        conn.close()


def show_schema(db_path='instance/library.db'):
    """Show the database schema (table structures)"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("DATABASE SCHEMA")
    print("=" * 80)
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        print(f"\nTable: {table_name}")
        print("-" * 80)
        
        # Get CREATE TABLE statement
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        create_statement = cursor.fetchone()[0]
        print(create_statement)
        print()
    
    conn.close()


if __name__ == "__main__":
    import sys
    
    print("\n🔍 LIBRARY DATABASE VIEWER")
    print("=" * 80)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "schema":
            show_schema()
        elif command == "query" and len(sys.argv) > 2:
            query = sys.argv[2]
            query_database(query)
        else:
            print("Usage:")
            print("  python view_db.py          - View all data")
            print("  python view_db.py schema   - View database schema")
            print('  python view_db.py query "SELECT * FROM user"  - Run custom query')
    else:
        view_database()
