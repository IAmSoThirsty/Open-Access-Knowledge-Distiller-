"""
OAKD - Open Access Knowledge Distiller

Transform research papers and technical documents into structured, verifiable knowledge graphs.

A structured knowledge engine with epistemic stability guarantees.
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
]
