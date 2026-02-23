"""
OAKD - Open Access Knowledge Distiller

Transform research papers and technical documents into structured, verifiable knowledge graphs.
"""

__version__ = "0.1.0"

from .document_parser import DocumentParser
from .claim_extractor import ClaimExtractor
from .citation_linker import CitationLinker
from .confidence_scorer import ConfidenceScorer
from .graph_builder import GraphBuilder
from .pipeline import KnowledgeDistillationPipeline

__all__ = [
    "DocumentParser",
    "ClaimExtractor",
    "CitationLinker",
    "ConfidenceScorer",
    "GraphBuilder",
    "KnowledgeDistillationPipeline",
]
