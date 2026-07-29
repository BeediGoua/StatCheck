import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.db.database import Base

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    external_id = Column(String, nullable=False, index=True)
    external_type = Column(String) # ex: dataflow
    title_fr = Column(String)
    title_en = Column(String)
    description = Column(String)
    theme = Column(String)
    subtheme = Column(String)
    producer = Column(String)
    geo_coverage = Column(String)
    main_frequency = Column(String)
    main_unit = Column(String)
    doc_url = Column(String)
    data_url = Column(String)
    license = Column(String)
    status = Column(String, default="active") # active, retired, archived
    is_active = Column(Boolean, default=True)
    
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    last_remote_update = Column(DateTime)

    source = relationship("Source", back_populates="datasets")
    aliases = relationship("DatasetAlias", back_populates="dataset", cascade="all, delete-orphan")
    dimensions = relationship("DatasetDimension", back_populates="dataset", cascade="all, delete-orphan")
    series = relationship("Series", back_populates="dataset", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("source_id", "external_type", "external_id", name="uq_dataset_external"),
    )

class DatasetAlias(Base):
    __tablename__ = "dataset_aliases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    alias = Column(String, nullable=False)
    alias_type = Column(String) # ex: synonym, historical_title
    
    dataset = relationship("Dataset", back_populates="aliases")

class DatasetRelation(Base):
    __tablename__ = "dataset_relations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    target_dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    relation_type = Column(String, nullable=False) # ex: replaces, child_of
    confidence_score = Column(String)
    detection_method = Column(String)

    source_dataset = relationship("Dataset", foreign_keys=[source_dataset_id])
    target_dataset = relationship("Dataset", foreign_keys=[target_dataset_id])
