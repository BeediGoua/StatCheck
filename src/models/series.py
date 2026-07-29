import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, UniqueConstraint, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from src.db.database import Base

class Series(Base):
    __tablename__ = "series"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    external_id = Column(String, nullable=False, index=True) # idbank
    title = Column(String)
    canonical_key = Column(String) # Clé SDMX complète
    frequency = Column(String)
    unit = Column(String)
    unit_multiplier = Column(Integer)
    decimals = Column(Integer)
    base_period = Column(String)
    first_period = Column(String)
    last_period = Column(String)
    last_updated_at = Column(DateTime)
    status = Column(String, default="active")
    
    # Pour la recherche rapide
    dimensions_json = Column(JSONB)

    dataset = relationship("Dataset", back_populates="series")
    dimension_values = relationship("SeriesDimensionValue", back_populates="series", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("dataset_id", "external_id", name="uq_series_external"),
    )

class SeriesDimensionValue(Base):
    __tablename__ = "series_dimension_values"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    series_id = Column(UUID(as_uuid=True), ForeignKey("series.id"), nullable=False)
    dimension_id = Column(UUID(as_uuid=True), ForeignKey("dimensions.id"), nullable=False)
    modality_id = Column(UUID(as_uuid=True), ForeignKey("modalities.id"), nullable=False)

    series = relationship("Series", back_populates="dimension_values")
    dimension = relationship("Dimension")
    modality = relationship("Modality")

    __table_args__ = (
        UniqueConstraint("series_id", "dimension_id", name="uq_series_dim"),
    )
