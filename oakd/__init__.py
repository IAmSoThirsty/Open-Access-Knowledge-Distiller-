"""
OAKD - Open Access Knowledge Distiller

Transform research papers and technical documents into structured, verifiable knowledge graphs.

A production-grade structured knowledge engine with:
- Epistemic stability guarantees
- Security hardening for adversarial environments
- Regulatory compliance controls
- Operational excellence monitoring
"""

__version__ = "1.0.0"

from .document_parser import DocumentParser
from .claim_extractor import ClaimExtractor
from .citation_linker import CitationLinker
from .confidence_scorer import ConfidenceScorer
from .graph_builder import GraphBuilder
from .pipeline import KnowledgeDistillationPipeline

# Epistemic stability modules
from .epistemic_stability import (
    ProvenanceTracker,
    DeterministicProcessor,
    ScoreDriftDetector,
    ProvenanceHash,
    ScoringVersion,
    GraphSchemaVersion,
    CURRENT_SCORING_VERSION,
    CURRENT_GRAPH_SCHEMA
)
from .checkpoint import (
    CheckpointManager,
    IdempotentBatchProcessor,
    PipelineStage,
    StageCheckpoint,
    PipelineExecution
)
from .graph_diff import (
    GraphDiffer,
    SchemaMigrator,
    VersionCompatibilityChecker,
    GraphDiff,
    GraphChange,
    ChangeType
)
from .invariants import (
    InvariantValidator,
    ValidationReport,
    InvariantViolation
)

# Security and compliance modules
from .security import (
    InputValidator,
    AuditLogger,
    RateLimiter,
    DataPrivacyController,
    ResourceLimiter,
    AuditEventType,
    AuditLogEntry,
    SecurityLevel
)
from .compliance import (
    ComplianceController,
    DataMinimizer,
    DataRetentionPolicy,
    ConsentRecord,
    DataSubjectRequest,
    DataCategory,
    ProcessingPurpose,
    DataSubjectRight
)

# Monitoring and operational modules
from .monitoring import (
    MetricsCollector,
    HealthMonitor,
    ResourceMonitor,
    SLATracker,
    AlertManager,
    CircuitBreaker,
    HealthStatus,
    HealthCheck,
    Metric,
    MetricType
)

# Enhanced pipeline
from .epistemic_pipeline import EpistemicPipeline

__all__ = [
    # Core components
    "DocumentParser",
    "ClaimExtractor",
    "CitationLinker",
    "ConfidenceScorer",
    "GraphBuilder",
    "KnowledgeDistillationPipeline",
    # Epistemic stability
    "ProvenanceTracker",
    "DeterministicProcessor",
    "ScoreDriftDetector",
    "ProvenanceHash",
    "ScoringVersion",
    "GraphSchemaVersion",
    "CURRENT_SCORING_VERSION",
    "CURRENT_GRAPH_SCHEMA",
    # Checkpointing
    "CheckpointManager",
    "IdempotentBatchProcessor",
    "PipelineStage",
    "StageCheckpoint",
    "PipelineExecution",
    # Graph diffing
    "GraphDiffer",
    "SchemaMigrator",
    "VersionCompatibilityChecker",
    "GraphDiff",
    "GraphChange",
    "ChangeType",
    # Invariants
    "InvariantValidator",
    "ValidationReport",
    "InvariantViolation",
    # Security
    "InputValidator",
    "AuditLogger",
    "RateLimiter",
    "DataPrivacyController",
    "ResourceLimiter",
    "AuditEventType",
    "AuditLogEntry",
    "SecurityLevel",
    # Compliance
    "ComplianceController",
    "DataMinimizer",
    "DataRetentionPolicy",
    "ConsentRecord",
    "DataSubjectRequest",
    "DataCategory",
    "ProcessingPurpose",
    "DataSubjectRight",
    # Monitoring
    "MetricsCollector",
    "HealthMonitor",
    "ResourceMonitor",
    "SLATracker",
    "AlertManager",
    "CircuitBreaker",
    "HealthStatus",
    "HealthCheck",
    "Metric",
    "MetricType",
    # Enhanced pipeline
    "EpistemicPipeline",
]

