"""
Epistemic Stability Module

Provides deterministic processing, provenance tracking, and versioning guarantees
for the OAKD knowledge engine.

This module ensures:
- Same input → same graph (under same version)
- Complete provenance chains (document → claim → citation → edge)
- Versioned scoring models with backward compatibility
- Graph schema versioning
- Deterministic graph hashing
- Score drift detection
"""

import hashlib
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ProvenanceLevel(Enum):
    """Levels of provenance tracking"""
    DOCUMENT = "document"
    CLAIM = "claim"
    CITATION = "citation"
    EDGE = "edge"
    SCORE = "score"


@dataclass(frozen=True)
class ProvenanceHash:
    """Immutable provenance hash with metadata"""
    hash_value: str  # SHA256 hash
    level: ProvenanceLevel
    version: str  # Semantic version
    timestamp: str  # ISO 8601 timestamp
    inputs: Tuple[str, ...]  # Input hashes that contributed
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'hash': self.hash_value,
            'level': self.level.value,
            'version': self.version,
            'timestamp': self.timestamp,
            'inputs': list(self.inputs),
            'metadata': self.metadata
        }


@dataclass(frozen=True)
class ScoringVersion:
    """Versioned scoring model metadata"""
    version: str  # Semantic version (e.g., "1.0.0")
    algorithm_hash: str  # Hash of scoring algorithm
    features: Tuple[str, ...]  # Feature names used
    weights: Dict[str, float]  # Feature weights
    created_at: str  # ISO 8601 timestamp
    backward_compatible_with: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'version': self.version,
            'algorithm_hash': self.algorithm_hash,
            'features': list(self.features),
            'weights': self.weights,
            'created_at': self.created_at,
            'backward_compatible_with': list(self.backward_compatible_with)
        }


@dataclass(frozen=True)
class GraphSchemaVersion:
    """Versioned graph schema metadata"""
    version: str  # Semantic version
    node_types: Tuple[str, ...]  # Supported node types
    edge_types: Tuple[str, ...]  # Supported edge types
    node_attributes: Dict[str, Tuple[str, ...]]  # Node type -> required attributes
    edge_attributes: Dict[str, Tuple[str, ...]]  # Edge type -> required attributes
    created_at: str  # ISO 8601 timestamp
    migration_from: Optional[str] = None  # Previous version for migration

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'version': self.version,
            'node_types': list(self.node_types),
            'edge_types': list(self.edge_types),
            'node_attributes': {k: list(v) for k, v in self.node_attributes.items()},
            'edge_attributes': {k: list(v) for k, v in self.edge_attributes.items()},
            'created_at': self.created_at,
            'migration_from': self.migration_from
        }


