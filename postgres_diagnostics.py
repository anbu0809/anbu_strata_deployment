#!/usr/bin/env python3

"""
PostgreSQL Migration Connection Diagnostics Tool
Helps troubleshoot PostgreSQL connection issues during migration
"""

import sqlite3
import json
import psycopg2
import socket
import time
from urllib.parse import urlparse

def diagnose_postgresql_connection():
    """Run comprehensive diagnostics on PostgreSQL connection"""
    
    print("=== PostgreSQL Migration Connection Diagnostics ===")
    print()
    
    # 1. Check saved connections
    print("1. Checking saved PostgreSQL connections...")
    postgres_connections = get_postgres_connections()
    
    if not postgres_connections:
        print("❌ No PostgreSQL connections found in database")
        return
    
    print(f"✅ Found {len(postgres_connections)} PostgreSQL connections")
    print()
    
    for conn_info in postgres_connections:
        print(f"Connection ID: {conn_info['id']} | Name: {conn_info['name']}")
        print("-" * 50)
        
        # 2. Network connectivity test
        print("2. Network Connectivity Tests:")
        test_network_connectivity(conn_info)
        
        # 3. Database connection test
        print("3. Database Connection Test:")
        test_database_connection(conn_info)
        
        # 4. SSL and Azure-specific tests
        print("4. SSL and Azure-Specific Tests:")
        test_ssl_and_azure_settings(conn_info)
        
        print()
        print("=" * 60)
        print()

def get_postgres_connections():
    """Get all PostgreSQL connections from database"""
    conn = sqlite3.connect('strata.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id, name, db_type, credentials FROM connections WHERE db_type = "PostgreSQL"')
        rows = cursor.fetchall()
        
        connections = []
        for row in rows:
            try:
                credentials = json.loads(row[3])
                connections.append({
                    'id': row[0],
                    'name': row[1],
                    'credentials': credentials
                })
            except Exception as e:
                print(f"❌ Error parsing credentials for {row[1]}: {e}")
        
        return connections
    except Exception as e:
        print(f"❌ Error reading database: {e}")
        return []
    finally:
        conn.close()

def test_network_connectivity(conn_info):
    """Test basic network connectivity"""
    creds = conn_info['credentials']
    host = creds.get('host')
    port = creds.get('port', 5432)
    
    print(f"   Testing connection to {host}:{port}...")
    
    try:
        # Test if host resolves
        print(f"   - DNS resolution: ", end="")
        ip_address = socket.gethostbyname(host)
        print(f"✅ {host} resolves to {ip_address}")
        
        # Test if port is reachable
        print(f"   - Port connectivity: ", end="")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5 second timeout
        
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Port {port} is reachable")
        else:
            print(f"❌ Port {port} is NOT reachable (Error: {result})")
            print(f"   This suggests:")
            print(f"   - Firewall blocking port {port}")
            print(f"   - Server not listening on port {port}")
            print(f"   - Network connectivity issues")
            
    except socket.gaierror:
        print(f"❌ DNS resolution failed for {host}")
        print(f"   This suggests:")
        print(f"   - Incorrect hostname")
        print(f"   - DNS issues")
        print(f"   - Firewall blocking DNS")
        
    except Exception as e:
        print(f"❌ Network test failed: {e}")

def test_database_connection(conn_info):
    """Test actual database connection"""
    creds = conn_info['credentials']
    host = creds.get('host')
    port = creds.get('port', 5432)
    database = creds.get('database')
    username = creds.get('username')
    password = creds.get('password')
    ssl_mode = creds.get('ssl', 'require')
    
    print(f"   Attempting connection to PostgreSQL...")
    
    try:
        # Test without SSL first
        print(f"   - Testing connection (SSL disabled): ", end="")
        try:
            connection = psycopg2.connect(
                host=host,
                port=port,
                dbname=database,
                user=username,
                password=password,
                sslmode='disable',
                connect_timeout=5
            )
            
            cursor = connection.cursor()
            cursor.execute('SELECT version()')
            version = cursor.fetchone()[0]
            print(f"✅ SUCCESS")
            print(f"   Database version: {version[:50]}...")
            
            cursor.execute('SELECT current_user, current_database(), inet_server_addr()')
            user_info = cursor.fetchone()
            print(f"   Connected as: {user_info[0]} to database: {user_info[1]}")
            print(f"   Server address: {user_info[2]}")
            
            connection.close()
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
        
        # Test with SSL
        print(f"   - Testing connection (SSL {ssl_mode}): ", end="")
        try:
            connection = psycopg2.connect(
                host=host,
                port=port,
                dbname=database,
                user=username,
                password=password,
                sslmode=ssl_mode,
                connect_timeout=5
            )
            
            cursor = connection.cursor()
            cursor.execute('SELECT version()')
            version = cursor.fetchone()[0]
            print(f"✅ SUCCESS")
            print(f"   Database version: {version[:50]}...")
            
            connection.close()
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
            
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")

def test_ssl_and_azure_settings(conn_info):
    """Test SSL and Azure-specific settings"""
    creds = conn_info['credentials']
    host = creds.get('host')
    port = creds.get('port', 5432)
    ssl_mode = creds.get('ssl', 'require')
    
    print(f"   Current SSL mode: {ssl_mode}")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    
    # Check if this looks like Azure
    if 'postgres.database.azure.com' in host:
        print(f"   ✅ Detected Azure PostgreSQL endpoint")
        print(f"   Azure PostgreSQL typically uses:")
        print(f"   - Port: 5432 (not {port})")
        print(f"   - SSL: Required (most likely)")
        print(f"   - Firewall: Must allow your IP address")
        
        if port != 5432:
            print(f"   ⚠️  WARNING: Using port {port}, but Azure PostgreSQL typically uses port 5432")
            print(f"      Consider changing to port 5432")
            
    else:
        print(f"   ⚠️  This doesn't appear to be an Azure PostgreSQL endpoint")
    
    # Check firewall access suggestion
    print(f"   Azure Firewall Requirements:")
    print(f"   1. Add your IP address to Azure PostgreSQL firewall rules")
    print(f"   2. Ensure 'Allow access to Azure services' is enabled")
    print(f"   3. Use the correct server name (should end with .postgres.database.azure.com)")

if __name__ == "__main__":
    diagnose_postgresql_connection()
    
    print("""
RECOMMENDATIONS TO FIX THE CONNECTION:

1. **Check Azure PostgreSQL Settings:**
   - Go to Azure Portal → Your PostgreSQL Server → Firewall rules
   - Add your current IP address to firewall rules
   - Enable "Allow access to Azure services"

2. **Verify Server Configuration:**
   - Server name should end with: .postgres.database.azure.com
   - Port should be: 5432 (standard)
   - SSL should be: Required (enabled)

3. **Update Connection in Strata:**
   - Delete and re-create the PostgreSQL connection with correct settings
   - Use these settings:
     * Host: your-server.postgres.database.azure.com
     * Port: 5432
     * Database: your-database-name
     * Username: your-username
     * Password: your-password
     * SSL: True/Require

4. **Test Network:**
   - Make sure you can ping the server from your network
   - Check if port 5432 is accessible

After making these changes, try the migration again!
""")