"""
Feast DB MCP server — run SQL and inspect schemas via connection string.

Start (stdio, for Cursor):
    uv run python -m mcp_db_server.server
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_db_server.connections import (
    build_sqlalchemy_url,
    create_db_engine,
    describe_table,
    execute_query,
    list_tables,
)

mcp = FastMCP(
    "feast-db",
    instructions=(
        "Tools to connect to SQL databases using a connection string and database type. "
        "Use list_tables and describe_table to explore schema, then execute_sql for read-only "
        "queries when designing Feast feature views. Never log or commit credentials."
    ),
)


@mcp.tool()
def execute_sql(
    connection_string: str,
    database_type: str,
    sql: str,
    limit: int = 100,
    read_only: bool = True,
) -> str:
    """
    Run a SQL statement against the database.

    Args:
        connection_string: DB URL or shorthand (e.g. user:pass@host:5432/mydb).
        database_type: One of postgres, mysql, sqlite, mssql.
        sql: SQL to execute. When read_only=true (default), only SELECT/WITH/SHOW/etc.
        limit: Max rows returned for SELECT-like queries (default 100).
        read_only: If true, block INSERT/UPDATE/DELETE/DDL (default true).
    """
    url = build_sqlalchemy_url(database_type, connection_string)
    engine = create_db_engine(url)
    try:
        return execute_query(engine, sql, limit=limit, read_only=read_only)
    finally:
        engine.dispose()


@mcp.tool()
def list_database_tables(
    connection_string: str,
    database_type: str,
    schema: str | None = None,
) -> str:
    """
    List tables in the database (all schemas or one schema).

    Args:
        connection_string: DB URL or shorthand.
        database_type: One of postgres, mysql, sqlite, mssql.
        schema: Optional schema name (e.g. public). Omit to list all schemas.
    """
    url = build_sqlalchemy_url(database_type, connection_string)
    engine = create_db_engine(url)
    try:
        return list_tables(engine, schema=schema)
    finally:
        engine.dispose()


@mcp.tool()
def describe_database_table(
    connection_string: str,
    database_type: str,
    table: str,
    schema: str | None = None,
) -> str:
    """
    Describe columns, primary key, and foreign keys for a table.

    Args:
        connection_string: DB URL or shorthand.
        database_type: One of postgres, mysql, sqlite, mssql.
        table: Table name.
        schema: Optional schema (e.g. public). For sqlite, defaults to main.
    """
    url = build_sqlalchemy_url(database_type, connection_string)
    engine = create_db_engine(url)
    try:
        return describe_table(engine, table=table, schema=schema)
    finally:
        engine.dispose()


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
