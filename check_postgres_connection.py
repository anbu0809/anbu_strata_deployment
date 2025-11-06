#!/usr/bin/env python3

"""
Check saved PostgreSQL connection and test connectivity
"""

import sqlite3
import json
import psycopg2

def check_saved_connections():
    """Check all saved connections in the database"""
    print("🔍 Checking saved connections in database...")
    
    conn = sqlite3.connect('strata.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id, name, db_type, credentials FROM connections')
        rows = cursor.fetchall()
        
        if not rows:
            print("❌ No connections found in database")
            return None
            
        print(f"✅ Found {len(rows)} saved connections:")
        print()
        
        for row in rows:
            try:
                credentials = json.loads(row[3])
                print(f"ID: {row[0]} | Name: {row[1]} | Type: {row[2]}")
                print(f"  Host: {credentials.get('host')}")
                print(f"  Port: {credentials.get('port', 'Not set')}")
                print(f"  Database: {credentials.get('database')}")
                print(f"  Username: {credentials.get('username')}")
                print(f"  SSL: {credentials.get('ssl', 'Not set')}")
                print()
                
                # If this is a PostgreSQL connection, test it
                if row[2] == 'PostgreSQL':
                    test_postgres_connection(credentials)
                    
            except Exception as e:
                print(f"❌ Error parsing credentials for {row[1]}: {e}")
                print()
                
    except Exception as e:
        print(f"❌ Error reading database: {e}")
    finally:
        conn.close()

def test_postgres_connection(credentials):
    """Test PostgreSQL connection with proper error handling"""
    print(f"🧪 Testing PostgreSQL connection to {credentials.get('host')}:{credentials.get('port', 5432)}...")
    
    try:
        # Extract connection details
        host = credentials.get('host')
        port = credentials.get('port', 5432)
        database = credentials.get('database')
        username = credentials.get('username')
        password = credentials.get('password')
        
        # Try to connect
        connection = psycopg2.connect(
            host=host,
            port=port,
            dbname=database,
            user=username,
            password=password,
            application_name='Strata Migration Tool'
        )
        
        # Test connection
        cursor = connection.cursor()
        cursor.execute('SELECT version()')
        version = cursor.fetchone()[0]
        
        print(f"✅ PostgreSQL connection successful!")
        print(f"   Database version: {version[:50]}...")
        
        # Test basic permissions
        cursor.execute('SELECT current_database(), current_user, inet_server_addr()')
        db_info = cursor.fetchone()
        print(f"   Current database: {db_info[0]}")
        print(f"   Connected as: {db_info[1]}")
        print(f"   Server address: {db_info[2]}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        print(f"   This explains why migration structure is failing!")

if __name__ == "__main__":
    print("🚀 PostgreSQL Connection Checker")
    print("=" * 50)
    check_saved_connections()
    print("=" * 50)
    print("💡 If connection fails:")
    print("   1. Check if Azure PostgreSQL allows your IP")
    print("   2. Verify port 5432 is open")
    print("   3. Check firewall rules")
    print("   4. Confirm credentials are correct")