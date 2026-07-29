import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from src.db.database import Base

class ParserRun(Base):
    __tablename__ = "parser_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parser_version = Column(String)
    parser_type = Column(String) # CLASSIC, LLM, HYBRID
    model_name = Column(String)
    prompt_version = Column(String)
    temperature = Column(String) # Stored as string to handle potentially missing/complex configs
    json_schema = Column(JSONB)
    run_date = Column(DateTime, default=datetime.utcnow)
    evaluated_corpus = Column(String)
    duration_ms = Column(Integer)
    cost = Column(String)
    status = Column(String)

    predictions = relationship("ClaimParsePrediction", back_populates="run", cascade="all, delete-orphan")
    resolution_runs = relationship("ResolutionRun", back_populates="parser_run", cascade="all, delete-orphan")

class ClaimParsePrediction(Base):
    __tablename__ = "claim_parse_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("parser_runs.id"), nullable=False)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    raw_output = Column(Text)
    structured_output = Column(JSONB)
    is_schema_valid = Column(Boolean)
    validation_errors = Column(Text)
    retry_count = Column(Integer, default=0)
    confidence = Column(String)
    processing_time_ms = Column(Integer)

    run = relationship("ParserRun", back_populates="predictions")
    claim = relationship("Claim")

class RetrievalRun(Base):
    __tablename__ = "retrieval_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    index_version = Column(String)
    lexical_config = Column(String)
    embedding_model = Column(String)
    fusion_method = Column(String)
    reranker_model = Column(String)
    k_value = Column(Integer)
    evaluated_corpus = Column(String)
    metrics = Column(JSONB)

    results = relationship("RetrievalResult", back_populates="run", cascade="all, delete-orphan")
    resolution_runs = relationship("ResolutionRun", back_populates="retrieval_run", cascade="all, delete-orphan")

class RetrievalResult(Base):
    __tablename__ = "retrieval_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("retrieval_runs.id"), nullable=False)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    lexical_rank = Column(Integer)
    vector_rank = Column(Integer)
    fusion_rank = Column(Integer)
    rerank_rank = Column(Integer)
    scores = Column(JSONB)
    match_explanation = Column(Text)

    run = relationship("RetrievalRun", back_populates="results")
    claim = relationship("Claim")
    dataset = relationship("Dataset")

class ResolutionRun(Base):
    __tablename__ = "resolution_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parser_run_id = Column(UUID(as_uuid=True), ForeignKey("parser_runs.id"))
    retrieval_run_id = Column(UUID(as_uuid=True), ForeignKey("retrieval_runs.id"))
    nomenclature_version = Column(String)
    rules_applied = Column(JSONB)
    results = Column(JSONB)
    ambiguities = Column(JSONB)
    automatic_decisions = Column(Integer)
    human_decisions = Column(Integer)

    parser_run = relationship("ParserRun", back_populates="resolution_runs")
    retrieval_run = relationship("RetrievalRun", back_populates="resolution_runs")
