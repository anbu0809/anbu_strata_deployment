from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from backend.models import AnalysisStatusResponse, CommonResponse
from backend.database import get_active_session, get_connection_by_id
import asyncio
import json
import os
import importlib
import xlsxwriter
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

router = APIRouter()

# Global variable to track analysis status (in production, use Redis or database)
analysis_status = {
    "phase": None,
    "percent": 0,
    "done": False,
    "results_summary": None,
    "error": None
}

def get_db_connector(db_type: str):
    """Dynamically import and return the appropriate database connector"""
    connectors = {
        "PostgreSQL": "psycopg2",
        "MySQL": "mysql.connector",
        "Snowflake": "snowflake.connector",
        "Databricks": "databricks.sql",
        "Oracle": "oracledb",
        "SQL Server": "pyodbc",
        "Teradata": "teradatasql",
        "Google BigQuery": "google.cloud.bigquery"
    }
    
    try:
        if db_type in connectors:
            return importlib.import_module(connectors[db_type])
        return None
    except ImportError:
        return None

def analyze_mysql_schema(connection_info):
    """Analyze MySQL database schema comprehensively"""
    print("[DEBUG] analyze_mysql_schema() function called - LIVE ROW COUNTING VERSION")
    try:
        # Use the same connection function as the working migration
        from backend.routes.migrate import connect_to_database
        
        # Get connection using the working function
        connection = connect_to_database(connection_info)
        cursor = connection.cursor()
        
        # DEBUG: Log the database name being used
        credentials = connection_info.get("credentials", {})
        database = credentials.get('database')
        print(f"[DEBUG] Database name in analysis: '{database}'")
        print(f"[DEBUG] Database name length: {len(database)}")
        print(f"[DEBUG] Database name bytes: {database.encode()}")
        
        # FIX: Trim whitespace from database name to match actual database
        database = database.strip() if database else database
        print(f"[DEBUG] Database name after trim: '{database}'")
        print(f"[DEBUG] Database name length after trim: {len(database)}")
        
        # Get list of tables with detailed info
        cursor.execute("""
            SELECT table_name, table_type, engine,
                   avg_row_length, data_length, index_length,
                   create_time, update_time, table_comment,
                   row_format, table_collation
            FROM information_schema.tables
            WHERE table_schema = %s
        """, (database,))
        tables_result = cursor.fetchall()
        
        print(f"[DEBUG] Query returned {len(tables_result)} tables")
        for table in tables_result:
            print(f"[DEBUG] Found table: {table[0]}")
        
        connection = connect_to_database(connection_info)
        cursor = connection.cursor()
        
        # Get database information
        cursor.execute("SELECT VERSION()")
        version_result = cursor.fetchone()
        version = version_result[0] if version_result else "Unknown"
        
        # Get character set and collation
        cursor.execute("SELECT @@character_set_database, @@collation_database")
        charset_result = cursor.fetchone()
        charset = charset_result[0] if charset_result else "Unknown"
        collation = charset_result[1] if charset_result else "Unknown"
        
        # Get list of tables with detailed info
        cursor.execute("""
            SELECT table_name, table_type, engine,
                   avg_row_length, data_length, index_length,
                   create_time, update_time, table_comment,
                   row_format, table_collation
            FROM information_schema.tables
            WHERE table_schema = %s
        """, (database,))
        tables_result = cursor.fetchall()
        
        print(f"[DEBUG] Query returned {len(tables_result)} tables")
        
        # Get detailed table structures
        tables = []
        for row in tables_result:
            table_name = row[0]
            
            # Get REAL row count directly from table (not cached from information_schema)
            try:
                print(f"[DEBUG] Counting rows for table {table_name}...")
                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                count_result = cursor.fetchone()
                real_row_count = count_result[0] if count_result else 0
                print(f"[DEBUG] {table_name} has {real_row_count} real rows")
            except Exception as e:
                print(f"Error counting rows for {table_name}: {e}")
                real_row_count = 0
            
            # Unpack table info tuple properly
            table_name_unpacked, table_type, engine, avg_row_length, data_length, index_length, create_time, update_time, comment, row_format, table_collation = row
            
            table_info = {
                "name": table_name_unpacked,
                "type": table_type,
                "engine": engine,
                "estimated_rows": real_row_count,  # Use REAL count, not cached
                "avg_row_length": avg_row_length if avg_row_length else 0,
                "data_length": data_length if data_length else 0,
                "index_length": index_length if index_length else 0,
                "create_time": str(create_time) if create_time else None,
                "update_time": str(update_time) if update_time else None,
                "comment": comment if comment else "",
                "row_format": row_format if row_format else None,
                "table_collation": table_collation if table_collation else None,
                "columns": [],
                "constraints": [],
                "indexes": [],
                "check_constraints": [],
                "triggers": []
            }
            
            # Get column details
            try:
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable, column_default, 
                           character_maximum_length, numeric_precision, numeric_scale,
                           column_key, extra, column_comment, column_type,
                           generation_expression, collation_name
                    FROM information_schema.columns 
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """, (database, table_name))
                columns_result = cursor.fetchall()
                
                for col_row in columns_result:
                    column_info = {
                        "name": col_row[0],
                        "data_type": col_row[1],
                        "is_nullable": col_row[2],
                        "default": col_row[3],
                        "max_length": col_row[4],
                        "precision": col_row[5],
                        "scale": col_row[6],
                        "key": col_row[7],
                        "extra": col_row[8],
                        "comment": col_row[9],
                        "column_type": col_row[10],
                        "generation_expression": col_row[11],
                        "collation": col_row[12]
                    }
                    table_info["columns"].append(column_info)
            except Exception:
                pass
            
            # Get constraints
            try:
                cursor.execute(f"""
                    SELECT constraint_name, constraint_type, enforced
                    FROM information_schema.table_constraints
                    WHERE table_schema = %s AND table_name = %s
                """, (database, table_name))
                constraints_result = cursor.fetchall()
                
                for constraint_row in constraints_result:
                    constraint_info = {
                        "name": constraint_row[0],
                        "type": constraint_row[1],
                        "enforced": constraint_row[2] if constraint_row[2] else True
                    }
                    table_info["constraints"].append(constraint_info)
            except Exception:
                pass
            
            # Get check constraints
            try:
                cursor.execute(f"""
                    SELECT constraint_name, check_clause
                    FROM information_schema.check_constraints
                    WHERE constraint_schema = %s AND table_name = %s
                """, (database, table_name))
                check_result = cursor.fetchall()
                
                for check_row in check_result:
                    check_info = {
                        "name": check_row[0],
                        "clause": check_row[1]
                    }
                    table_info["check_constraints"].append(check_info)
            except Exception:
                pass
            
            # Get indexes
            try:
                cursor.execute(f"""
                    SHOW INDEX FROM `{table_name}`
                """)
                indexes_result = cursor.fetchall()
                
                index_dict = {}
                for index_row in indexes_result:
                    index_name = index_row[2]
                    if index_name not in index_dict:
                        index_dict[index_name] = {
                            "name": index_name,
                            "unique": index_row[1] == 0,
                            "columns": [],
                            "collation": index_row[4],
                            "cardinality": index_row[6],
                            "sub_part": index_row[7],
                            "packed": index_row[8],
                            "null": index_row[9],
                            "index_type": index_row[10],
                            "comment": index_row[11]
                        }
                    index_dict[index_name]["columns"].append(index_row[4])
                
                table_info["indexes"] = list(index_dict.values())
            except Exception:
                pass
            
            # Get triggers for this table
            try:
                cursor.execute(f"""
                    SELECT trigger_name, event_manipulation, action_statement, action_timing,
                           action_reference_old_table, action_reference_new_table,
                           action_reference_old_row, action_reference_new_row, 
                           sql_mode, definer, character_set_client,
                           collation_connection, database_collation
                    FROM information_schema.triggers
                    WHERE trigger_schema = %s AND event_object_table = %s
                """, (database, table_name))
                triggers_result = cursor.fetchall()
                
                for trigger_row in triggers_result:
                    trigger_info = {
                        "name": trigger_row[0],
                        "event": trigger_row[1],
                        "action": trigger_row[2],
                        "timing": trigger_row[3],
                        "old_table": trigger_row[4],
                        "new_table": trigger_row[5],
                        "old_row": trigger_row[6],
                        "new_row": trigger_row[7],
                        "sql_mode": trigger_row[8],
                        "definer": trigger_row[9],
                        "charset_client": trigger_row[10],
                        "collation_connection": trigger_row[11],
                        "database_collation": trigger_row[12]
                    }
                    table_info["triggers"].append(trigger_info)
            except Exception:
                pass
            
            tables.append(table_info)
        
        # Get views with definitions
        cursor.execute("""
            SELECT table_name, view_definition, check_option, is_updatable, 
                   definer, security_type, character_set_client, 
                   collation_connection
            FROM information_schema.views
            WHERE table_schema = %s
        """, (database,))
        views_result = cursor.fetchall()
        views = []
        for row in views_result:
            views.append({
                "name": row[0],
                "definition": row[1],
                "check_option": row[2],
                "is_updatable": row[3],
                "definer": row[4],
                "security_type": row[5],
                "charset_client": row[6],
                "collation_connection": row[7]
            })
        
        # Get stored procedures
        cursor.execute("""
            SELECT routine_name, routine_definition, sql_data_access, 
                   sql_mode, routine_comment, definer, created, 
                   last_altered, security_type, character_set_client,
                   collation_connection, database_collation
            FROM information_schema.routines
            WHERE routine_schema = %s AND routine_type = 'PROCEDURE'
        """, (database,))
        procedures_result = cursor.fetchall()
        procedures = []
        for row in procedures_result:
            procedures.append({
                "name": row[0],
                "definition": row[1] if row[1] else "",
                "sql_data_access": row[2],
                "sql_mode": row[3],
                "comment": row[4],
                "definer": row[5],
                "created": str(row[6]) if row[6] else None,
                "last_altered": str(row[7]) if row[7] else None,
                "security_type": row[8],
                "charset_client": row[9],
                "collation_connection": row[10],
                "database_collation": row[11]
            })
        
        # Get functions
        cursor.execute("""
            SELECT routine_name, routine_definition, sql_data_access,
                   sql_mode, routine_comment, definer, created,
                   last_altered, security_type, character_set_client,
                   collation_connection, database_collation, 
                   routine_body, external_name, external_language
            FROM information_schema.routines
            WHERE routine_schema = %s AND routine_type = 'FUNCTION'
        """, (database,))
        functions_result = cursor.fetchall()
        functions = []
        for row in functions_result:
            functions.append({
                "name": row[0],
                "definition": row[1] if row[1] else "",
                "sql_data_access": row[2],
                "sql_mode": row[3],
                "comment": row[4],
                "definer": row[5],
                "created": str(row[6]) if row[6] else None,
                "last_altered": str(row[7]) if row[7] else None,
                "security_type": row[8],
                "charset_client": row[9],
                "collation_connection": row[10],
                "database_collation": row[11],
                "routine_body": row[12],
                "external_name": row[13],
                "external_language": row[14]
            })
        
        # Get triggers (global)
        cursor.execute("""
            SELECT trigger_name, event_manipulation, event_object_table, 
                   action_statement, action_timing, action_reference_old_table,
                   action_reference_new_table, action_reference_old_row,
                   action_reference_new_row, sql_mode, definer, 
                   character_set_client, collation_connection, database_collation,
                   created
            FROM information_schema.triggers
            WHERE trigger_schema = %s
        """, (database,))
        triggers_result = cursor.fetchall()
        triggers = []
        for row in triggers_result:
            triggers.append({
                "name": row[0],
                "event": row[1],
                "table": row[2],
                "action": row[3],
                "timing": row[4],
                "old_table": row[5],
                "new_table": row[6],
                "old_row": row[7],
                "new_row": row[8],
                "sql_mode": row[9],
                "definer": row[10],
                "charset_client": row[11],
                "collation_connection": row[12],
                "database_collation": row[13],
                "created": str(row[14]) if row[14] else None
            })
        
        # Get indexes (global)
        cursor.execute("""
            SELECT table_name, index_name, column_name, non_unique, 
                   seq_in_index, collation, cardinality, sub_part,
                   packed, nullable, index_type, comment, index_comment,
                   is_visible, expression
            FROM information_schema.statistics
            WHERE table_schema = %s
            ORDER BY table_name, index_name, seq_in_index
        """, (database,))
        indexes_result = cursor.fetchall()
        global_indexes = []
        index_dict = {}
        for row in indexes_result:
            key = f"{row[0]}.{row[1]}"
            if key not in index_dict:
                index_dict[key] = {
                    "table": row[0],
                    "name": row[1],
                    "unique": row[3] == 0,
                    "columns": [],
                    "collation": row[5],
                    "cardinality": row[6],
                    "sub_part": row[7],
                    "packed": row[8],
                    "nullable": row[9],
                    "index_type": row[10],
                    "comment": row[11],
                    "index_comment": row[12],
                    "is_visible": row[13],
                    "expression": row[14]
                }
            index_dict[key]["columns"].append(row[2])
        global_indexes = list(index_dict.values())
        
        # Get foreign key relationships with cascade rules
        cursor.execute("""
            SELECT kcu.table_name, kcu.column_name, kcu.constraint_name, 
                   kcu.referenced_table_name, kcu.referenced_column_name,
                   rc.update_rule, rc.delete_rule, rc.match_option
            FROM information_schema.key_column_usage kcu
            JOIN information_schema.referential_constraints rc 
              ON kcu.constraint_name = rc.constraint_name 
              AND kcu.table_schema = rc.constraint_schema
            WHERE kcu.table_schema = %s AND kcu.referenced_table_name IS NOT NULL
        """, (database,))
        fk_result = cursor.fetchall()
        foreign_keys = []
        for row in fk_result:
            foreign_keys.append({
                "table": row[0],
                "column": row[1],
                "constraint": row[2],
                "referenced_table": row[3],
                "referenced_column": row[4],
                "update_rule": row[5],
                "delete_rule": row[6],
                "match_option": row[7]
            })
        
        # Get sequences (auto-increment info)
        cursor.execute("""
            SELECT table_name, column_name, extra
            FROM information_schema.columns
            WHERE table_schema = %s AND extra LIKE '%auto_increment%'
        """, (database,))
        sequences_result = cursor.fetchall()
        sequences = []
        for row in sequences_result:
            sequences.append({
                "table": row[0],
                "column": row[1],
                "extra": row[2]
            })
        
        # Get partition information
        try:
            cursor.execute("""
                SELECT table_name, partition_name, partition_method, 
                       partition_expression, partition_description,
                       table_rows, avg_row_length, data_length,
                       index_length, partition_comment
                FROM information_schema.partitions
                WHERE table_schema = %s AND partition_name IS NOT NULL
            """, (database,))
            partitions_result = cursor.fetchall()
            partitions = []
            for row in partitions_result:
                partitions.append({
                    "table": row[0],
                    "partition_name": row[1],
                    "partition_method": row[2],
                    "partition_expression": row[3],
                    "partition_description": row[4],
                    "table_rows": row[5],
                    "avg_row_length": row[6],
                    "data_length": row[7],
                    "index_length": row[8],
                    "comment": row[9]
                })
        except Exception:
            partitions = []
        
        # Get users and privileges
        try:
            cursor.execute("SELECT user, host FROM mysql.user")
            users_result = cursor.fetchall()
            users = [{"user": row[0], "host": row[1]} for row in users_result]
        except Exception:
            users = []
        
        # Get grants for current user
        try:
            cursor.execute("SHOW GRANTS")
            grants_result = cursor.fetchall()
            grants = [row[0] for row in grants_result]
        except Exception:
            grants = []
        
        connection.close()
        
        return {
            "database_type": "MySQL",
            "version": version,
            "charset": charset,
            "collation": collation,
            "schemas": [database],
            "tables": tables,
            "views": views,
            "procedures": procedures,
            "functions": functions,
            "triggers": triggers,
            "indexes": global_indexes,
            "foreign_keys": foreign_keys,
            "sequences": sequences,
            "partitions": partitions,
            "users": users,
            "grants": grants,
            "environment": {
                "host": credentials.get('host'),
                "port": credentials.get('port', 3306),
                "database": database
            }
        }
    except Exception as e:
        raise Exception(f"MySQL analysis failed: {str(e)}")

def analyze_postgresql_schema(connection_info):
    """Analyze PostgreSQL database schema comprehensively"""
    try:
        import psycopg2
        
        # Extract credentials
        credentials = connection_info.get("credentials", {})
        host = credentials.get('host')
        port = credentials.get('port', 5432)
        database = credentials.get('database')
        username = credentials.get('username')
        password = credentials.get('password')
        
        # Create connection
        connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': username,
            'password': password
        }
        
        connection = psycopg2.connect(**connection_params)
        cursor = connection.cursor()
        
        # Get database information
        cursor.execute("SELECT version()")
        version_result = cursor.fetchone()
        version = version_result[0] if version_result else "Unknown"
        
        # Get character encoding
        cursor.execute("SHOW server_encoding")
        encoding_result = cursor.fetchone()
        encoding = encoding_result[0] if encoding_result else "Unknown"
        
        # Get list of tables with detailed info
        cursor.execute("""
            SELECT
                schemaname,
                tablename,
                tableowner,
                hasindexes,
                hasrules,
                hastriggers
            FROM pg_tables
            WHERE schemaname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            ORDER BY schemaname, tablename
        """)
        tables_result = cursor.fetchall()
        
        # Get detailed table structures
        tables = []
        for row in tables_result:
            schema_name = row[0]
            table_name = row[1]
            table_info = {
                "name": table_name,
                "schema": schema_name,
                "type": "BASE TABLE",
                "engine": "heap",
                "estimated_rows": 0,
                "avg_row_length": 0,
                "data_length": 0,
                "index_length": 0,
                "create_time": None,
                "update_time": None,
                "comment": "",
                "row_format": "heap",
                "table_collation": "C",
                "columns": [],
                "constraints": [],
                "indexes": [],
                "check_constraints": [],
                "triggers": []
            }
            
            # Get row count for this table
            try:
                cursor.execute(f"SELECT COUNT(*) FROM \"{schema_name}\".\"{table_name}\"")
                count_result = cursor.fetchone()
                table_info["estimated_rows"] = count_result[0] if count_result else 0
            except Exception:
                table_info["estimated_rows"] = 0
            
            # Get column details
            try:
                cursor.execute("""
                    SELECT
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale,
                        udt_name,
                        column_default
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """, (schema_name, table_name))
                columns_result = cursor.fetchall()
                
                for col_row in columns_result:
                    column_info = {
                        "name": col_row[0],
                        "data_type": col_row[1],
                        "is_nullable": col_row[2],
                        "default": col_row[3],
                        "max_length": col_row[4],
                        "precision": col_row[5],
                        "scale": col_row[6],
                        "key": "",
                        "extra": "",
                        "comment": "",
                        "column_type": col_row[7],
                        "generation_expression": None,
                        "collation": "C"
                    }
                    table_info["columns"].append(column_info)
            except Exception:
                pass
            
            tables.append(table_info)
        
        # Get views
        cursor.execute("""
            SELECT
                schemaname,
                viewname,
                definition
            FROM pg_views
            WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
            ORDER BY schemaname, viewname
        """)
        views_result = cursor.fetchall()
        views = []
        for row in views_result:
            views.append({
                "name": row[1],
                "schema": row[0],
                "definition": row[2],
                "check_option": "NONE",
                "is_updatable": "YES",
                "definer": "postgres",
                "security_type": "DEFINER",
                "charset_client": "UTF8",
                "collation_connection": "C"
            })
        
        connection.close()
        
        return {
            "database_type": "PostgreSQL",
            "version": version,
            "charset": encoding,
            "collation": "C",
            "schemas": list(set([table["schema"] for table in tables] + [view["schema"] for view in views])),
            "tables": tables,
            "views": views,
            "procedures": [],
            "functions": [],
            "triggers": [],
            "indexes": [],
            "foreign_keys": [],
            "sequences": [],
            "partitions": [],
            "users": [],
            "grants": [],
            "environment": {
                "host": host,
                "port": port,
                "database": database
            }
        }
    except Exception as e:
        raise Exception(f"PostgreSQL analysis failed: {str(e)}")

def analyze_database_schema(connection_info):
    """Analyze database schema based on database type - FIXED VERSION"""
    db_type = connection_info.get("dbType", "Unknown")
    
    if db_type == "MySQL":
        return analyze_mysql_schema(connection_info)
    elif db_type == "PostgreSQL":
        return analyze_postgresql_schema(connection_info)
    else:
        # For other database types, attempt to connect and analyze or return helpful error
        return {
            "database_type": db_type,
            "version": "Unknown",
            "charset": "Unknown",
            "collation": "Unknown",
            "schemas": [connection_info.get("credentials", {}).get("database", "Unknown")],
            "tables": [],
            "views": [],
            "procedures": [],
            "functions": [],
            "triggers": [],
            "indexes": [],
            "foreign_keys": [],
            "sequences": [],
            "partitions": [],
            "users": [],
            "grants": [],
            "environment": {
                "host": "unknown",
                "port": 0,
                "database": "unknown"
            },
            "error": f"Database type '{db_type}' is not supported. Currently supported: MySQL, PostgreSQL."
        }

async def run_analysis_task():
    """Background task to run the analysis"""
    print("[DEBUG] run_analysis_task() called - checking what version is running")
    global analysis_status
    
    # Reset status
    analysis_status = {
        "phase": "Initializing",
        "percent": 0,
        "done": False,
        "results_summary": None,
        "error": None
    }
    
    try:
        # Get session info
        session = get_active_session()
        source_db = session.get("source")
        
        if not source_db:
            raise Exception("No source database selected")
        
        # Get full connection details
        connection_info = get_connection_by_id(source_db["id"])
        if not connection_info:
            raise Exception("Source database connection not found")
        
        # Analysis phases
        phases = [
            ("Connecting to source database", 10),
            ("Analyzing database schema", 30),
            ("Extracting table structures", 50),
            ("Analyzing views and procedures", 70),
            ("Checking indexes and relationships", 85),
            ("Generating analysis report", 100)
        ]
        
        for phase, percent in phases[:-1]:  # All phases except the last one
            analysis_status["phase"] = phase
            analysis_status["percent"] = percent
            await asyncio.sleep(0.5)  # Simulate work
        
        # Perform actual schema analysis
        analysis_status["phase"] = "Analyzing database schema"
        analysis_status["percent"] = 60
        analysis_bundle = analyze_database_schema(connection_info)
        
        # Final phase
        analysis_status["phase"] = "Generating analysis report"
        analysis_status["percent"] = 100
        
        # Clear existing artifacts before saving new analysis
        if os.path.exists("artifacts"):
            import shutil
            shutil.rmtree("artifacts")
            print("[DEBUG] Cleared artifacts directory")
        os.makedirs("artifacts", exist_ok=True)
        
        # Add timestamp to analysis bundle
        import datetime
        analysis_bundle["analysis_timestamp"] = datetime.datetime.now().isoformat()
        analysis_bundle["analysis_version"] = "v2_live_rows"
        
        print(f"[DEBUG] Saving analysis with {len(analysis_bundle['tables'])} tables and live row counts")
        table_counts = [f"{t['name']}:{t['estimated_rows']}" for t in analysis_bundle['tables']]
        print(f"[DEBUG] Table row counts: {table_counts}")
        
        with open("artifacts/analysis_bundle.json", "w") as f:
            json.dump(analysis_bundle, f, indent=2, default=str)
        
        # Update status
        analysis_status["done"] = True
        analysis_status["results_summary"] = {
            "tables_analyzed": len(analysis_bundle["tables"]),
            "views_found": len(analysis_bundle["views"]),
            "procedures_found": len(analysis_bundle["procedures"]),
            "functions_found": len(analysis_bundle.get("functions", [])),
            "triggers_found": len(analysis_bundle.get("triggers", [])),
            "indexes_found": len(analysis_bundle["indexes"]),
            "total_rows": sum(table["estimated_rows"] for table in analysis_bundle["tables"])
        }
        
    except Exception as e:
        analysis_status["error"] = str(e)
        analysis_status["done"] = True
        analysis_status["percent"] = 100

def export_analysis_json():
    """Export analysis bundle as JSON"""
    if not os.path.exists("artifacts/analysis_bundle.json"):
        return None
    
    with open("artifacts/analysis_bundle.json", "r") as f:
        data = json.load(f)
    
    return data

def export_analysis_xlsx():
    """Export analysis bundle as Excel"""
    if not os.path.exists("artifacts/analysis_bundle.json"):
        return None
    
    with open("artifacts/analysis_bundle.json", "r") as f:
        data = json.load(f)
    
    # Create Excel file
    excel_filename = "artifacts/analysis_report.xlsx"
    workbook = xlsxwriter.Workbook(excel_filename)
    
    # Summary sheet
    summary_sheet = workbook.add_worksheet("Summary")
    summary_sheet.write(0, 0, "Database Analysis Report - Summary")
    summary_sheet.write(2, 0, "Database Type:")
    summary_sheet.write(2, 1, data.get("database_type", "Unknown"))
    summary_sheet.write(3, 0, "Version:")
    summary_sheet.write(3, 1, data.get("version", "Unknown"))
    summary_sheet.write(4, 0, "Tables:")
    summary_sheet.write(4, 1, len(data.get("tables", [])))
    summary_sheet.write(5, 0, "Views:")
    summary_sheet.write(5, 1, len(data.get("views", [])))
    summary_sheet.write(6, 0, "Procedures:")
    summary_sheet.write(6, 1, len(data.get("procedures", [])))
    
    # Tables sheet
    if "tables" in data:
        tables_sheet = workbook.add_worksheet("Tables")
        tables_sheet.write(0, 0, "Table Name")
        tables_sheet.write(0, 1, "Type")
        tables_sheet.write(0, 2, "Engine")
        tables_sheet.write(0, 3, "Rows")
        tables_sheet.write(0, 4, "Data Length")
        tables_sheet.write(0, 5, "Index Length")
        
        for i, table in enumerate(data["tables"], start=1):
            tables_sheet.write(i, 0, table.get("name", ""))
            tables_sheet.write(i, 1, table.get("type", ""))
            tables_sheet.write(i, 2, table.get("engine", ""))
            tables_sheet.write(i, 3, table.get("estimated_rows", 0))
            tables_sheet.write(i, 4, table.get("data_length", 0))
            tables_sheet.write(i, 5, table.get("index_length", 0))
    
    # Views sheet
    if "views" in data:
        views_sheet = workbook.add_worksheet("Views")
        views_sheet.write(0, 0, "View Name")
        views_sheet.write(0, 1, "Definition")
        
        for i, view in enumerate(data["views"], start=1):
            views_sheet.write(i, 0, view.get("name", ""))
            views_sheet.write(i, 1, view.get("definition", "")[:1000])  # Limit length
    
    workbook.close()
    return excel_filename

def export_analysis_pdf():
    """Export analysis bundle as PDF"""
    if not os.path.exists("artifacts/analysis_bundle.json"):
        return None
    
    with open("artifacts/analysis_bundle.json", "r") as f:
        data = json.load(f)
    
    # Create PDF file
    pdf_filename = "artifacts/analysis_report.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("Strata - Database Analysis Report", styles["Title"])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Database Info
    db_info = Paragraph(f"<b>Database Type:</b> {data.get('database_type', 'Unknown')}<br/>"
                        f"<b>Version:</b> {data.get('version', 'Unknown')}<br/>"
                        f"<b>Charset:</b> {data.get('charset', 'Unknown')}<br/>"
                        f"<b>Collation:</b> {data.get('collation', 'Unknown')}", 
                        styles["Normal"])
    story.append(db_info)
    story.append(Spacer(1, 12))
    
    # Summary
    summary_data = [
        ["Category", "Count"],
        ["Tables", str(len(data.get("tables", [])))],
        ["Views", str(len(data.get("views", [])))],
        ["Procedures", str(len(data.get("procedures", [])))],
        ["Functions", str(len(data.get("functions", [])))],
        ["Triggers", str(len(data.get("triggers", [])))],
        ["Indexes", str(len(data.get("indexes", [])))]
    ]
    
    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 12))
    
    # Tables section
    if "tables" in data:
        tables_header = Paragraph("<b>Tables</b>", styles["Heading2"])
        story.append(tables_header)
        
        for table in data["tables"][:10]:  # Limit to first 10 tables
            table_name = Paragraph(f"<b>{table.get('name', '')}</b>", styles["Heading3"])
            story.append(table_name)
            
            table_info = Paragraph(f"Type: {table.get('type', '')}<br/>"
                                   f"Engine: {table.get('engine', '')}<br/>"
                                   f"Rows: {table.get('estimated_rows', 0)}<br/>"
                                   f"Columns: {len(table.get('columns', []))}", 
                                   styles["Normal"])
            story.append(table_info)
            story.append(Spacer(1, 6))
    
    # Build PDF
    doc.build(story)
    return pdf_filename

@router.post("/start", response_model=CommonResponse)
async def start_analysis(background_tasks: BackgroundTasks):
    global analysis_status
    analysis_status["phase"] = "Starting"
    analysis_status["percent"] = 0
    analysis_status["done"] = False
    analysis_status["error"] = None
    
    background_tasks.add_task(run_analysis_task)
    
    return CommonResponse(ok=True, message="Analysis started")

@router.get("/status", response_model=AnalysisStatusResponse)
async def get_analysis_status():
    global analysis_status
    return AnalysisStatusResponse(
        ok=True,
        phase=analysis_status["phase"],
        percent=analysis_status["percent"],
        done=analysis_status["done"],
        resultsSummary=analysis_status["results_summary"],
        error=analysis_status["error"]
    )

@router.get("/data")
async def get_analysis_data():
    """Get analysis data for display in frontend"""
    if not os.path.exists("artifacts/analysis_bundle.json"):
        return {"error": "Analysis data not found"}
    
    with open("artifacts/analysis_bundle.json", "r") as f:
        data = json.load(f)
    
    return data

@router.get("/export/json")
async def export_analysis_json_endpoint():
    """Export analysis bundle as JSON"""
    data = export_analysis_json()
    if data is None:
        return {"error": "Analysis report not found"}
    
    return JSONResponse(content=data)

@router.get("/export/xlsx")
async def export_analysis_xlsx_endpoint():
    """Export analysis bundle as Excel"""
    filename = export_analysis_xlsx()
    if filename is None:
        return {"error": "Analysis report not found"}
    
    return FileResponse(
        filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="analysis_report.xlsx"
    )

@router.get("/export/pdf")
async def export_analysis_pdf_endpoint():
    """Export analysis bundle as PDF"""
    filename = export_analysis_pdf()
    if filename is None:
        return {"error": "Analysis report not found"}
    
    return FileResponse(
        filename,
        media_type="application/pdf",
        filename="analysis_report.pdf"
    )