class ProvenanceTracker:
    """
    Tracks provenance chains throughout the pipeline.

    Ensures every claim traces to source, every citation resolves to fragment,
    and every score records feature contributors.
    """

    def __init__(self, system_version: str = "1.0.0"):
        self.system_version = system_version
        self._provenance_chain: Dict[str, ProvenanceHash] = {}
        self._claim_to_document: Dict[str, str] = {}
        self._citation_to_fragment: Dict[str, str] = {}
        self._score_features: Dict[str, Dict[str, float]] = {}

    def hash_document(
        self,
        pdf_path: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> ProvenanceHash:
        """
        Create deterministic hash for document.

        Args:
            pdf_path: Path to PDF file
            content: Extracted text content
            metadata: Document metadata

        Returns:
            ProvenanceHash for document
        """
        # Create deterministic input representation
        hash_input = {
            'pdf_path': pdf_path,
            'content': content,
            'metadata': metadata,
            'version': self.system_version
        }

        # Sort keys for determinism
        canonical = json.dumps(hash_input, sort_keys=True)
        hash_value = hashlib.sha256(canonical.encode('utf-8')).hexdigest()

        prov_hash = ProvenanceHash(
            hash_value=hash_value,
            level=ProvenanceLevel.DOCUMENT,
            version=self.system_version,
            timestamp=datetime.utcnow().isoformat(),
            inputs=(),
            metadata={'pdf_path': pdf_path}
        )

        self._provenance_chain[hash_value] = prov_hash
        return prov_hash

    def hash_claim(
        self,
        claim_text: str,
        document_hash: str,
        section: str,
        page_number: Optional[int],
        context: str
    ) -> ProvenanceHash:
        """
        Create deterministic hash for claim with document provenance.

        Args:
            claim_text: Claim text
            document_hash: Hash of source document
            section: Section name
            page_number: Page number
            context: Surrounding context

        Returns:
            ProvenanceHash for claim

        Raises:
            ValueError: If document_hash not in provenance chain
        """
        if document_hash not in self._provenance_chain:
            raise ValueError(f"Document hash {document_hash} not found in provenance chain")

        # Create deterministic input
        hash_input = {
            'claim_text': claim_text,
            'document_hash': document_hash,
            'section': section,
            'page_number': page_number,
            'context': context,
            'version': self.system_version
        }

        canonical = json.dumps(hash_input, sort_keys=True)
        hash_value = hashlib.sha256(canonical.encode('utf-8')).hexdigest()

        prov_hash = ProvenanceHash(
            hash_value=hash_value,
            level=ProvenanceLevel.CLAIM,
            version=self.system_version,
            timestamp=datetime.utcnow().isoformat(),
            inputs=(document_hash,),
            metadata={
                'section': section,
                'page_number': page_number
            }
        )

        self._provenance_chain[hash_value] = prov_hash
        self._claim_to_document[hash_value] = document_hash
        return prov_hash

    def hash_citation(
        self,
        citation_text: str,
        document_hash: str,
        fragment_location: str
    ) -> ProvenanceHash:
        """
        Create deterministic hash for citation with fragment resolution.

        Args:
            citation_text: Citation text
            document_hash: Hash of source document
            fragment_location: Location of citation in document

        Returns:
            ProvenanceHash for citation
        """
        if document_hash not in self._provenance_chain:
            raise ValueError(f"Document hash {document_hash} not found in provenance chain")

        hash_input = {
            'citation_text': citation_text,
            'document_hash': document_hash,
            'fragment_location': fragment_location,
            'version': self.system_version
        }

        canonical = json.dumps(hash_input, sort_keys=True)
        hash_value = hashlib.sha256(canonical.encode('utf-8')).hexdigest()

        prov_hash = ProvenanceHash(
            hash_value=hash_value,
            level=ProvenanceLevel.CITATION,
            version=self.system_version,
            timestamp=datetime.utcnow().isoformat(),
            inputs=(document_hash,),
            metadata={'fragment_location': fragment_location}
        )

        self._provenance_chain[hash_value] = prov_hash
        self._citation_to_fragment[hash_value] = fragment_location
        return prov_hash

    def hash_edge(
        self,
        source_hash: str,
        target_hash: str,
        edge_type: str,
        weight: float,
        metadata: Dict[str, Any]
    ) -> ProvenanceHash:
        """
        Create deterministic hash for graph edge with provenance.

        Args:
            source_hash: Source node hash
            target_hash: Target node hash
            edge_type: Edge type
            weight: Edge weight
            metadata: Edge metadata

        Returns:
            ProvenanceHash for edge
        """
        if source_hash not in self._provenance_chain:
            raise ValueError(f"Source hash {source_hash} not in provenance chain")
        if target_hash not in self._provenance_chain:
            raise ValueError(f"Target hash {target_hash} not in provenance chain")

        hash_input = {
            'source_hash': source_hash,
            'target_hash': target_hash,
            'edge_type': edge_type,
            'weight': weight,
            'metadata': metadata,
            'version': self.system_version
        }

        canonical = json.dumps(hash_input, sort_keys=True)
        hash_value = hashlib.sha256(canonical.encode('utf-8')).hexdigest()

        prov_hash = ProvenanceHash(
            hash_value=hash_value,
            level=ProvenanceLevel.EDGE,
            version=self.system_version,
            timestamp=datetime.utcnow().isoformat(),
            inputs=(source_hash, target_hash),
            metadata={
                'edge_type': edge_type,
                'weight': weight
            }
        )

        self._provenance_chain[hash_value] = prov_hash
        return prov_hash

    def hash_score(
        self,
        claim_hash: str,
        features: Dict[str, float],
        scoring_version: str
    ) -> ProvenanceHash:
        """
        Create hash for confidence score with feature tracking.

        Args:
            claim_hash: Hash of claim being scored
            features: Feature name -> value mapping
            scoring_version: Version of scoring algorithm

        Returns:
            ProvenanceHash for score
        """
        if claim_hash not in self._provenance_chain:
            raise ValueError(f"Claim hash {claim_hash} not in provenance chain")

        hash_input = {
            'claim_hash': claim_hash,
            'features': features,
            'scoring_version': scoring_version,
            'system_version': self.system_version
        }

        canonical = json.dumps(hash_input, sort_keys=True)
        hash_value = hashlib.sha256(canonical.encode('utf-8')).hexdigest()

        prov_hash = ProvenanceHash(
            hash_value=hash_value,
            level=ProvenanceLevel.SCORE,
            version=self.system_version,
            timestamp=datetime.utcnow().isoformat(),
            inputs=(claim_hash,),
            metadata={
                'features': features,
                'scoring_version': scoring_version
            }
        )

        self._provenance_chain[hash_value] = prov_hash
        self._score_features[hash_value] = features
        return prov_hash

    def verify_claim_traceability(self, claim_hash: str) -> bool:
        """
        Verify claim traces to document.

        Invariant: Every extracted claim must trace to at least one citation
        """
        return claim_hash in self._claim_to_document

    def verify_citation_resolution(self, citation_hash: str) -> bool:
        """
        Verify citation resolves to document fragment.

        Invariant: Every citation must resolve to a document fragment
        """
        return citation_hash in self._citation_to_fragment

    def verify_score_features(self, score_hash: str) -> bool:
        """
        Verify confidence score records feature contributors.

        Invariant: Every confidence score must record feature contributors
        """
        return score_hash in self._score_features

    def get_provenance_chain(self, hash_value: str) -> List[ProvenanceHash]:
        """
        Get complete provenance chain for a hash.

        Returns chain from root document to specified hash.
        """
        if hash_value not in self._provenance_chain:
            return []

        chain = [self._provenance_chain[hash_value]]
        current = self._provenance_chain[hash_value]

        while current.inputs:
            # Traverse up the provenance chain
            parent_hash = current.inputs[0]
            if parent_hash in self._provenance_chain:
                current = self._provenance_chain[parent_hash]
                chain.append(current)
            else:
                break

        return list(reversed(chain))

    def export_provenance(self) -> Dict[str, Any]:
        """Export complete provenance chain for persistence"""
        return {
            'system_version': self.system_version,
            'provenance_chain': {
                h: p.to_dict() for h, p in self._provenance_chain.items()
            },
            'claim_to_document': self._claim_to_document,
            'citation_to_fragment': self._citation_to_fragment,
            'score_features': self._score_features
        }


class DeterministicProcessor:
    """
    Ensures deterministic processing: same input → same graph.

    Handles:
    - Deterministic ordering of collections
    - Stable hashing of objects
    - Version-aware processing
    """

    @staticmethod
    def deterministic_sort_claims(claims: List) -> List:
        """
        Sort claims deterministically by text hash.

        Ensures same claims always appear in same order.
        """
        def claim_key(claim):
            return hashlib.sha256(claim.text.encode('utf-8')).hexdigest()

        return sorted(claims, key=claim_key)

    @staticmethod
    def deterministic_sort_citations(citations: List) -> List:
        """Sort citations deterministically"""
        def citation_key(citation):
            return hashlib.sha256(
                f"{citation.citation_id}:{citation.raw_text}".encode('utf-8')
            ).hexdigest()

        return sorted(citations, key=citation_key)

    @staticmethod
    def compute_graph_hash(graph) -> str:
        """
        Compute deterministic hash of entire graph.

        Args:
            graph: NetworkX graph

        Returns:
            SHA256 hash of graph structure and content
        """
        # Extract nodes and edges in deterministic order
        nodes = sorted(graph.nodes(data=True), key=lambda x: x[0])
        edges = sorted(graph.edges(data=True), key=lambda x: (x[0], x[1]))

        graph_repr = {
            'nodes': [
                {'id': n, 'attrs': dict(sorted(attrs.items()))}
                for n, attrs in nodes
            ],
            'edges': [
                {'source': s, 'target': t, 'attrs': dict(sorted(attrs.items()))}
                for s, t, attrs in edges
            ]
        }

        canonical = json.dumps(graph_repr, sort_keys=True)
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


class ScoreDriftDetector:
    """
    Detects drift in confidence scores between runs.

    Compares scores across versions to detect unexpected changes.
    """

    def __init__(self, tolerance: float = 0.01):
        self.tolerance = tolerance
        self._baseline_scores: Dict[str, float] = {}

    def set_baseline(self, claim_hash: str, score: float):
        """Set baseline score for claim"""
        self._baseline_scores[claim_hash] = score

    def detect_drift(self, claim_hash: str, new_score: float) -> Tuple[bool, float]:
        """
        Detect if score has drifted from baseline.

        Returns:
            (has_drifted, drift_amount)
        """
        if claim_hash not in self._baseline_scores:
            return False, 0.0

        baseline = self._baseline_scores[claim_hash]
        drift = abs(new_score - baseline)
        has_drifted = drift > self.tolerance

        return has_drifted, drift

    def get_drift_report(self) -> Dict[str, Any]:
        """Generate drift detection report"""
        return {
            'tolerance': self.tolerance,
            'baseline_count': len(self._baseline_scores),
            'baseline_scores': self._baseline_scores.copy()
        }


# Current scoring version
CURRENT_SCORING_VERSION = ScoringVersion(
    version="1.0.0",
    algorithm_hash=hashlib.sha256(b"citation:0.5,linguistic:0.3,context:0.2").hexdigest(),
    features=("citation_score", "linguistic_score", "context_score"),
    weights={
        "citation_score": 0.5,
        "linguistic_score": 0.3,
        "context_score": 0.2
    },
    created_at=datetime.utcnow().isoformat(),
    backward_compatible_with=()
)

# Current graph schema version
CURRENT_GRAPH_SCHEMA = GraphSchemaVersion(
    version="1.0.0",
    node_types=("document", "claim", "citation"),
    edge_types=("contains", "supports", "cites"),
    node_attributes={
        "document": ("title", "authors", "num_sections", "num_references"),
        "claim": ("section", "claim_type", "confidence", "page_number"),
        "citation": ("authors", "title", "year", "doi", "url", "format")
    },
    edge_attributes={
        "contains": ("edge_type", "weight"),
        "supports": ("edge_type", "weight", "link_strength"),
        "cites": ("edge_type", "weight")
    },
    created_at=datetime.utcnow().isoformat(),
    migration_from=None
)
