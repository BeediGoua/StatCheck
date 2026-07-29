import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from src.db.database import Base

class Claim(Base):
    __tablename__ = "claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stable_id = Column(String, unique=True, index=True)
    text = Column(Text, nullable=False)
    language = Column(String, default="fr")
    published_at = Column(DateTime)
    collected_at = Column(DateTime, default=datetime.utcnow)
    author = Column(String)
    source_type = Column(String)
    url = Column(String)
    context = Column(Text)
    theme = Column(String)
    difficulty = Column(String)
    is_synthetic = Column(Boolean, default=False)
    annotation_status = Column(String, default="PENDING")
    corpus_version = Column(String)
    paraphrase_group_id = Column(String, index=True)
    event_group_id = Column(String, index=True)
    split_name = Column(String) # TRAIN, VALIDATION, TEST

    annotations = relationship("ClaimAnnotation", back_populates="claim", cascade="all, delete-orphan")
    spans = relationship("ClaimSpan", back_populates="claim", cascade="all, delete-orphan")
    semantics = relationship("ClaimSemantic", back_populates="claim", cascade="all, delete-orphan")
    dataset_judgments = relationship("ClaimDatasetJudgment", back_populates="claim", cascade="all, delete-orphan")
    dimension_judgments = relationship("ClaimDimensionJudgment", back_populates="claim", cascade="all, delete-orphan")
    query_gold = relationship("ClaimQueryGold", back_populates="claim", cascade="all, delete-orphan")

class ClaimAnnotation(Base):
    __tablename__ = "claim_annotations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    schema_version = Column(String)
    annotator_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String)
    comment = Column(Text)
    overall_confidence = Column(String)
    is_validated = Column(Boolean, default=False)
    validator_name = Column(String)

    claim = relationship("Claim", back_populates="annotations")
    spans = relationship("ClaimSpan", back_populates="annotation")

class ClaimSpan(Base):
    __tablename__ = "claim_spans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    annotation_id = Column(UUID(as_uuid=True), ForeignKey("claim_annotations.id"))
    start_pos = Column(Integer)
    end_pos = Column(Integer)
    text = Column(String)
    label = Column(String) # ex: INDICATOR, TIME
    confidence = Column(String)

    claim = relationship("Claim", back_populates="spans")
    annotation = relationship("ClaimAnnotation", back_populates="spans")

class ClaimSemantic(Base):
    __tablename__ = "claim_semantics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    normalized_indicator = Column(String)
    operation = Column(String)
    direction = Column(String)
    value = Column(String)
    unit = Column(String)
    start_period = Column(String)
    end_period = Column(String)
    time_granularity = Column(String)
    territory = Column(String)
    population = Column(String)
    comparison_base = Column(String)
    seasonal_adjustment = Column(String)
    answerability_status = Column(String)
    full_json = Column(JSONB)

    claim = relationship("Claim", back_populates="semantics")

class ClaimDatasetJudgment(Base):
    __tablename__ = "claim_dataset_judgments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"))
    relevance_score = Column(Integer) # 0 to 3

    claim = relationship("Claim", back_populates="dataset_judgments")
    dataset = relationship("Dataset")

class ClaimDimensionJudgment(Base):
    __tablename__ = "claim_dimension_judgments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"))
    dimension_id = Column(UUID(as_uuid=True), ForeignKey("dimensions.id"))
    expected_modality_id = Column(UUID(as_uuid=True), ForeignKey("modalities.id"))
    match_type = Column(String)
    is_mandatory = Column(Boolean)
    acceptable_alternative_id = Column(UUID(as_uuid=True), ForeignKey("modalities.id"))
    justification = Column(Text)
    real_ambiguity = Column(Boolean)

    claim = relationship("Claim", back_populates="dimension_judgments")
    dataset = relationship("Dataset")
    dimension = relationship("Dimension")
    expected_modality = relationship("Modality", foreign_keys=[expected_modality_id])
    acceptable_alternative = relationship("Modality", foreign_keys=[acceptable_alternative_id])

class ClaimQueryGold(Base):
    __tablename__ = "claim_query_gold"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"))
    period = Column(String)
    frequency = Column(String)
    operation = Column(String)
    unit = Column(String)
    expected_transformation = Column(String)
    alternatives = Column(JSONB)
    answerability_verdict = Column(String)

    claim = relationship("Claim", back_populates="query_gold")
    dataset = relationship("Dataset")
