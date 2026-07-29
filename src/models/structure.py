import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.db.database import Base

class Dimension(Base):
    __tablename__ = "dimensions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String, unique=True, nullable=False, index=True) # canonique, ex: SEXE
    label_fr = Column(String)
    label_en = Column(String)
    description = Column(String)
    semantic_role = Column(String) # temps, territoire, mesure, etc.
    logical_type = Column(String)
    is_temporal = Column(Boolean, default=False)
    is_geographical = Column(Boolean, default=False)
    display_order = Column(Integer)
    is_active = Column(Boolean, default=True)

    dataset_dimensions = relationship("DatasetDimension", back_populates="dimension")
    modalities = relationship("Modality", back_populates="dimension")

class Modality(Base):
    __tablename__ = "modalities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dimension_id = Column(UUID(as_uuid=True), ForeignKey("dimensions.id"), nullable=False)
    code = Column(String, nullable=False, index=True)
    label_fr = Column(String)
    label_en = Column(String)
    description = Column(String)
    parent_code = Column(String)
    hierarchy_level = Column(Integer)
    is_active = Column(Boolean, default=True)

    dimension = relationship("Dimension", back_populates="modalities")

    __table_args__ = (
        UniqueConstraint("dimension_id", "code", name="uq_modality_code"),
    )

class DatasetDimension(Base):
    __tablename__ = "dataset_dimensions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    dimension_id = Column(UUID(as_uuid=True), ForeignKey("dimensions.id"), nullable=False)
    position = Column(Integer) # Position dans la clé SDMX
    is_mandatory = Column(Boolean, default=True)
    external_codelist = Column(String)
    modality_count = Column(Integer, default=0)
    display_order = Column(Integer)

    dataset = relationship("Dataset", back_populates="dimensions")
    dimension = relationship("Dimension", back_populates="dataset_dimensions")
    allowed_modalities = relationship("DatasetDimensionModality", back_populates="dataset_dimension", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("dataset_id", "dimension_id", name="uq_dataset_dimension"),
        UniqueConstraint("dataset_id", "position", name="uq_dataset_dimension_position"),
    )

class DatasetDimensionModality(Base):
    __tablename__ = "dataset_dimension_modalities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_dimension_id = Column(UUID(as_uuid=True), ForeignKey("dataset_dimensions.id"), nullable=False)
    modality_id = Column(UUID(as_uuid=True), ForeignKey("modalities.id"), nullable=False)
    display_order = Column(Integer)
    is_active = Column(Boolean, default=True)

    dataset_dimension = relationship("DatasetDimension", back_populates="allowed_modalities")
    modality = relationship("Modality")

    __table_args__ = (
        UniqueConstraint("dataset_dimension_id", "modality_id", name="uq_dataset_dim_modality"),
    )
