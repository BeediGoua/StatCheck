import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, UniqueConstraint, Index, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
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
class DataflowDimension(Base):
    __tablename__ = "dataflow_dimensions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id = Column(String, nullable=False, index=True)
    dataflow_id = Column(String, nullable=False, index=True)
    dimension_id = Column(String, nullable=False)
    
    canonical_concept = Column(String, nullable=False)
    position = Column(Integer, nullable=False)
    role = Column(String, nullable=False) # SERIES, TIME, MEASURE, ATTRIBUTE
    representation_type = Column(String)
    codelist = Column(String)
    is_mandatory = Column(Boolean, default=True)
    metadata_version = Column(String)
    
    __table_args__ = (
        UniqueConstraint("snapshot_id", "dataflow_id", "dimension_id", name="uq_dataflow_dimension"),
        # Index partiel PostgreSQL : La position n'est unique que pour les dimensions de la clé de série
        Index(
            "uq_dataflow_dim_position", 
            "snapshot_id", "dataflow_id", "position", 
            unique=True, 
            postgresql_where=text("role = 'SERIES'")
        ),
    )
class DataflowModality(Base):
    __tablename__ = "dataflow_modalities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id = Column(String, nullable=False, index=True)
    dataflow_id = Column(String, nullable=False, index=True)
    dimension_id = Column(String, nullable=False, index=True)
    code = Column(String, nullable=False)
    
    # Préservation pour les preuves
    original_label = Column(String, nullable=False)
    normalized_label = Column(String)
    
    parent_code = Column(String)
    hierarchy_level = Column(Integer)
    
    valid_from = Column(DateTime)
    valid_to = Column(DateTime)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("snapshot_id", "dataflow_id", "dimension_id", "code", name="uq_dataflow_modality"),
    )
class DimensionAlias(Base):
    __tablename__ = "dimension_aliases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Périmètres : GLOBAL, CONCEPT, DIMENSION
    scope_type = Column(String, nullable=False) 
    scope_value = Column(String) # Valeur du concept ou ID de la dimension
    
    alias_text = Column(String, nullable=False, index=True)
    target_code = Column(String, nullable=False)
    
    source = Column(String, nullable=False) # MANUAL, LLM, AUTO
    confidence = Column(String)
    
    valid_from = Column(DateTime)
    valid_to = Column(DateTime)
    review_status = Column(String, default="PENDING") # PENDING, APPROVED, REJECTED
    
    __table_args__ = (
        # Permettre plusieurs modalités pour le même alias (ex: 'total' -> 'T', 'total' -> '_T')
        UniqueConstraint("scope_type", "scope_value", "alias_text", "target_code", name="uq_dimension_alias"),
    )

class DimensionDefaultPolicy(Base):
    __tablename__ = "dimension_default_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id = Column(String, nullable=False, index=True)
    dataflow_id = Column(String, nullable=False, index=True)
    dimension_id = Column(String, nullable=False, index=True)
    
    # Types de politiques : SAFE_TOTAL, SOURCE_DEFAULT, NO_DEFAULT
    policy_type = Column(String, nullable=False)
    
    # Code de la modalité visée (ex: '_T' pour TOTAL)
    target_modality_code = Column(String)
    
    justification = Column(String)
    reviewer = Column(String)
    reviewed_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("snapshot_id", "dataflow_id", "dimension_id", name="uq_dimension_policy"),
    )

class AvailableSeriesKey(Base):
    __tablename__ = "available_series_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id = Column(String, nullable=False, index=True)
    dataflow_id = Column(String, nullable=False, index=True)
    
    ordered_key = Column(String, nullable=False) # ex: M.FR.IPC...
    key_hash = Column(String, nullable=False, index=True)
    
    # Valeurs de dimensions stockées en JSONB pour requêtage rapide
    dimensions_json = Column(JSONB, nullable=False)
    
    idbank = Column(String, index=True)
    
    first_period = Column(String)
    last_period = Column(String)
    
    availability_source = Column(String)
    observation_date = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("snapshot_id", "dataflow_id", "ordered_key", name="uq_available_series_key"),
        # Index GIN pour accélérer les requêtes filtrant sur certaines dimensions du JSONB
        Index("ix_series_dimensions_gin", "dimensions_json", postgresql_using="gin"),
    )
