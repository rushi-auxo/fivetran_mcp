import os
import psycopg2
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
from fastmcp import FastMCP

# ─── Load environment variables ───────────────────────────────
load_dotenv()
FIVETRAN_API_KEY = os.getenv("FIVETRAN_API_KEY")
FIVETRAN_API_SECRET = os.getenv("FIVETRAN_API_SECRET")

if FIVETRAN_API_KEY is None or FIVETRAN_API_SECRET is None:
    raise ValueError("FIVETRAN_API_KEY and FIVETRAN_API_SECRET must be set in environment variables.")

# ─── Fivetran API setup ───────────────────────────────────────
BASE_URL = "https://api.fivetran.com/v1/connectors"
auth = HTTPBasicAuth(FIVETRAN_API_KEY, FIVETRAN_API_SECRET)
headers = {"Content-Type": "application/json; version=2"}

# ─── Init MCP server ─────────────────────────────────────────
mcp = FastMCP("My MCP Server")

# ─── PostgreSQL DDL Extraction Tool ─────────────────────────
@mcp.tool()
def get_postgres_dml(schema_name: str) -> str:
    """
    Extract all DML/DDL for a given PostgreSQL schema, including materialized views and indexes.

    Args:
        schema_name (str): Name of the PostgreSQL schema to extract DDL from.

    Returns:
        str: Complete DDL statements as a formatted string.
    """
    pg_connection = psycopg2.connect(
        host='databaseforpostgresql.postgres.database.azure.com',
        database='postgres',
        user='Administratorpostgrssql',
        password='Welcome@123',
        port=5432
    )

    if pg_connection is None:
        raise RuntimeError("No database connection set. Call set_pg_connection() first.")

    if not schema_name or not schema_name.strip():
        raise ValueError("schema_name cannot be empty")

    cur = pg_connection.cursor()
    ddl_statements = []

    try:
        cur.execute("""
            SELECT c.relname,
                   pg_get_viewdef(c.oid)
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind = 'm'
            AND n.nspname = %s
            ORDER BY c.relname
        """, (schema_name,))

        matviews = cur.fetchall()

        for matview_name, definition in matviews:
            clean_definition = definition.strip().rstrip(';')
            matview_ddl = f'CREATE MATERIALIZED VIEW "{schema_name}"."{matview_name}" AS\n{clean_definition};'
            ddl_statements.append(matview_ddl)

            # Indexes
            cur.execute("""
                SELECT 'CREATE' || CASE WHEN ix.indisunique THEN ' UNIQUE' ELSE '' END ||
                       ' INDEX "' || i.relname || '" ON "' || n.nspname || '"."' || t.relname || 
                       '" (' || string_agg('"' || a.attname || '"', ', ' ORDER BY c.ordinality) || ');'
                FROM pg_class t
                JOIN pg_namespace n ON n.oid = t.relnamespace
                JOIN pg_index ix ON t.oid = ix.indrelid
                JOIN pg_class i ON i.oid = ix.indexrelid
                JOIN unnest(ix.indkey) WITH ORDINALITY c(attnum, ordinality) ON true
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = c.attnum
                WHERE n.nspname = %s AND t.relname = %s AND t.relkind = 'm'
                GROUP BY n.nspname, t.relname, i.relname, ix.indisunique
            """, (schema_name, matview_name))

            for idx in cur.fetchall():
                ddl_statements.append(idx[0])

        return '\n\n'.join(ddl_statements)

    finally:
        cur.close()
        pg_connection.close()

# ---------------- RUN ----------------
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
