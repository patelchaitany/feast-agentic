from datetime import timedelta

from feast import Entity, FeatureView, Field, FileSource
from feast.data_format import ParquetFormat
from feast.types import Array, Float32, Float64, Int64, String, ValueType

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

customer = Entity(
    name="customer_id",
    description="Unique customer identifier",
    value_type=ValueType.STRING,
)

document = Entity(
    name="doc_id",
    description="Knowledge-base document chunk identifier",
    value_type=ValueType.INT64,
)

# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------

customer_profile_source = FileSource(
    file_format=ParquetFormat(),
    path="data/customer_profiles.parquet",
    timestamp_field="event_timestamp",
)

customer_profile_realtime_source = FileSource(
    file_format=ParquetFormat(),
    path="data/customer_profiles_realtime.parquet",
    timestamp_field="event_timestamp",
)

knowledge_base_source = FileSource(
    file_format=ParquetFormat(),
    path="data/knowledge_base.parquet",
    timestamp_field="event_timestamp",
)

knowledge_base_v2_source = FileSource(
    file_format=ParquetFormat(),
    path="data/knowledge_base_v2.parquet",
    timestamp_field="event_timestamp",
)

agent_memory_source = FileSource(
    file_format=ParquetFormat(),
    path="data/agent_memory.parquet",
    timestamp_field="event_timestamp",
)

agent_memory_long_term_source = FileSource(
    file_format=ParquetFormat(),
    path="data/agent_memory_long_term.parquet",
    timestamp_field="event_timestamp",
)

# ---------------------------------------------------------------------------
# Feature views — primary
# ---------------------------------------------------------------------------

CUSTOMER_PROFILE_SCHEMA = [
    Field(name="name", dtype=String),
    Field(name="email", dtype=String),
    Field(name="plan_tier", dtype=String),
    Field(name="account_age_days", dtype=Int64),
    Field(name="total_spend", dtype=Float64),
    Field(name="open_tickets", dtype=Int64),
    Field(name="satisfaction_score", dtype=Float64),
]

customer_profile = FeatureView(
    name="customer_profile",
    entities=[customer],
    schema=CUSTOMER_PROFILE_SCHEMA,
    source=customer_profile_source,
    ttl=timedelta(days=1),
)

KNOWLEDGE_BASE_SCHEMA = [
    Field(
        name="vector",
        dtype=Array(Float32),
        vector_index=True,
        vector_search_metric="COSINE",
    ),
    Field(name="title", dtype=String),
    Field(name="content", dtype=String),
    Field(name="category", dtype=String),
]

knowledge_base = FeatureView(
    name="knowledge_base",
    entities=[document],
    schema=KNOWLEDGE_BASE_SCHEMA,
    source=knowledge_base_source,
    ttl=timedelta(days=7),
)

AGENT_MEMORY_SCHEMA = [
    Field(name="last_topic", dtype=String),
    Field(name="last_resolution", dtype=String),
    Field(name="interaction_count", dtype=Int64),
    Field(name="preferences", dtype=String),
    Field(name="open_issue", dtype=String),
]

agent_memory = FeatureView(
    name="agent_memory",
    entities=[customer],
    schema=AGENT_MEMORY_SCHEMA,
    source=agent_memory_source,
    ttl=timedelta(days=30),
)

# ---------------------------------------------------------------------------
# Duplicate feature views — same schema, different names
#
# Real-world motivation:
#   customer_profile_realtime  — fed by a streaming pipeline with tighter TTL
#   knowledge_base_v2          — a re-indexed version of the same corpus
#   agent_memory_long_term     — longer retention for compliance / analytics
# ---------------------------------------------------------------------------

customer_profile_realtime = FeatureView(
    name="customer_profile_realtime",
    entities=[customer],
    schema=CUSTOMER_PROFILE_SCHEMA,
    source=customer_profile_realtime_source,
    ttl=timedelta(hours=1),
)

knowledge_base_v2 = FeatureView(
    name="knowledge_base_v2",
    entities=[document],
    schema=KNOWLEDGE_BASE_SCHEMA,
    source=knowledge_base_v2_source,
    ttl=timedelta(days=14),
)

agent_memory_long_term = FeatureView(
    name="agent_memory_long_term",
    entities=[customer],
    schema=AGENT_MEMORY_SCHEMA,
    source=agent_memory_long_term_source,
    ttl=timedelta(days=365),
)
