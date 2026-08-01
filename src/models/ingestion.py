import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from src.db.database import Base

class CatalogSnapshot(Base):
    __tablename__ = "catalog_snapshots"

    id = Column(String, primary_key=True) # e.g. "insee-2026-07"
    status = Column(String, nullable=False, default="BUILDING") # BUILDING, VALIDATING, READY, FAILED, STALE
    source_sha256 = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime)
    
    runs = relationship("IngestionRun", back_populates="snapshot")

class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    snapshot_id = Column(String, ForeignKey("catalog_snapshots.id"))
    source_sha256 = Column(String)
    ingestion_type = Column(String) # CATALOG, STRUCTURES, OBSERVATIONS
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    status = Column(String, default="PENDING") # PENDING, RUNNING, SUCCESS, FAILED
    trigger_type = Column(String) # MANUAL, CRON
    
    # Stats
    items_discovered = Column(Integer, default=0)
    items_created = Column(Integer, default=0)
    items_updated = Column(Integer, default=0)
    items_unchanged = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)
    download_size_bytes = Column(Integer, default=0)
    summary_message = Column(Text)

    source = relationship("Source", back_populates="ingestion_runs")
    snapshot = relationship("CatalogSnapshot", back_populates="runs")
    items = relationship("IngestionItem", back_populates="run", cascade="all, delete-orphan")

class IngestionItem(Base):
    __tablename__ = "ingestion_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("ingestion_runs.id"), nullable=False)
    item_type = Column(String, nullable=False) # DATAFLOW, DATASTRUCTURE, CODELIST
    external_id = Column(String, nullable=False)
    current_step = Column(String)
    attempt_count = Column(Integer, default=0)
    status = Column(String, default="PENDING")
    http_status = Column(Integer)
    error_message = Column(Text)
    received_hash = Column(String)
    raw_file_path = Column(String)
    next_retry_at = Column(DateTime)

    run = relationship("IngestionRun", back_populates="items")

class ResourceVersion(Base):
    __tablename__ = "resource_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    resource_type = Column(String, nullable=False)
    external_id = Column(String, nullable=False)
    
    # Les fameux 3 hashs
    raw_hash = Column(String, nullable=False)
    normalized_hash = Column(String)
    business_hash = Column(String)
    
    retrieved_at = Column(DateTime, default=datetime.utcnow)
    remote_published_at = Column(DateTime)
    http_headers = Column(JSONB)
    raw_file_path = Column(String)
    file_size_bytes = Column(Integer)
    mime_type = Column(String)
    run_id = Column(UUID(as_uuid=True), ForeignKey("ingestion_runs.id"))

    source = relationship("Source", back_populates="resource_versions")

class IngestionError(Base):
    __tablename__ = "ingestion_errors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("ingestion_runs.id"), nullable=False)
    step = Column(String)
    category = Column(String)
    exception_type = Column(String)
    message = Column(Text)
    truncated_response = Column(Text)
    is_temporary = Column(Boolean)
    resolution_status = Column(String, default="OPEN")
    created_at = Column(DateTime, default=datetime.utcnow)
