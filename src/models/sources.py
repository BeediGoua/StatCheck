import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.db.database import Base

class Source(Base):
    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False, index=True) # ex: INSEE_BDM
    name = Column(String, nullable=False)
    source_type = Column(String) # ex: API_SDMX
    base_url = Column(String)
    main_format = Column(String)
    protocol_version = Column(String)
    rate_limit = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_checked_at = Column(DateTime)

    endpoints = relationship("SourceEndpoint", back_populates="source", cascade="all, delete-orphan")
    datasets = relationship("Dataset", back_populates="source")
    ingestion_runs = relationship("IngestionRun", back_populates="source")
    resource_versions = relationship("ResourceVersion", back_populates="source")

class SourceEndpoint(Base):
    __tablename__ = "source_endpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    endpoint_type = Column(String, nullable=False) # ex: DATAFLOW, DATASTRUCTURE
    url_template = Column(String, nullable=False)
    expected_format = Column(String)
    http_method = Column(String, default="GET")
    supported_parameters = Column(String) # On peut utiliser du JSONB si on veut
    is_active = Column(Boolean, default=True)

    source = relationship("Source", back_populates="endpoints")
