import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Float, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.db.database import Base

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_name = Column(String, nullable=False)
    architecture = Column(String, nullable=False) # e.g. C0, C1, C2, C3
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, default="RUNNING")
    manifest = Column(JSON, nullable=True)
    configuration_hash = Column(String, nullable=True)

    predictions = relationship("EvaluationPrediction", back_populates="run")
    metrics = relationship("EvaluationMetric", back_populates="run")

class EvaluationPrediction(Base):
    __tablename__ = "evaluation_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("evaluation_runs.id"), nullable=False)
    claim_id = Column(UUID(as_uuid=True), nullable=False) # Reference to the claim/affirmation
    attempt_index = Column(Integer, default=1)
    raw_output = Column(JSON, nullable=True)
    canonical_output = Column(JSON, nullable=True)
    processing_time_ms = Column(Integer)
    is_successful = Column(Boolean, default=True)
    error_type = Column(String, nullable=True)

    run = relationship("EvaluationRun", back_populates="predictions")
    field_scores = relationship("EvaluationFieldScore", back_populates="prediction")
    fusion_decisions = relationship("FusionDecision", back_populates="prediction")

    __table_args__ = (
        UniqueConstraint("run_id", "claim_id", "attempt_index", name="uq_eval_pred"),
    )

class EvaluationFieldScore(Base):
    __tablename__ = "evaluation_field_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("evaluation_predictions.id"), nullable=False)
    field_name = Column(String, nullable=False)
    is_exact_match = Column(Boolean, default=False)
    f1_score = Column(Float, nullable=True)
    error_category = Column(String, nullable=True)
    expected_value = Column(JSON, nullable=True)
    predicted_value = Column(JSON, nullable=True)

    prediction = relationship("EvaluationPrediction", back_populates="field_scores")

class FusionDecision(Base):
    __tablename__ = "fusion_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("evaluation_predictions.id"), nullable=False)
    field_name = Column(String, nullable=False)
    selected_origin = Column(String, nullable=False) # BASELINE, LLM
    decision_rule = Column(String, nullable=False)
    baseline_value = Column(JSON, nullable=True)
    llm_value = Column(JSON, nullable=True)
    fusion_value = Column(JSON, nullable=True)
    is_agreement = Column(Boolean, default=False)

    prediction = relationship("EvaluationPrediction", back_populates="fusion_decisions")

class EvaluationMetric(Base):
    __tablename__ = "evaluation_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("evaluation_runs.id"), nullable=False)
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)
    level = Column(String, default="GLOBAL") # GLOBAL, FIELD, CATEGORY
    category = Column(String, nullable=True)

    run = relationship("EvaluationRun", back_populates="metrics")

class GoldAnnotation(Base):
    __tablename__ = "gold_annotations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), nullable=False) # L'unité d'annotation
    dataflow_id = Column(String, nullable=False)
    metadata_snapshot_id = Column(String, nullable=False)
    
    expected_status = Column(String, nullable=False) # FOUND, NOT_FOUND, AMBIGUOUS
    codes_by_dimension = Column(JSON, nullable=True) # {"FREQ": "M", "NATURE": "INDICE"}
    time_window = Column(JSON, nullable=True) # {"start": "2020", "end": "2025"}
    allowed_defaults = Column(JSON, nullable=True) # {"AGE": "TOTAL"}
    forbidden_substitutions = Column(JSON, nullable=True) # {"GEO": ["FRANCE_METRO"]}
    
    ambiguities = Column(String, nullable=True)
    limitations = Column(String, nullable=True)
    annotation_provenance = Column(String, nullable=False) # HUMAN_EXPERT, SYNTHETIC_LLM

    keys = relationship("GoldAnnotationKey", back_populates="annotation", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("claim_id", "dataflow_id", "metadata_snapshot_id", name="uq_gold_annotation"),
    )

class GoldAnnotationKey(Base):
    __tablename__ = "gold_annotation_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    annotation_id = Column(UUID(as_uuid=True), ForeignKey("gold_annotations.id"), nullable=False)
    expected_ordered_key = Column(String, nullable=False) # M.INDICE.FR.TOTAL
    relevance = Column(String, nullable=False, default="EXACT") # EXACT, ACCEPTABLE, INSUFFICIENT

    annotation = relationship("GoldAnnotation", back_populates="keys")
