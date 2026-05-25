"""Database connection helpers for the feast-db MCP server."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import quote_plus

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

SUPPORTED_DATABASE_TYPES = frozenset(
    {
        "postgres",
        "postgresql",
        "mysql",
        "sqlite",
        "mssql",
        "sqlserver",
    }
)

_DIALECT_ALIASES = {
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "mysql": "mysql",
    "sqlite": "sqlite",
    "mssql": "mssql",
    "sqlserver": "mssql",
}

_DRIVER_BY_DIALECT = {
    "postgresql": "postgresql+psycopg",
    "mysql": "mysql+pymysql",
    "sqlite": "sqlite",
    "mssql": "mssql+pymssql",
}

_READ_ONLY_PREFIXES = (
    "SELECT",
    "WITH",
    "SHOW",
    "DESCRIBE",
    "DESC",
    "EXPLAIN",
    "PRAGMA",
)


def normalize_database_type(database_type: str) -> str:
    key = database_type.strip().lower()
    if key not in _DIALECT_ALIASES:
        supported = ", ".join(sorted(SUPPORTED_DATABASE_TYPES))
        raise ValueError(
            f"Unsupported database_type={database_type!r}. Supported: {supported}"
        )
    return _DIALECT_ALIASES[key]


def build_sqlalchemy_url(database_type: str, connection_string: str) -> str:
    """Build a SQLAlchemy URL from database type and a connection string."""
    dialect = normalize_database_type(database_type)
    raw = connection_string.strip()

    if "://" in raw:
        return raw

    driver = _DRIVER_BY_DIALECT[dialect]

    if dialect == "sqlite":
        if raw.startswith("sqlite:"):
            return raw
        # Absolute paths need four slashes: sqlite:////var/folders/.../db.sqlite
        if raw.startswith("/"):
            return f"{driver}:////{raw.lstrip('/')}"
        return f"{driver}:///{raw}"

    if dialect == "postgresql":
        return f"{driver}://{raw}"

    if dialect == "mysql":
        return f"{driver}://{raw}"

    if dialect == "mssql":
        # user:pass@host:port/db or host:port;database=db;user=u;password=p
        if "@" in raw or ";" in raw:
            return f"{driver}://{raw}"
        return f"{driver}://{quote_plus(raw)}"

    raise ValueError(f"Cannot build URL for dialect={dialect}")


def _strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"--[^\n]*", "", sql)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    return sql.strip()


def assert_read_only_sql(sql: str) -> None:
    cleaned = _strip_sql_comments(sql)
    if not cleaned:
        raise ValueError("SQL query is empty.")
    first = cleaned.split(None, 1)[0].upper()
    if first not in _READ_ONLY_PREFIXES:
        raise ValueError(
            f"Only read-only queries are allowed (got {first!r}). "
            "Allowed prefixes: SELECT, WITH, SHOW, DESCRIBE, EXPLAIN, PRAGMA. "
            "Set read_only=false to run writes (use with caution)."
        )


def create_db_engine(url: str) -> Engine:
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=1,
        max_overflow=0,
    )


def rows_to_json(rows: list[dict[str, Any]], *, truncated: bool) -> str:
    payload = {
        "row_count": len(rows),
        "truncated": truncated,
        "rows": rows,
    }
    return json.dumps(payload, indent=2, default=str)


def execute_query(
    engine: Engine,
    sql: str,
    *,
    limit: int,
    read_only: bool,
) -> str:
    if read_only:
        assert_read_only_sql(sql)

    cleaned = _strip_sql_comments(sql)
    is_select_like = cleaned.split(None, 1)[0].upper() in _READ_ONLY_PREFIXES

    with engine.connect() as conn:
        if is_select_like and "LIMIT" not in cleaned.upper():
            sql_to_run = f"{sql.rstrip().rstrip(';')} LIMIT {int(limit)}"
        else:
            sql_to_run = sql

        result = conn.execute(text(sql_to_run))

        if not result.returns_rows:
            conn.commit()
            return json.dumps(
                {
                    "row_count": result.rowcount,
                    "message": "Query executed (no result rows).",
                },
                indent=2,
            )

        columns = list(result.keys())
        fetched = result.fetchmany(limit + 1)
        truncated = len(fetched) > limit
        if truncated:
            fetched = fetched[:limit]

        rows = [dict(zip(columns, row)) for row in fetched]
        return rows_to_json(rows, truncated=truncated)


def list_tables(engine: Engine, schema: str | None = None) -> str:
    inspector = inspect(engine)
    dialect = engine.dialect.name

    if dialect == "sqlite":
        tables = inspector.get_table_names()
        payload = {"schema": "main", "tables": sorted(tables)}
        return json.dumps(payload, indent=2)

    schemas = [schema] if schema else inspector.get_schema_names()
    tables_by_schema: dict[str, list[str]] = {}
    for sch in schemas:
        if sch in ("information_schema", "pg_catalog", "pg_toast"):
            continue
        try:
            names = inspector.get_table_names(schema=sch)
        except SQLAlchemyError:
            continue
        if names:
            tables_by_schema[sch] = sorted(names)

    return json.dumps({"schemas": tables_by_schema}, indent=2)


def describe_table(engine: Engine, table: str, schema: str | None = None) -> str:
    inspector = inspect(engine)
    dialect = engine.dialect.name

    if dialect == "sqlite" and schema is None:
        schema = "main"

    columns = inspector.get_columns(table, schema=schema)
    pk = inspector.get_pk_constraint(table, schema=schema)
    fks = inspector.get_foreign_keys(table, schema=schema)

    simplified_columns = [
        {
            "name": col["name"],
            "type": str(col["type"]),
            "nullable": col.get("nullable"),
            "default": col.get("default"),
        }
        for col in columns
    ]

    payload = {
        "table": table,
        "schema": schema,
        "columns": simplified_columns,
        "primary_key": pk.get("constrained_columns", []),
        "foreign_keys": [
            {
                "columns": fk.get("constrained_columns", []),
                "referred_table": fk.get("referred_table"),
                "referred_columns": fk.get("referred_columns", []),
            }
            for fk in fks
        ],
    }
    return json.dumps(payload, indent=2, default=str)
