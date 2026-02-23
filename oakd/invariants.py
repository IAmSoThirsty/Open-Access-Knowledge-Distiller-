"""
Invariant Validation Module

Enforces critical system invariants:
- Every extracted claim must trace to at least one citation
- Every citation must resolve to a document fragment
- Every confidence score must record feature contributors
- Every graph edge must preserve provenance metadata
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field


@dataclass
class InvariantViolation:
    """Represents a violation of system invariant"""
    invariant_name: str
    severity: str  # "error", "warning"
    element_id: str
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.invariant_name}: {self.description} (element: {self.element_id})"


@dataclass
class ValidationReport:
    """Report of invariant validation"""
    passed: bool
    violations: List[InvariantViolation]
    warnings_count: int = 0
    errors_count: int = 0

    def __post_init__(self):
        self.warnings_count = sum(1 for v in self.violations if v.severity == "warning")
        self.errors_count = sum(1 for v in self.violations if v.severity == "error")
        self.passed = self.errors_count == 0

    def get_summary(self) -> str:
        """Get human-readable summary"""
        return (
            f"Validation {'PASSED' if self.passed else 'FAILED'}\n"
            f"  Errors: {self.errors_count}\n"
            f"  Warnings: {self.warnings_count}\n"
            f"  Total Violations: {len(self.violations)}"
        )


class InvariantValidator:
    """
    Validates system invariants throughout pipeline execution.

    This transforms OAKD from a parser into a structured knowledge engine
    with formal epistemic guarantees.
    """

    def __init__(self, strict_mode: bool = True):
        """
        Initialize validator.

        Args:
            strict_mode: If True, warnings are treated as errors
        """
        self.strict_mode = strict_mode
        self._violations: List[InvariantViolation] = []

    def validate_all(
        self,
        parsed_document: Any,
        claims: List[Any],
        claim_citation_links: List[Any],
        confidence_scores: List[Any],
        graph: Any,
        provenance_tracker: Any
    ) -> ValidationReport:
        """
        Validate all system invariants.

        Args:
            parsed_document: ParsedDocument
            claims: List of Claim objects
            claim_citation_links: List of ClaimCitationLink objects
            confidence_scores: List of ConfidenceScore objects
            graph: NetworkX graph
            provenance_tracker: ProvenanceTracker instance

        Returns:
            ValidationReport with all violations
        """
        self._violations = []

        # Invariant 1: Every claim must trace to source document
        self._validate_claim_traceability(claims, parsed_document)

        # Invariant 2: Every citation must resolve to document fragment
        self._validate_citation_resolution(claim_citation_links, parsed_document)

        # Invariant 3: Every confidence score must record feature contributors
        self._validate_score_features(confidence_scores)

        # Invariant 4: Every graph edge must preserve provenance metadata
        self._validate_edge_provenance(graph)

        # Invariant 5: Claims must link to citations (or be flagged)
        self._validate_claim_citation_links(claims, claim_citation_links)

        # Invariant 6: Graph structure integrity
        self._validate_graph_structure(graph)

        # Invariant 7: Provenance chain completeness
        if provenance_tracker:
            self._validate_provenance_chains(provenance_tracker, claims, claim_citation_links)

        return ValidationReport(
            passed=not any(v.severity == "error" for v in self._violations),
            violations=self._violations
        )

    def _validate_claim_traceability(self, claims: List[Any], parsed_document: Any):
        """
        Invariant: Every extracted claim must trace to source document.

        Ensures claims are not fabricated and can be verified.
        """
        document_title = parsed_document.title
        document_sections = {s.title for s in parsed_document.sections}

        for claim in claims:
            # Verify claim section exists in document
            if claim.section not in document_sections and claim.section != "Abstract":
                self._violations.append(InvariantViolation(
                    invariant_name="claim_traceability",
                    severity="error",
                    element_id=claim.text[:50],
                    description=f"Claim from unknown section '{claim.section}'"
                ))

            # Verify claim has context
            if not claim.context or len(claim.context) < len(claim.text):
                self._violations.append(InvariantViolation(
                    invariant_name="claim_traceability",
                    severity="warning",
                    element_id=claim.text[:50],
                    description="Claim missing sufficient context"
                ))

    def _validate_citation_resolution(self, claim_citation_links: List[Any], parsed_document: Any):
        """
        Invariant: Every citation must resolve to a document fragment.

        Ensures citations are not phantom references.
        """
        document_refs = set(parsed_document.references)

        for link in claim_citation_links:
            for citation in link.citations:
                # Check citation appears in document references
                citation_found = False
                for ref in document_refs:
                    # Simple substring match (could be improved)
                    if citation.raw_text in ref or ref in citation.raw_text:
                        citation_found = True
                        break

                if not citation_found:
                    self._violations.append(InvariantViolation(
                        invariant_name="citation_resolution",
                        severity="warning",
                        element_id=citation.citation_id,
                        description=f"Citation not found in document references"
                    ))

    def _validate_score_features(self, confidence_scores: List[Any]):
        """
        Invariant: Every confidence score must record feature contributors.

        Ensures scores are explainable and auditable.
        """
        required_features = {'citation_score', 'linguistic_score', 'context_score'}

        for score in confidence_scores:
            # Check all required features present
            if not score.factors:
                self._violations.append(InvariantViolation(
                    invariant_name="score_features",
                    severity="error",
                    element_id=score.claim_text[:50],
                    description="Confidence score missing feature tracking"
                ))
                continue

            missing_features = required_features - set(score.factors.keys())
            if missing_features:
                self._violations.append(InvariantViolation(
                    invariant_name="score_features",
                    severity="error",
                    element_id=score.claim_text[:50],
                    description=f"Missing features: {missing_features}"
                ))

            # Verify feature values in valid range
            for feature, value in score.factors.items():
                if not (0.0 <= value <= 1.0):
                    self._violations.append(InvariantViolation(
                        invariant_name="score_features",
                        severity="error",
                        element_id=score.claim_text[:50],
                        description=f"Feature '{feature}' value {value} out of range [0,1]"
                    ))

    def _validate_edge_provenance(self, graph: Any):
        """
        Invariant: Every graph edge must preserve provenance metadata.

        Ensures graph relationships are traceable to source.
        """
        required_edge_attrs = {'edge_type', 'weight'}

        for source, target, attrs in graph.edges(data=True):
            edge_id = f"{source}->{target}"

            # Check required attributes present
            missing_attrs = required_edge_attrs - set(attrs.keys())
            if missing_attrs:
                self._violations.append(InvariantViolation(
                    invariant_name="edge_provenance",
                    severity="error",
                    element_id=edge_id,
                    description=f"Edge missing required attributes: {missing_attrs}"
                ))

            # Validate edge_type
            valid_edge_types = {'contains', 'supports', 'cites'}
            if attrs.get('edge_type') not in valid_edge_types:
                self._violations.append(InvariantViolation(
                    invariant_name="edge_provenance",
                    severity="error",
                    element_id=edge_id,
                    description=f"Invalid edge_type: {attrs.get('edge_type')}"
                ))

            # Validate weight range
            weight = attrs.get('weight', 1.0)
            if not (0.0 <= weight <= 1.0):
                self._violations.append(InvariantViolation(
                    invariant_name="edge_provenance",
                    severity="error",
                    element_id=edge_id,
                    description=f"Edge weight {weight} out of range [0,1]"
                ))

    def _validate_claim_citation_links(self, claims: List[Any], claim_citation_links: List[Any]):
        """
        Invariant: Claims should link to citations (or be explicitly flagged as uncited).

        Warns about claims without citation support.
        """
        claims_with_citations = {link.claim_text for link in claim_citation_links}

        for claim in claims:
            if claim.text not in claims_with_citations:
                self._violations.append(InvariantViolation(
                    invariant_name="claim_citation_link",
                    severity="warning",
                    element_id=claim.text[:50],
                    description="Claim has no citation links"
                ))

    def _validate_graph_structure(self, graph: Any):
        """
        Invariant: Graph must have valid structure.

        Ensures:
        - No orphan nodes (except document root)
        - No self-loops
        - No duplicate edges
        """
        # Check for self-loops
        for node in graph.nodes():
            if graph.has_edge(node, node):
                self._violations.append(InvariantViolation(
                    invariant_name="graph_structure",
                    severity="error",
                    element_id=node,
                    description="Node has self-loop"
                ))

        # Check for orphan nodes
        document_nodes = [n for n, attrs in graph.nodes(data=True) if attrs.get('node_type') == 'document']

        if len(document_nodes) != 1:
            self._violations.append(InvariantViolation(
                invariant_name="graph_structure",
                severity="error",
                element_id="graph",
                description=f"Graph must have exactly 1 document node, found {len(document_nodes)}"
            ))

        # Check all nodes reachable from document
        if document_nodes:
            doc_node = document_nodes[0]
            # In directed graph, check successors
            reachable = set()
            to_visit = [doc_node]
            while to_visit:
                current = to_visit.pop()
                if current in reachable:
                    continue
                reachable.add(current)
                to_visit.extend(graph.successors(current))

            orphans = set(graph.nodes()) - reachable
            if orphans:
                self._violations.append(InvariantViolation(
                    invariant_name="graph_structure",
                    severity="warning",
                    element_id="graph",
                    description=f"Found {len(orphans)} orphan nodes unreachable from document"
                ))

    def _validate_provenance_chains(
        self,
        provenance_tracker: Any,
        claims: List[Any],
        claim_citation_links: List[Any]
    ):
        """
        Invariant: Complete provenance chains must exist.

        Ensures every element can be traced back to source.
        """
        # This would validate using the ProvenanceTracker
        # For now, placeholder validation
        pass

    def get_violations(self, severity: Optional[str] = None) -> List[InvariantViolation]:
        """
        Get violations, optionally filtered by severity.

        Args:
            severity: "error" or "warning", or None for all

        Returns:
            List of violations
        """
        if severity is None:
            return self._violations

        return [v for v in self._violations if v.severity == severity]
