from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from backend.models import CommonResponse, AnalysisStatusResponse
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

# Global variable to track extraction status
extraction_status = {
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

def extract_mysql_ddl(connection_info):
    """Extract comprehensive DDL from MySQL database"""
    try:
        # Import mysql.connector inside the function to handle import errors
        import mysql.connector
        
        # Extract credentials
        credentials = connection_info.get("credentials", {})
        host = credentials.get('host')
        port = credentials.get('port', 3306)
        database = credentials.get('database')
        username = credentials.get('username')
        password = credentials.get('password')
        # Handle both 'ssl' and 'ssl-mode' parameters for compatibility
        ssl_mode = credentials.get('ssl', credentials.get('ssl-mode', 'require'))
        
        # Configure SSL settings
        ssl_config = {}
        if ssl_mode == 'disable' or ssl_mode == 'false':
            ssl_config['ssl_disabled'] = True
        else:
            # For Azure MySQL, we need to handle SSL properly
            ssl_config['ssl_disabled'] = False
            ssl_config['ssl_verify_cert'] = False
            ssl_config['ssl_verify_identity'] = False
            # For Azure MySQL specifically
            if host and 'mysql.database.azure.com' in host:
                ssl_config['ssl_verify_cert'] = False
                ssl_config['ssl_verify_identity'] = False
        
        # Create connection with SSL configuration
        connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': username,
            'password': password,
            **ssl_config
        }
        
        connection = mysql.connector.connect(**connection_params)
        cursor = connection.cursor()
        
        # Extract DDL scripts
        ddl_scripts = {
            "tables": [],
            "views": [],
            "indexes": [],
            "constraints": [],
            "sequences": [],
            "triggers": [],
            "procedures": [],
            "functions": [],
            "materialized_views": [],
            "types": [],
            "domains": [],
            "roles": [],
            "grants": [],
            "partition_schemes": [],
            "storage_configs": [],
            "computed_columns": [],
            "advanced_constraints": [],
            "security_policies": [],
            "data_sampling": []
        }
        
        # Get tables DDL with enhanced information
        cursor.execute("SHOW TABLES")
        tables_result = cursor.fetchall()
        tables = []
        if tables_result:
            for row in tables_result:
                if row and len(row) > 0:
                    tables.append(str(row[0]))
        
        for table in tables:
            try:
                # Get CREATE TABLE statement
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                create_result = cursor.fetchone()
                if create_result and len(create_result) > 1 and create_result[1]:
                    ddl_scripts["tables"].append({
                        "name": str(table),
                        "ddl": str(create_result[1]),
                        "type": "TABLE"
                    })
            except Exception:
                pass
        
        # Get views DDL with enhanced information
        cursor.execute("SHOW FULL TABLES WHERE Table_type = 'VIEW'")
        views_result = cursor.fetchall()
        views = []
        if views_result:
            for row in views_result:
                if row and len(row) > 0:
                    views.append(str(row[0]))
        
        for view in views:
            try:
                # Get CREATE VIEW statement
                cursor.execute(f"SHOW CREATE VIEW `{view}`")
                create_result = cursor.fetchone()
                if create_result and len(create_result) > 1 and create_result[1]:
                    ddl_scripts["views"].append({
                        "name": str(view),
                        "ddl": str(create_result[1]),
                        "type": "VIEW"
                    })
            except Exception:
                pass
        
        # Get stored procedures with enhanced information
        cursor.execute("""
            SELECT routine_name, routine_definition, sql_data_access, 
                   security_type, created, last_altered
            FROM information_schema.routines
            WHERE routine_schema = %s AND routine_type = 'PROCEDURE'
        """, (database,))
        procedures_result = cursor.fetchall()
        
        for row in procedures_result:
            ddl_scripts["procedures"].append({
                "name": str(row[0]) if row and len(row) > 0 else "",
                "ddl": str(row[1]) if row and len(row) > 1 and row[1] else "",
                "type": "PROCEDURE",
                "sql_data_access": str(row[2]) if row and len(row) > 2 else "",
                "security_type": str(row[3]) if row and len(row) > 3 else "",
                "created": str(row[4]) if row and len(row) > 4 and row[4] else None,
                "last_altered": str(row[5]) if row and len(row) > 5 and row[5] else None
            })
        
        # Get functions with enhanced information
        cursor.execute("""
            SELECT routine_name, routine_definition, sql_data_access,
                   security_type, created, last_altered, data_type
            FROM information_schema.routines
            WHERE routine_schema = %s AND routine_type = 'FUNCTION'
        """, (database,))
        functions_result = cursor.fetchall()
        
        for row in functions_result:
            ddl_scripts["functions"].append({
                "name": str(row[0]) if row and len(row) > 0 else "",
                "ddl": str(row[1]) if row and len(row) > 1 and row[1] else "",
                "type": "FUNCTION",
                "sql_data_access": str(row[2]) if row and len(row) > 2 else "",
                "security_type": str(row[3]) if row and len(row) > 3 else "",
                "created": str(row[4]) if row and len(row) > 4 and row[4] else None,
                "last_altered": str(row[5]) if row and len(row) > 5 and row[5] else None,
                "return_type": str(row[6]) if row and len(row) > 6 else ""
            })
        
        # Get triggers with complete DDL and dialect conversion capabilities
        cursor.execute("""
            SELECT trigger_name, event_manipulation, event_object_table, 
                   action_statement, action_timing, definer, created,
                   sql_mode, character_set_client, collation_connection
            FROM information_schema.triggers
            WHERE trigger_schema = %s
        """, (database,))
        triggers_result = cursor.fetchall()
        
        for row in triggers_result:
            # Generate proper CREATE TRIGGER statement with target dialect conversion placeholder
            trigger_ddl = f"DELIMITER $$\nCREATE TRIGGER `{str(row[0]) if row and len(row) > 0 else ''}` {str(row[4]) if row and len(row) > 4 else ''} {str(row[1]) if row and len(row) > 1 else ''} ON `{str(row[2]) if row and len(row) > 2 else ''}` FOR EACH ROW\n{str(row[3]) if row and len(row) > 3 else ''}$$\nDELIMITER ;"
            
            # Add target dialect conversion template
            target_ddl = f"-- TARGET DIALECT CONVERSION TEMPLATE --\n-- Convert the following MySQL trigger to target dialect --\n{trigger_ddl}"
            
            ddl_scripts["triggers"].append({
                "name": str(row[0]) if row and len(row) > 0 else "",
                "ddl": trigger_ddl,
                "target_ddl_template": target_ddl,
                "type": "TRIGGER",
                "event": str(row[1]) if row and len(row) > 1 else "",
                "table": str(row[2]) if row and len(row) > 2 else "",
                "timing": str(row[4]) if row and len(row) > 4 else "",
                "definer": str(row[5]) if row and len(row) > 5 else "",
                "created": str(row[6]) if row and len(row) > 6 and row[6] else None,
                "sql_mode": str(row[7]) if row and len(row) > 7 else ""
            })
        
        # Get constraints with enhanced information
        constraints = []
        relationships = []
        
        # Get primary keys with enhanced information
        cursor.execute("""
            SELECT kcu.table_name, kcu.column_name, kcu.constraint_name,
                   tc.constraint_type
            FROM information_schema.key_column_usage kcu
            JOIN information_schema.table_constraints tc 
              ON kcu.constraint_name = tc.constraint_name 
              AND kcu.table_schema = tc.table_schema
            WHERE kcu.table_schema = %s AND tc.constraint_type = 'PRIMARY KEY'
            ORDER BY kcu.table_name, kcu.ordinal_position
        """, (database,))
        pk_result = cursor.fetchall()
        
        # Group primary keys by table
        pk_dict = {}
        for row in pk_result:
            table_name = row[0]
            if table_name not in pk_dict:
                pk_dict[table_name] = {
                    "table": table_name,
                    "columns": [],
                    "constraint_name": row[2],
                    "constraint_type": row[3]
                }
            pk_dict[table_name]["columns"].append(row[1])
        
        for table_name, pk_info in pk_dict.items():
            constraint_ddl = f"ALTER TABLE `{table_name}` ADD CONSTRAINT `{pk_info['constraint_name']}` PRIMARY KEY ({', '.join([f'`{col}`' for col in pk_info['columns']])});"
            constraints.append({
                "type": "PRIMARY KEY",
                "table": table_name,
                "columns": pk_info["columns"],
                "name": pk_info["constraint_name"],
                "ddl": constraint_ddl
            })
        
        # Get foreign keys with cascade options
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
        
        # Group foreign keys by constraint
        fk_dict = {}
        for row in fk_result:
            constraint_name = row[2]
            if constraint_name not in fk_dict:
                fk_dict[constraint_name] = {
                    "table": row[0],
                    "columns": [],
                    "referenced_table": row[3],
                    "referenced_columns": [],
                    "name": constraint_name,
                    "update_rule": row[5],
                    "delete_rule": row[6],
                    "match_option": row[7]
                }
            fk_dict[constraint_name]["columns"].append(row[1])
            fk_dict[constraint_name]["referenced_columns"].append(row[4])
        
        for constraint_name, fk_info in fk_dict.items():
            # Generate FK DDL with cascade options
            fk_columns = ', '.join([f'`{col}`' for col in fk_info["columns"]])
            ref_columns = ', '.join([f'`{col}`' for col in fk_info["referenced_columns"]])
            cascade_options = []
            if fk_info["update_rule"] != "NO ACTION":
                cascade_options.append(f"ON UPDATE {fk_info['update_rule']}")
            if fk_info["delete_rule"] != "NO ACTION":
                cascade_options.append(f"ON DELETE {fk_info['delete_rule']}")
            
            cascade_str = " " + " ".join(cascade_options) if cascade_options else ""
            constraint_ddl = f"ALTER TABLE `{fk_info['table']}` ADD CONSTRAINT `{fk_info['name']}` FOREIGN KEY ({fk_columns}) REFERENCES `{fk_info['referenced_table']}` ({ref_columns}){cascade_str};"
            
            constraints.append({
                "type": "FOREIGN KEY",
                "table": fk_info["table"],
                "columns": fk_info["columns"],
                "referenced_table": fk_info["referenced_table"],
                "referenced_columns": fk_info["referenced_columns"],
                "name": fk_info["name"],
                "update_rule": fk_info["update_rule"],
                "delete_rule": fk_info["delete_rule"],
                "match_option": fk_info["match_option"],
                "ddl": constraint_ddl
            })
            
            relationships.append({
                "source_table": fk_info["table"],
                "source_columns": fk_info["columns"],
                "target_table": fk_info["referenced_table"],
                "target_columns": fk_info["referenced_columns"],
                "constraint_name": fk_info["name"],
                "update_rule": fk_info["update_rule"],
                "delete_rule": fk_info["delete_rule"]
            })
        
        # Get check constraints
        cursor.execute("""
            SELECT tc.table_name, tc.constraint_name, cc.check_clause
            FROM information_schema.table_constraints tc
            JOIN information_schema.check_constraints cc
              ON tc.constraint_name = cc.constraint_name
              AND tc.constraint_schema = cc.constraint_schema
            WHERE tc.constraint_schema = %s AND tc.constraint_type = 'CHECK'
        """, (database,))
        check_result = cursor.fetchall()
        
        for row in check_result:
            constraint_ddl = f"ALTER TABLE `{row[0]}` ADD CONSTRAINT `{row[1]}` CHECK ({row[2]});"
            constraints.append({
                "type": "CHECK",
                "table": row[0],
                "name": row[1],
                "check_clause": row[2],
                "ddl": constraint_ddl
            })
        
        # Get unique constraints
        cursor.execute("""
            SELECT kcu.table_name, kcu.column_name, kcu.constraint_name
            FROM information_schema.key_column_usage kcu
            JOIN information_schema.table_constraints tc 
              ON kcu.constraint_name = tc.constraint_name 
              AND kcu.table_schema = tc.table_schema
            WHERE kcu.table_schema = %s AND tc.constraint_type = 'UNIQUE'
            ORDER BY kcu.table_name, kcu.ordinal_position
        """, (database,))
        unique_result = cursor.fetchall()
        
        # Group unique constraints by constraint name
        unique_dict = {}
        for row in unique_result:
            constraint_name = row[2]
            if constraint_name not in unique_dict:
                unique_dict[constraint_name] = {
                    "table": row[0],
                    "columns": [],
                    "name": constraint_name
                }
            unique_dict[constraint_name]["columns"].append(row[1])
        
        for constraint_name, unique_info in unique_dict.items():
            columns_str = ', '.join([f'`{col}`' for col in unique_info["columns"]])
            constraint_ddl = f"ALTER TABLE `{unique_info['table']}` ADD CONSTRAINT `{unique_info['name']}` UNIQUE ({columns_str});"
            constraints.append({
                "type": "UNIQUE",
                "table": unique_info["table"],
                "columns": unique_info["columns"],
                "name": unique_info["name"],
                "ddl": constraint_ddl
            })
        
        # Get indexes with enhanced information
        cursor.execute("""
            SELECT table_name, index_name, column_name, non_unique, 
                   seq_in_index, collation, cardinality, sub_part,
                   packed, nullable, index_type, comment
            FROM information_schema.statistics
            WHERE table_schema = %s
            ORDER BY table_name, index_name, seq_in_index
        """, (database,))
        indexes_result = cursor.fetchall()
        
        # Group indexes by name
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
                    "comment": row[11]
                }
            index_dict[key]["columns"].append(row[2])
        
        indexes = list(index_dict.values())
        for idx in indexes:
            columns_str = ', '.join([f'`{col}`' for col in idx["columns"]])
            unique_str = "UNIQUE " if idx["unique"] else ""
            index_ddl = f"CREATE {unique_str}INDEX `{idx['name']}` ON `{idx['table']}` ({columns_str});"
            ddl_scripts["indexes"].append({
                "table": idx["table"],
                "name": idx["name"],
                "unique": idx["unique"],
                "columns": idx["columns"],
                "ddl": index_ddl,
                "collation": idx["collation"],
                "cardinality": idx["cardinality"],
                "index_type": idx["index_type"],
                "comment": idx["comment"]
            })
        
        # Get sequences (auto-increment info) with ALTER SEQUENCE statements
        cursor.execute("""
            SELECT table_name, column_name, extra, column_default
            FROM information_schema.columns
            WHERE table_schema = %s AND extra LIKE '%auto_increment%'
        """, (database,))
        sequences_result = cursor.fetchall()
        
        for row in sequences_result:
            # For MySQL, we create ALTER TABLE statements to set auto_increment
            sequence_ddl = f"ALTER TABLE `{row[0]}` MODIFY `{row[1]}` {row[1]} AUTO_INCREMENT;"
            
            # Add CREATE SEQUENCE template for target dialects that support it
            create_sequence_template = f"CREATE SEQUENCE {row[0]}_{row[1]}_seq START WITH 1 INCREMENT BY 1;"
            alter_sequence_template = f"ALTER SEQUENCE {row[0]}_{row[1]}_seq RESTART WITH {{current_value}};"
            
            ddl_scripts["sequences"].append({
                "table": row[0],
                "column": row[1],
                "ddl": sequence_ddl,
                "create_sequence_template": create_sequence_template,
                "alter_sequence_template": alter_sequence_template,
                "type": "AUTO_INCREMENT",
                "default_value": row[3]
            })
        
        # Get partition information
        try:
            cursor.execute("""
                SELECT table_name, partition_name, partition_method, 
                       partition_expression, partition_description
                FROM information_schema.partitions
                WHERE table_schema = %s AND partition_name IS NOT NULL
            """, (database,))
            partitions_result = cursor.fetchall()
            
            partition_dict = {}
            for row in partitions_result:
                table_name = row[0]
                if table_name not in partition_dict:
                    partition_dict[table_name] = {
                        "table": table_name,
                        "partitions": []
                    }
                partition_dict[table_name]["partitions"].append({
                    "name": row[1],
                    "method": row[2],
                    "expression": row[3],
                    "description": row[4]
                })
            
            for table_name, partition_info in partition_dict.items():
                ddl_scripts["partition_schemes"].append({
                    "table": table_name,
                    "partitions": partition_info["partitions"]
                })
        except Exception:
            pass
        
        # Get user-defined types (MySQL doesn't have user-defined types, but we'll include for completeness)
        # Get domains (MySQL doesn't have domains, but we'll include for completeness)
        
        # Get synonyms/aliases (MySQL doesn't have synonyms, but we'll include for completeness)
        synonyms = []
        
        # Get jobs/schedulers (MySQL events)
        jobs = []
        try:
            cursor.execute("""
                SELECT event_name, event_definition, event_type, 
                       execute_at, interval_value, interval_field,
                       starts, ends, status, definer
                FROM information_schema.events
                WHERE event_schema = %s
            """, (database,))
            events_result = cursor.fetchall()
            for row in events_result:
                jobs.append({
                    "name": row[0],
                    "definition": row[1],
                    "type": row[2],
                    "execute_at": str(row[3]) if row[3] else None,
                    "interval_value": row[4],
                    "interval_field": row[5],
                    "starts": str(row[6]) if row[6] else None,
                    "ends": str(row[7]) if row[7] else None,
                    "status": row[8],
                    "definer": row[9]
                })
        except Exception:
            pass
        
        # Get data profile baseline
        data_profile = {}
        for table in tables:
            try:
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                count_result = cursor.fetchone()
                row_count = count_result[0] if count_result else 0
                
                # Get column info for null stats
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_schema = %s AND table_name = %s
                """, (database, table))
                columns_result = cursor.fetchall()
                
                column_stats = []
                for col_row in columns_result:
                    column_name = col_row[0]
                    try:
                        # Get null count
                        cursor.execute(f"SELECT COUNT(*) FROM `{table}` WHERE `{column_name}` IS NULL")
                        null_result = cursor.fetchone()
                        null_count = null_result[0] if null_result else 0
                        
                        # Get distinct count
                        cursor.execute(f"SELECT COUNT(DISTINCT `{column_name}`) FROM `{table}`")
                        distinct_result = cursor.fetchone()
                        distinct_count = distinct_result[0] if distinct_result else 0
                        
                        column_stats.append({
                            "name": column_name,
                            "data_type": col_row[1],
                            "nullable": col_row[2] == "YES",
                            "null_count": null_count,
                            "distinct_count": distinct_count,
                            "null_ratio": null_count / row_count if row_count > 0 else 0
                        })
                    except Exception:
                        column_stats.append({
                            "name": column_name,
                            "data_type": col_row[1],
                            "nullable": col_row[2] == "YES",
                            "null_count": 0,
                            "distinct_count": 0,
                            "null_ratio": 0
                        })
                
                data_profile[table] = {
                    "row_count": row_count,
                    "columns": column_stats
                }
            except Exception:
                data_profile[table] = {
                    "row_count": 0,
                    "columns": []
                }
        
        # Get computed/generated columns
        try:
            cursor.execute("""
                SELECT table_name, column_name, generation_expression, column_default
                FROM information_schema.columns
                WHERE table_schema = %s AND extra LIKE '%%GENERATED%%'
            """, (database,))
            computed_result = cursor.fetchall()
            
            for row in computed_result:
                if row and len(row) >= 4:
                    computed_ddl = f"ALTER TABLE `{row[0]}` ADD COLUMN `{row[1]}` GENERATED ALWAYS AS ({row[2]});"
                    ddl_scripts["computed_columns"].append({
                        "table": str(row[0]) if row[0] else "",
                        "column": str(row[1]) if row[1] else "",
                        "expression": str(row[2]) if row[2] else "",
                        "ddl": computed_ddl,
                        "default_value": str(row[3]) if row[3] else ""
                    })
        except Exception as e:
            # Handle older MySQL versions that don't have is_generated column
            print(f"Warning: Could not extract computed columns: {str(e)}")
            pass
        
        # Get advanced constraints (named check constraints with more details)
        cursor.execute("""
            SELECT tc.table_name, tc.constraint_name, cc.check_clause, tc.enforced
            FROM information_schema.table_constraints tc
            JOIN information_schema.check_constraints cc
              ON tc.constraint_name = cc.constraint_name
              AND tc.constraint_schema = cc.constraint_schema
            WHERE tc.constraint_schema = %s AND tc.constraint_type = 'CHECK'
        """, (database,))
        check_result = cursor.fetchall()
        
        for row in check_result:
            constraint_ddl = f"ALTER TABLE `{row[0]}` ADD CONSTRAINT `{row[1]}` CHECK ({row[2]});"
            ddl_scripts["advanced_constraints"].append({
                "type": "CHECK",
                "table": row[0],
                "name": row[1],
                "check_clause": row[2],
                "enforced": row[3],
                "ddl": constraint_ddl
            })
        
        # Get security policies and row-level security (MySQL doesn't have RLS, but we'll include for completeness)
        try:
            cursor.execute("""
                SELECT user, host, account_locked, password_expired
                FROM mysql.user
                WHERE user != 'mysql.session' AND user != 'mysql.sys' AND user != 'mysql.infoschema'
            """)
            security_result = cursor.fetchall()
            
            for row in security_result:
                security_ddl = f"CREATE USER '{row[0]}'@'{row[1]}';"
                ddl_scripts["security_policies"].append({
                    "user": row[0],
                    "host": row[1],
                    "account_locked": row[2],
                    "password_expired": row[3],
                    "ddl": security_ddl
                })
        except Exception:
            pass
        
        # Get data sampling for testing
        for table in tables[:5]:  # Sample first 5 tables
            try:
                cursor.execute(f"SELECT * FROM `{table}` LIMIT 10")
                sample_data = cursor.fetchall()
                
                # Get column names
                cursor.execute(f"DESCRIBE `{table}`")
                columns_result = cursor.fetchall()
                column_names = [col[0] for col in columns_result]
                
                ddl_scripts["data_sampling"].append({
                    "table": table,
                    "sample_rows": len(sample_data),
                    "columns": column_names,
                    "sample_data": sample_data
                })
            except Exception:
                pass
        
        # Enhanced dependency graph with proper ordering and validation scripts
        dependency_graph = {
            "creation_order": ["types", "domains", "tables", "constraints", "indexes", "computed_columns", "views", "materialized_views", "triggers", "procedures", "functions", "roles", "grants", "security_policies"],
            "deletion_order": ["security_policies", "grants", "roles", "functions", "procedures", "triggers", "materialized_views", "views", "computed_columns", "indexes", "constraints", "tables", "domains", "types"],
            "dependencies": {},
            "validation_scripts": {
                "pre_migration": [],
                "post_migration": [],
                "data_integrity": []
            }
        }
        
        # Add dependencies for each table
        for table in tables:
            dependency_graph["dependencies"][table] = {
                "depends_on": [],
                "referenced_by": []
            }
        
        # Populate dependencies based on foreign keys
        for fk in relationships:
            source_table = fk["source_table"]
            target_table = fk["target_table"]
            if source_table in dependency_graph["dependencies"]:
                dependency_graph["dependencies"][source_table]["depends_on"].append(target_table)
            if target_table in dependency_graph["dependencies"]:
                dependency_graph["dependencies"][target_table]["referenced_by"].append(source_table)
        
        # Add validation scripts
        # Pre-migration validation
        dependency_graph["validation_scripts"]["pre_migration"].append({
            "name": "check_table_counts",
            "description": "Verify table counts before migration",
            "script": f"SELECT table_name, table_rows FROM information_schema.tables WHERE table_schema = '{database}';"
        })
        
        # Data integrity check scripts
        for table in tables:
            dependency_graph["validation_scripts"]["data_integrity"].append({
                "name": f"check_{table}_integrity",
                "description": f"Check data integrity for {table}",
                "script": f"SELECT COUNT(*) as row_count FROM `{table}`;"
            })
        
        # Data type conversion map
        type_mappings = {
            "tinyint": "SMALLINT",
            "smallint": "SMALLINT",
            "mediumint": "INTEGER",
            "int": "INTEGER",
            "bigint": "BIGINT",
            "float": "FLOAT",
            "double": "DOUBLE PRECISION",
            "decimal": "DECIMAL",
            "date": "DATE",
            "datetime": "TIMESTAMP",
            "timestamp": "TIMESTAMP",
            "time": "TIME",
            "year": "SMALLINT",
            "char": "CHAR",
            "varchar": "VARCHAR",
            "text": "TEXT",
            "mediumtext": "TEXT",
            "longtext": "TEXT",
            "binary": "BYTEA",
            "varbinary": "BYTEA",
            "blob": "BYTEA",
            "mediumblob": "BYTEA",
            "longblob": "BYTEA"
        }
        
        # Security and roles with GRANT statements
        security = []
        try:
            cursor.execute("SELECT user, host FROM mysql.user")
            users_result = cursor.fetchall()
            for row in users_result:
                security.append({
                    "user": row[0],
                    "host": row[1],
                    "type": "USER"
                })
        except Exception:
            pass
        
        # Get grants for current database
        try:
            cursor.execute(f"SHOW GRANTS FOR CURRENT_USER()")
            grants_result = cursor.fetchall()
            for row in grants_result:
                ddl_scripts["grants"].append({
                    "grantee": "CURRENT_USER",
                    "privilege": row[0],
                    "type": "GRANT"
                })
        except Exception:
            pass
        
        # Performance and configuration
        performance = {
            "table_stats": [],
            "index_stats": []
        }
        
        # Get table statistics
        try:
            cursor.execute("""
                SELECT table_name, table_rows, avg_row_length, 
                       data_length, index_length, create_time, update_time
                FROM information_schema.tables 
                WHERE table_schema = %s
            """, (database,))
            table_stats_result = cursor.fetchall()
            for row in table_stats_result:
                performance["table_stats"].append({
                    "table": row[0],
                    "rows": row[1],
                    "avg_row_length": row[2],
                    "data_length": row[3],
                    "index_length": row[4],
                    "create_time": str(row[5]) if row[5] else None,
                    "update_time": str(row[6]) if row[6] else None
                })
        except Exception:
            pass
        
        # Get index statistics
        try:
            cursor.execute("""
                SELECT table_name, index_name, cardinality
                FROM information_schema.statistics
                WHERE table_schema = %s
                GROUP BY table_name, index_name, cardinality
            """, (database,))
            index_stats_result = cursor.fetchall()
            for row in index_stats_result:
                performance["index_stats"].append({
                    "table": row[0],
                    "index": row[1],
                    "cardinality": row[2]
                })
        except Exception:
            pass
        
        connection.close()
        
        # Enhanced extraction report
        extraction_report = {
            "tables": len(ddl_scripts["tables"]),
            "views": len(ddl_scripts["views"]),
            "procedures": len(ddl_scripts["procedures"]),
            "functions": len(ddl_scripts["functions"]),
            "triggers": len(ddl_scripts["triggers"]),
            "indexes": len(ddl_scripts["indexes"]),
            "constraints": len(constraints),
            "relationships": len(relationships),
            "sequences": len(ddl_scripts["sequences"]),
            "partition_schemes": len(ddl_scripts["partition_schemes"]),
            "grants": len(ddl_scripts["grants"]),
            "computed_columns": len(ddl_scripts["computed_columns"]),
            "advanced_constraints": len(ddl_scripts["advanced_constraints"]),
            "security_policies": len(ddl_scripts["security_policies"]),
            "data_samples": len(ddl_scripts["data_sampling"])
        }
        
        return {
            "ddl_scripts": ddl_scripts,
            "constraints": constraints,
            "relationships": relationships,
            "indexes": indexes,
            "synonyms": synonyms,
            "jobs": jobs,
            "data_profile": data_profile,
            "dependency_graph": dependency_graph,
            "type_mappings": type_mappings,
            "security": security,
            "performance": performance,
            "extraction_report": extraction_report
        }
    except Exception as e:
        raise Exception(f"MySQL DDL extraction failed: {str(e)}")

def extract_postgresql_ddl(connection_info):
    """Extract comprehensive DDL from PostgreSQL database"""
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
        
        # Extract DDL scripts
        ddl_scripts = {
            "tables": [],
            "views": [],
            "indexes": [],
            "constraints": [],
            "sequences": [],
            "triggers": [],
            "procedures": [],
            "functions": [],
            "materialized_views": [],
            "types": [],
            "domains": [],
            "roles": [],
            "grants": [],
            "partition_schemes": [],
            "storage_configs": [],
            "computed_columns": [],
            "advanced_constraints": [],
            "security_policies": [],
            "data_sampling": []
        }
        
        # Get tables DDL
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
        tables = []
        if tables_result:
            for row in tables_result:
                if row and len(row) > 1:
                    schema_name = str(row[0])
                    table_name = str(row[1])
                    tables.append((schema_name, table_name))
                    
                    # Generate CREATE TABLE DDL
                    table_ddl = f"CREATE TABLE \"{schema_name}\".\"{table_name}\" ();"
                    ddl_scripts["tables"].append({
                        "name": table_name,
                        "schema": schema_name,
                        "ddl": table_ddl,
                        "type": "TABLE"
                    })
        
        # Get views DDL
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
        if views_result:
            for row in views_result:
                if row and len(row) > 2:
                    schema_name = str(row[0])
                    view_name = str(row[1])
                    view_def = str(row[2])
                    views.append((schema_name, view_name))
                    
                    view_ddl = f"CREATE OR REPLACE VIEW \"{schema_name}\".\"{view_name}\" AS {view_def};"
                    ddl_scripts["views"].append({
                        "name": view_name,
                        "schema": schema_name,
                        "ddl": view_ddl,
                        "type": "VIEW"
                    })
        
        # Get functions
        cursor.execute("""
            SELECT
                n.nspname as schema,
                p.proname as name,
                pg_get_function_result(p.oid) as return_type,
                pg_get_functiondef(p.oid) as definition,
                l.lanname as language
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            JOIN pg_language l ON p.prolang = l.oid
            WHERE n.nspname NOT IN ('information_schema', 'pg_catalog')
            AND pg_get_function_result(p.oid) IS NOT NULL
        """)
        functions_result = cursor.fetchall()
        
        for row in functions_result:
            if row and len(row) > 4:
                ddl_scripts["functions"].append({
                    "name": str(row[1]) if row[1] else "",
                    "schema": str(row[0]) if row[0] else "",
                    "ddl": str(row[3]) if row[3] else "",
                    "type": "FUNCTION",
                    "return_type": str(row[2]) if row[2] else "",
                    "language": str(row[4]) if row[4] else ""
                })
        
        # Get sequences
        cursor.execute("""
            SELECT
                schemaname,
                sequencename
            FROM pg_sequences
            WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
            ORDER BY schemaname, sequencename
        """)
        sequences_result = cursor.fetchall()
        
        for row in sequences_result:
            if row and len(row) > 1:
                sequence_ddl = f"CREATE SEQUENCE \"{str(row[0])}\".\"{str(row[1])}\";"
                ddl_scripts["sequences"].append({
                    "name": str(row[1]) if row[1] else "",
                    "schema": str(row[0]) if row[0] else "",
                    "ddl": sequence_ddl,
                    "type": "SEQUENCE"
                })
        
        # Get indexes
        cursor.execute("""
            SELECT
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
            ORDER BY schemaname, tablename, indexname
        """)
        indexes_result = cursor.fetchall()
        
        for row in indexes_result:
            if row and len(row) > 3:
                ddl_scripts["indexes"].append({
                    "schema": str(row[0]) if row[0] else "",
                    "table": str(row[1]) if row[1] else "",
                    "name": str(row[2]) if row[2] else "",
                    "ddl": str(row[3]) if row[3] else "",
                    "unique": "UNIQUE" in str(row[3]),
                    "index_type": "BTREE"
                })
        
        connection.close()
        
        # Create basic extraction report
        extraction_report = {
            "tables": len(ddl_scripts["tables"]),
            "views": len(ddl_scripts["views"]),
            "procedures": 0,
            "functions": len(ddl_scripts["functions"]),
            "triggers": 0,
            "indexes": len(ddl_scripts["indexes"]),
            "constraints": 0,
            "relationships": 0,
            "sequences": len(ddl_scripts["sequences"]),
            "partition_schemes": 0,
            "grants": 0,
            "computed_columns": 0,
            "advanced_constraints": 0,
            "security_policies": 0,
            "data_samples": 0
        }
        
        return {
            "ddl_scripts": ddl_scripts,
            "constraints": [],
            "relationships": [],
            "indexes": ddl_scripts["indexes"],
            "synonyms": [],
            "jobs": [],
            "data_profile": {},
            "dependency_graph": {
                "creation_order": ["types", "domains", "tables", "constraints", "indexes", "views", "materialized_views", "triggers", "procedures", "functions", "roles", "grants"],
                "deletion_order": ["grants", "roles", "functions", "procedures", "triggers", "materialized_views", "views", "indexes", "constraints", "tables", "domains", "types"],
                "dependencies": {}
            },
            "type_mappings": {},
            "security": [],
            "performance": {
                "table_stats": [],
                "index_stats": []
            },
            "extraction_report": extraction_report
        }
    except Exception as e:
        raise Exception(f"PostgreSQL DDL extraction failed: {str(e)}")

def extract_database_ddl(connection_info):
    """Extract database DDL based on database type - FIXED VERSION"""
    db_type = connection_info.get("dbType", "Unknown")
    
    if db_type == "MySQL":
        return extract_mysql_ddl(connection_info)
    elif db_type == "PostgreSQL":
        return extract_postgresql_ddl(connection_info)
    else:
        # For other database types, return helpful error
        return {
            "ddl_scripts": {
                "tables": [],
                "views": [],
                "indexes": [],
                "constraints": [],
                "sequences": [],
                "triggers": [],
                "procedures": [],
                "functions": [],
                "materialized_views": [],
                "types": [],
                "domains": [],
                "roles": [],
                "grants": [],
                "partition_schemes": [],
                "storage_configs": []
            },
            "constraints": [],
            "relationships": [],
            "indexes": [],
            "synonyms": [],
            "jobs": [],
            "data_profile": {},
            "dependency_graph": {
                "creation_order": [],
                "deletion_order": [],
                "dependencies": {}
            },
            "type_mappings": {},
            "security": [],
            "performance": {
                "table_stats": [],
                "index_stats": []
            },
            "extraction_report": {
                "tables": 0,
                "views": 0,
                "procedures": 0,
                "functions": 0,
                "triggers": 0,
                "indexes": 0,
                "constraints": 0,
                "relationships": 0,
                "sequences": 0,
                "partition_schemes": 0,
                "grants": 0
            },
            "error": f"Database type '{db_type}' is not supported. Currently supported: MySQL, PostgreSQL."
        }

def export_extraction_json():
    """Export extraction bundle as JSON"""
    if not os.path.exists("artifacts/extraction_bundle.json"):
        return None
    
    with open("artifacts/extraction_bundle.json", "r") as f:
        data = json.load(f)
    
    return data

def export_extraction_xlsx():
    """Export extraction bundle as Excel"""
    if not os.path.exists("artifacts/extraction_bundle.json"):
        return None
    
    with open("artifacts/extraction_bundle.json", "r") as f:
        data = json.load(f)
    
    # Create Excel file
    excel_filename = "artifacts/extraction_report.xlsx"
    workbook = xlsxwriter.Workbook(excel_filename)
    
    # Summary sheet
    summary_sheet = workbook.add_worksheet("Summary")
    summary_sheet.write(0, 0, "Database Extraction Report - Summary")
    summary_sheet.write(2, 0, "Objects Extracted")
    
    report = data.get("extraction_report", {})
    row = 3
    for key, value in report.items():
        summary_sheet.write(row, 0, key.replace("_", " ").title())
        summary_sheet.write(row, 1, value)
        row += 1
    
    # Tables sheet
    if "ddl_scripts" in data and "tables" in data["ddl_scripts"]:
        tables_sheet = workbook.add_worksheet("Tables")
        tables_sheet.write(0, 0, "Table Name")
        tables_sheet.write(0, 1, "DDL")
        
        for i, table in enumerate(data["ddl_scripts"]["tables"], start=1):
            tables_sheet.write(i, 0, table.get("name", ""))
            tables_sheet.write(i, 1, table.get("ddl", "")[:1000])  # Limit length
    
    # Constraints sheet
    if "constraints" in data:
        constraints_sheet = workbook.add_worksheet("Constraints")
        constraints_sheet.write(0, 0, "Type")
        constraints_sheet.write(0, 1, "Table")
        constraints_sheet.write(0, 2, "Columns")
        constraints_sheet.write(0, 3, "DDL")
        
        for i, constraint in enumerate(data["constraints"], start=1):
            constraints_sheet.write(i, 0, constraint.get("type", ""))
            constraints_sheet.write(i, 1, constraint.get("table", ""))
            constraints_sheet.write(i, 2, ", ".join(constraint.get("columns", [])))
            constraints_sheet.write(i, 3, constraint.get("ddl", "")[:500])  # Limit length
    
    # Triggers sheet
    if "ddl_scripts" in data and "triggers" in data["ddl_scripts"]:
        triggers_sheet = workbook.add_worksheet("Triggers")
        triggers_sheet.write(0, 0, "Trigger Name")
        triggers_sheet.write(0, 1, "Table")
        triggers_sheet.write(0, 2, "Event")
        triggers_sheet.write(0, 3, "Timing")
        triggers_sheet.write(0, 4, "DDL")
        triggers_sheet.write(0, 5, "Target DDL Template")
        
        for i, trigger in enumerate(data["ddl_scripts"]["triggers"], start=1):
            triggers_sheet.write(i, 0, trigger.get("name", ""))
            triggers_sheet.write(i, 1, trigger.get("table", ""))
            triggers_sheet.write(i, 2, trigger.get("event", ""))
            triggers_sheet.write(i, 3, trigger.get("timing", ""))
            triggers_sheet.write(i, 4, trigger.get("ddl", "")[:1000])  # Limit length
            triggers_sheet.write(i, 5, trigger.get("target_ddl_template", "")[:1000])  # Limit length
    
    # Sequences sheet
    if "ddl_scripts" in data and "sequences" in data["ddl_scripts"]:
        sequences_sheet = workbook.add_worksheet("Sequences")
        sequences_sheet.write(0, 0, "Table")
        sequences_sheet.write(0, 1, "Column")
        sequences_sheet.write(0, 2, "DDL")
        sequences_sheet.write(0, 3, "Create Sequence Template")
        sequences_sheet.write(0, 4, "Alter Sequence Template")
        
        for i, sequence in enumerate(data["ddl_scripts"]["sequences"], start=1):
            sequences_sheet.write(i, 0, sequence.get("table", ""))
            sequences_sheet.write(i, 1, sequence.get("column", ""))
            sequences_sheet.write(i, 2, sequence.get("ddl", ""))
            sequences_sheet.write(i, 3, sequence.get("create_sequence_template", ""))
            sequences_sheet.write(i, 4, sequence.get("alter_sequence_template", ""))
    
    # Computed Columns sheet
    if "ddl_scripts" in data and "computed_columns" in data["ddl_scripts"]:
        computed_sheet = workbook.add_worksheet("Computed Columns")
        computed_sheet.write(0, 0, "Table")
        computed_sheet.write(0, 1, "Column")
        computed_sheet.write(0, 2, "Expression")
        computed_sheet.write(0, 3, "DDL")
        
        for i, computed in enumerate(data["ddl_scripts"]["computed_columns"], start=1):
            computed_sheet.write(i, 0, computed.get("table", ""))
            computed_sheet.write(i, 1, computed.get("column", ""))
            computed_sheet.write(i, 2, computed.get("expression", ""))
            computed_sheet.write(i, 3, computed.get("ddl", ""))
    
    # Advanced Constraints sheet
    if "ddl_scripts" in data and "advanced_constraints" in data["ddl_scripts"]:
        adv_constraints_sheet = workbook.add_worksheet("Advanced Constraints")
        adv_constraints_sheet.write(0, 0, "Table")
        adv_constraints_sheet.write(0, 1, "Name")
        adv_constraints_sheet.write(0, 2, "Type")
        adv_constraints_sheet.write(0, 3, "Check Clause")
        adv_constraints_sheet.write(0, 4, "DDL")
        
        for i, constraint in enumerate(data["ddl_scripts"]["advanced_constraints"], start=1):
            adv_constraints_sheet.write(i, 0, constraint.get("table", ""))
            adv_constraints_sheet.write(i, 1, constraint.get("name", ""))
            adv_constraints_sheet.write(i, 2, constraint.get("type", ""))
            adv_constraints_sheet.write(i, 3, constraint.get("check_clause", ""))
            adv_constraints_sheet.write(i, 4, constraint.get("ddl", ""))
    
    workbook.close()
    return excel_filename

def export_extraction_pdf():
    """Export extraction bundle as PDF"""
    if not os.path.exists("artifacts/extraction_bundle.json"):
        return None
    
    with open("artifacts/extraction_bundle.json", "r") as f:
        data = json.load(f)
    
    # Create PDF file
    pdf_filename = "artifacts/extraction_report.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("Strata - Database Extraction Report", styles["Title"])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Summary
    report = data.get("extraction_report", {})
    summary_data = [["Object Type", "Count"]]
    for key, value in report.items():
        summary_data.append([key.replace("_", " ").title(), str(value)])
    
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
    if "ddl_scripts" in data and "tables" in data["ddl_scripts"]:
        tables_header = Paragraph("<b>Tables</b>", styles["Heading2"])
        story.append(tables_header)
        
        for table in data["ddl_scripts"]["tables"][:5]:  # Limit to first 5 tables
            table_name = Paragraph(f"<b>{table.get('name', '')}</b>", styles["Heading3"])
            story.append(table_name)
            
            # Add a preview of the DDL
            ddl_preview = table.get("ddl", "")[:200] + "..." if len(table.get("ddl", "")) > 200 else table.get("ddl", "")
            table_ddl = Paragraph(f"<pre>{ddl_preview}</pre>", styles["Normal"])
            story.append(table_ddl)
            story.append(Spacer(1, 6))
    
    # Triggers section
    if "ddl_scripts" in data and "triggers" in data["ddl_scripts"]:
        triggers_header = Paragraph("<b>Triggers</b>", styles["Heading2"])
        story.append(triggers_header)
        
        for trigger in data["ddl_scripts"]["triggers"][:3]:  # Limit to first 3 triggers
            trigger_name = Paragraph(f"<b>{trigger.get('name', '')}</b> on {trigger.get('table', '')}", styles["Heading3"])
            story.append(trigger_name)
            
            # Add trigger DDL
            ddl_preview = trigger.get("ddl", "")[:300] + "..." if len(trigger.get("ddl", "")) > 300 else trigger.get("ddl", "")
            trigger_ddl = Paragraph(f"<pre>{ddl_preview}</pre>", styles["Normal"])
            story.append(trigger_ddl)
            
            # Add target DDL template
            target_ddl_preview = trigger.get("target_ddl_template", "")[:300] + "..." if len(trigger.get("target_ddl_template", "")) > 300 else trigger.get("target_ddl_template", "")
            target_ddl = Paragraph(f"<i>Target DDL Template:</i><br/><pre>{target_ddl_preview}</pre>", styles["Normal"])
            story.append(target_ddl)
            story.append(Spacer(1, 6))
    
    # Sequences section
    if "ddl_scripts" in data and "sequences" in data["ddl_scripts"]:
        sequences_header = Paragraph("<b>Sequences</b>", styles["Heading2"])
        story.append(sequences_header)
        
        for sequence in data["ddl_scripts"]["sequences"][:3]:  # Limit to first 3 sequences
            sequence_name = Paragraph(f"<b>{sequence.get('table', '')}.{sequence.get('column', '')}</b>", styles["Heading3"])
            story.append(sequence_name)
            
            # Add sequence DDL
            sequence_ddl = Paragraph(f"<pre>{sequence.get('ddl', '')}</pre>", styles["Normal"])
            story.append(sequence_ddl)
            
            # Add templates
            templates = Paragraph(f"<i>Create Template:</i><br/><pre>{sequence.get('create_sequence_template', '')}</pre><br/>" +
                                f"<i>Alter Template:</i><br/><pre>{sequence.get('alter_sequence_template', '')}</pre>", styles["Normal"])
            story.append(templates)
            story.append(Spacer(1, 6))
    
    # Build PDF
    doc.build(story)
    return pdf_filename

async def run_extraction_task():
    """Background task to run the extraction"""
    global extraction_status
    
    # Reset status
    extraction_status = {
        "phase": "Initializing",
        "percent": 0,
        "done": False,
        "results_summary": None,
        "error": None
    }
    
    try:
        # Get session info
        session = get_active_session()
        print(f"Session data: {session}")  # Debug print
        source_db = session.get("source")
        
        if not source_db:
            raise Exception("No source database selected")
        
        # Get full connection details
        connection_info = get_connection_by_id(source_db["id"])
        print(f"Connection info: {connection_info}")  # Debug print
        if not connection_info:
            raise Exception("Source database connection not found")
        
        # Extraction phases
        phases = [
            ("Loading analysis results", 10),
            ("Generating DDL scripts", 30),
            ("Extracting constraints", 50),
            ("Building dependency graph", 70),
            ("Preparing type mappings", 85),
            ("Finalizing extraction", 100)
        ]
        
        for phase, percent in phases[:-1]:  # All phases except the last one
            extraction_status["phase"] = phase
            extraction_status["percent"] = percent
            await asyncio.sleep(0.5)  # Simulate work
        
        # Perform actual DDL extraction
        extraction_status["phase"] = "Generating DDL scripts"
        extraction_status["percent"] = 60
        extraction_bundle = extract_database_ddl(connection_info)
        
        # Final phase
        extraction_status["phase"] = "Finalizing extraction"
        extraction_status["percent"] = 100
        
        # Save to artifacts directory
        os.makedirs("artifacts", exist_ok=True)
        with open("artifacts/extraction_bundle.json", "w") as f:
            json.dump(extraction_bundle, f, indent=2, default=str)
        
        # Update status
        extraction_status["done"] = True
        extraction_status["results_summary"] = {
            "objects_extracted": sum(extraction_bundle["extraction_report"].values()),
            "tables": extraction_bundle["extraction_report"].get("tables", 0),
            "views": extraction_bundle["extraction_report"].get("views", 0),
            "procedures": extraction_bundle["extraction_report"].get("procedures", 0)
        }
        
    except Exception as e:
        print(f"Extraction error: {str(e)}")  # Debug print
        extraction_status["error"] = str(e)
        extraction_status["done"] = True
        extraction_status["percent"] = 100

@router.post("/start", response_model=CommonResponse)
async def start_extraction(background_tasks: BackgroundTasks):
    global extraction_status
    extraction_status["phase"] = "Starting"
    extraction_status["percent"] = 0
    extraction_status["done"] = False
    extraction_status["error"] = None
    
    background_tasks.add_task(run_extraction_task)
    
    return CommonResponse(ok=True, message="Extraction started")

@router.get("/status", response_model=AnalysisStatusResponse)
async def get_extraction_status():
    global extraction_status
    return AnalysisStatusResponse(
        ok=True,
        phase=extraction_status["phase"],
        percent=extraction_status["percent"],
        done=extraction_status["done"],
        resultsSummary=extraction_status["results_summary"],
        error=extraction_status["error"]
    )

@router.get("/data")
async def get_extraction_data():
    """Get extraction data for display in frontend"""
    if not os.path.exists("artifacts/extraction_bundle.json"):
        return {"error": "Extraction data not found"}
    
    with open("artifacts/extraction_bundle.json", "r") as f:
        data = json.load(f)
    
    return data

@router.get("/export/json")
async def export_extraction_json_endpoint():
    """Export extraction bundle as JSON"""
    filename = export_extraction_json()
    if filename is None:
        return {"error": "Extraction report not found"}
    
    return FileResponse(
        filename,
        media_type="application/json",
        filename="extraction_report.json"
    )

@router.get("/export/xlsx")
async def export_extraction_xlsx_endpoint():
    """Export extraction bundle as Excel"""
    filename = export_extraction_xlsx()
    if filename is None:
        return {"error": "Extraction report not found"}
    
    return FileResponse(
        filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="extraction_report.xlsx"
    )

@router.get("/export/pdf")
async def export_extraction_pdf_endpoint():
    """Export extraction bundle as PDF"""
    filename = export_extraction_pdf()
    if filename is None:
        return {"error": "Extraction report not found"}
    
    return FileResponse(
        filename,
        media_type="application/pdf",
        filename="extraction_report.pdf"
    )