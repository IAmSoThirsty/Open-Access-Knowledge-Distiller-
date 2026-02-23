"""
OAKD Interface Contracts

This module defines all formal interface contracts for the OAKD system.
These interfaces serve as the canonical specification for component interactions.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple, Iterator
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# Enumerations
# ============================================================================

class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class GraphFormat(Enum):
    """Graph export format enumeration"""
    GEXF = "gexf"
    GRAPHML = "graphml"
    JSON = "json"
    GML = "gml"


class ClaimType(Enum):
    """Claim type enumeration"""
    ASSERTION = "assertion"
    FINDING = "finding"
    HYPOTHESIS = "hypothesis"


class CitationFormat(Enum):
    """Citation format enumeration"""
    APA = "APA"
    MLA = "MLA"
    CHICAGO = "Chicago"
    UNKNOWN = "unknown"


# ============================================================================
# Layer 3: Domain Layer Interfaces
# ============================================================================

class IDocumentParser(ABC):
    """
    Document parser interface contract.

    Responsible for parsing PDF documents into structured representations.
    """

    @abstractmethod
    def parse(self, pdf_path: str):
        """
        Parse PDF into structured document.

        Args:
            pdf_path: Absolute path to PDF file

        Returns:
            ParsedDocument with structured content

        Raises:
            FileNotFoundError: PDF file not found
            PermissionError: Insufficient permissions
            ParseError: Document parsing failed
        """
        pass

    @abstractmethod
    def supports_format(self, file_path: str) -> bool:
        """
        Check if parser supports file format.

        Args:
            file_path: Path to file

        Returns:
            True if format is supported
        """
        pass


class ITextExtractor(ABC):
    """Interface for extracting raw text from PDFs"""

    @abstractmethod
    def extract_text(self, pdf_document, page_range: Optional[Tuple[int, int]] = None) -> List[Tuple[int, str]]:
        """
        Extract text from PDF pages.

        Args:
            pdf_document: PDF document handle
            page_range: Optional (start, end) page range

        Returns:
            List of (page_number, text) tuples

        Raises:
            ExtractionError: Text extraction failed
        """
        pass


class ITitleExtractor(ABC):
    """Interface for extracting document title"""

    @abstractmethod
    def extract_title(self, page_texts: List[Tuple[int, str]]) -> str:
        """
        Extract document title from first page.

        Args:
            page_texts: List of (page_number, text) tuples

        Returns:
            Title string

        Raises:
            ExtractionError: Title extraction failed
        """
        pass


class IAbstractExtractor(ABC):
    """Interface for extracting document abstract"""

    @abstractmethod
    def extract_abstract(self, full_text: str) -> str:
        """
        Extract abstract section from document.

        Args:
            full_text: Full document text

        Returns:
            Abstract string (empty if not found)

        Raises:
            ExtractionError: Abstract extraction failed
        """
        pass


class ISectionExtractor(ABC):
    """Interface for extracting document sections"""

    @abstractmethod
    def extract_sections(self, page_texts: List[Tuple[int, str]]) -> List:
        """
        Extract document sections based on headings.

        Args:
            page_texts: List of (page_number, text) tuples

        Returns:
            List of DocumentSection objects

        Raises:
            ExtractionError: Section extraction failed
        """
        pass


class IReferenceExtractor(ABC):
    """Interface for extracting references/bibliography"""

    @abstractmethod
    def extract_references(self, full_text: str) -> List[str]:
        """
        Extract references from document.

        Args:
            full_text: Full document text

        Returns:
            List of reference strings

        Raises:
            ExtractionError: Reference extraction failed
        """
        pass


class IClaimExtractor(ABC):
    """
    Claim extractor interface contract.

    Responsible for extracting verifiable claims from parsed documents.
    """

    @abstractmethod
    def extract_claims(self, parsed_document) -> List:
        """
        Extract claims from parsed document.

        Args:
            parsed_document: ParsedDocument object

        Returns:
            List of Claim objects

        Raises:
            ExtractionError: Claim extraction failed
        """
        pass

    @abstractmethod
    def extract_from_text(self, text: str, context: Dict) -> List:
        """
        Extract claims from text segment.

        Args:
            text: Text to extract from
            context: Extraction context (section, page_number)

        Returns:
            List of Claim objects

        Raises:
            ExtractionError: Extraction failed
        """
        pass


class IPatternExtractor(ABC):
    """Interface for pattern-based claim extraction"""

    @abstractmethod
    def extract_pattern_claims(self, text: str, section: str, page_number: Optional[int]) -> List:
        """
        Extract claims using indicator patterns.

        Args:
            text: Text to extract from
            section: Section name
            page_number: Optional page number

        Returns:
            List of Claim objects matching patterns
        """
        pass


class IDeclarativeExtractor(ABC):
    """Interface for declarative statement extraction"""

    @abstractmethod
    def extract_declarative_claims(self, text: str, section: str, page_number: Optional[int]) -> List:
        """
        Extract strong declarative statements as claims.

        Args:
            text: Text to extract from
            section: Section name
            page_number: Optional page number

        Returns:
            List of Claim objects
        """
        pass


class IClaimValidator(ABC):
    """Interface for claim validation"""

    @abstractmethod
    def is_valid_claim(self, claim_text: str) -> bool:
        """
        Validate claim text.

        Args:
            claim_text: Claim text to validate

        Returns:
            True if valid claim

        Validation Rules:
            - Length between min_claim_length and max_claim_length
            - At least 3 words
        """
        pass


class ICitationLinker(ABC):
    """
    Citation linker interface contract.

    Responsible for linking claims to supporting citations.
    """

    @abstractmethod
    def link_claims_to_citations(self, claims: List, references: List[str]) -> List:
        """
        Link claims to their supporting citations.

        Args:
            claims: List of Claim objects
            references: List of reference strings

        Returns:
            List of ClaimCitationLink objects

        Raises:
            LinkingError: Citation linking failed
        """
        pass

    @abstractmethod
    def parse_citation(self, reference: str):
        """
        Parse reference string into Citation object.

        Args:
            reference: Reference string

        Returns:
            Citation object

        Raises:
            ParseError: Citation parsing failed
        """
        pass


class IReferenceParser(ABC):
    """Interface for parsing reference strings"""

    @abstractmethod
    def parse_references(self, references: List[str]) -> List:
        """
        Parse reference strings into Citation objects.

        Args:
            references: List of reference strings

        Returns:
            List of Citation objects

        Raises:
            ParseError: Parsing failed
        """
        pass


class IDOIExtractor(ABC):
    """Interface for extracting DOIs from references"""

    @abstractmethod
    def extract_doi(self, text: str) -> Optional[str]:
        """
        Extract DOI from reference text.

        Args:
            text: Reference text

        Returns:
            DOI string or None

        Pattern: 10.\\d{4,9}/[-._;()/:A-Z0-9]+
        """
        pass


class IURLExtractor(ABC):
    """Interface for extracting URLs from references"""

    @abstractmethod
    def extract_url(self, text: str) -> Optional[str]:
        """
        Extract URL from reference text.

        Args:
            text: Reference text

        Returns:
            URL string or None

        Pattern: https?://[^\\s]+
        """
        pass


class ICitationMarkerDetector(ABC):
    """Interface for detecting citation markers in text"""

    @abstractmethod
    def find_citation_markers(self, text: str) -> set:
        """
        Find citation markers in text.

        Args:
            text: Text to search

        Returns:
            Set of citation IDs

        Supported Patterns:
            - Numeric: [1], [2,3], [1-3]
            - Author-year: (Smith 2020), (Smith et al. 2020)
        """
        pass


class ILinkStrengthCalculator(ABC):
    """Interface for calculating claim-citation link strength"""

    @abstractmethod
    def calculate_link_strength(self, claim, citations: List) -> float:
        """
        Calculate link strength between claim and citations.

        Args:
            claim: Claim object
            citations: List of Citation objects

        Returns:
            Float in range [0.0, 1.0]

        Algorithm:
            - Base strength: min(citation_count / 3.0, 1.0)
            - Boost for recent citations (year > 2015): * 1.2
        """
        pass


class IConfidenceScorer(ABC):
    """
    Confidence scorer interface contract.

    Responsible for assigning confidence scores to claims.
    """

    @abstractmethod
    def score_claims(self, claims: List, claim_citation_links: List) -> List:
        """
        Assign confidence scores to claims.

        Args:
            claims: List of Claim objects
            claim_citation_links: List of ClaimCitationLink objects

        Returns:
            List of ConfidenceScore objects

        Raises:
            ScoringError: Confidence scoring failed
        """
        pass

    @abstractmethod
    def score_claim(self, claim, citation_link: Optional) -> Any:
        """
        Score single claim.

        Args:
            claim: Claim object
            citation_link: Optional ClaimCitationLink

        Returns:
            ConfidenceScore object

        Raises:
            ScoringError: Scoring failed
        """
        pass


class ICitationScorer(ABC):
    """Interface for citation-based scoring"""

    @abstractmethod
    def score_citations(self, citation_link) -> float:
        """
        Score claim based on citation support.

        Args:
            citation_link: ClaimCitationLink object

        Returns:
            Float in range [0.0, 1.0]

        Algorithm:
            - Base: 0.3 for uncited claims
            - Score: min(0.5 + (count * 0.1), 1.0)
            - Adjustment: score * link_strength
        """
        pass


class ILinguisticScorer(ABC):
    """Interface for linguistic pattern scoring"""

    @abstractmethod
    def score_linguistics(self, claim_text: str) -> float:
        """
        Score claim based on linguistic patterns.

        Args:
            claim_text: Claim text

        Returns:
            Float in range [0.0, 1.0]

        Features:
            - HEDGE_WORDS: Reduce confidence by 0.05 each
            - BOOST_WORDS: Increase confidence by 0.05 each
            - UNCERTAINTY_MARKERS: Reduce by 0.1 each
            - Question marks: Reduce by 0.2
            - Word count: [10-50] +0.05, >100 -0.05
        """
        pass


class IContextScorer(ABC):
    """Interface for context-based scoring"""

    @abstractmethod
    def score_context(self, claim) -> float:
        """
        Score claim based on contextual factors.

        Args:
            claim: Claim object

        Returns:
            Float in range [0.0, 1.0]

        Section Weights:
            - Results/Findings/Conclusion: +0.2
            - Discussion/Limitations: +0.0
            - Introduction/Background: -0.1

        Claim Type Weights:
            - Finding: +0.1
            - Hypothesis: -0.1
        """
        pass


class IGraphBuilder(ABC):
    """
    Graph builder interface contract.

    Responsible for constructing knowledge graphs from pipeline outputs.
    """

    @abstractmethod
    def build_graph(self, parsed_document, claims: List, claim_citation_links: List, confidence_scores: List):
        """
        Build knowledge graph from pipeline outputs.

        Args:
            parsed_document: ParsedDocument object
            claims: List of Claim objects
            claim_citation_links: List of ClaimCitationLink objects
            confidence_scores: List of ConfidenceScore objects

        Returns:
            Knowledge graph (NetworkX DiGraph)

        Raises:
            GraphBuildError: Graph construction failed
        """
        pass

    @abstractmethod
    def export_graph(self, graph, output_path: str, format: Optional[str] = None) -> None:
        """
        Export graph to file.

        Args:
            graph: Knowledge graph
            output_path: Output file path
            format: Optional export format (gexf, graphml, json, gml)

        Raises:
            StorageError: Export failed
        """
        pass


class INodeFactory(ABC):
    """Interface for creating graph nodes"""

    @abstractmethod
    def create_document_node(self, parsed_document):
        """
        Create document node.

        Args:
            parsed_document: ParsedDocument object

        Returns:
            GraphNode with type="document"

        Node ID Format: doc_{hash(title) % 10000}
        """
        pass

    @abstractmethod
    def create_claim_node(self, claim, confidence):
        """
        Create claim node.

        Args:
            claim: Claim object
            confidence: ConfidenceScore object

        Returns:
            GraphNode with type="claim"

        Node ID Format: claim_{hash(text) % 100000}
        """
        pass

    @abstractmethod
    def create_citation_node(self, citation):
        """
        Create citation node.

        Args:
            citation: Citation object

        Returns:
            GraphNode with type="citation"

        Node ID Format: cit_{citation_id}
        """
        pass


class IEdgeFactory(ABC):
    """Interface for creating graph edges"""

    @abstractmethod
    def create_edge(self, source: str, target: str, edge_type: str, weight: float = 1.0):
        """
        Create graph edge.

        Args:
            source: Source node ID
            target: Target node ID
            edge_type: Edge type (contains, supports, cites)
            weight: Edge weight [0.0, 1.0]

        Returns:
            GraphEdge object

        Edge Types:
            - contains: Document → Claim
            - supports: Claim → Citation
            - cites: Citation → Citation (future)
        """
        pass


# ============================================================================
# Layer 2: Application Layer Interfaces
# ============================================================================

class IPipeline(ABC):
    """
    Pipeline orchestration interface contract.

    Responsible for coordinating document processing workflow.
    """

    @abstractmethod
    def process(self, pdf_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Process single PDF document through pipeline.

        Args:
            pdf_path: Absolute path to PDF file
            output_path: Optional output path for graph

        Returns:
            Dictionary with pipeline results:
                - parsed_document: ParsedDocument
                - claims: List[Claim]
                - claim_citation_links: List[ClaimCitationLink]
                - confidence_scores: List[ConfidenceScore]
                - high_confidence_claims: List[ConfidenceScore]
                - graph: NetworkX DiGraph
                - graph_statistics: Dict

        Raises:
            ValidationError: Input validation failed
            PipelineError: Processing failed
        """
        pass

    @abstractmethod
    def process_batch(self, pdf_paths: List[str], output_dir: Optional[str] = None) -> List[Dict]:
        """
        Process multiple PDF documents.

        Args:
            pdf_paths: List of PDF file paths
            output_dir: Optional output directory for graphs

        Returns:
            List of result dictionaries

        Raises:
            ValidationError: Input validation failed
            BatchProcessingError: Batch processing failed
        """
        pass


class IConfigurationProvider(ABC):
    """
    Configuration provider interface contract.

    Responsible for providing configuration to components.
    """

    @abstractmethod
    def get_config(self, component: str) -> Dict[str, Any]:
        """
        Get configuration for component.

        Args:
            component: Component name (e.g., 'document_parser')

        Returns:
            Component-specific configuration dictionary

        Raises:
            ConfigurationError: Configuration not found or invalid
        """
        pass

    @abstractmethod
    def validate_config(self, config: Dict) -> 'ValidationResult':
        """
        Validate configuration against schema.

        Args:
            config: Configuration dictionary

        Returns:
            ValidationResult object

        Raises:
            ValidationError: Configuration invalid
        """
        pass


# ============================================================================
# Layer 4: Infrastructure Layer Interfaces
# ============================================================================

class IFileReader(ABC):
    """
    File reader interface contract.

    Responsible for reading files from disk.
    """

    @abstractmethod
    def read_pdf(self, file_path: str):
        """
        Read PDF file.

        Args:
            file_path: Absolute path to PDF

        Returns:
            PDFDocument handle

        Raises:
            FileNotFoundError: File not found
            PermissionError: Insufficient permissions
            PDFError: Invalid PDF format
        """
        pass

    @abstractmethod
    def exists(self, file_path: str) -> bool:
        """
        Check if file exists.

        Args:
            file_path: File path

        Returns:
            True if file exists
        """
        pass


class IPDFProcessor(ABC):
    """
    PDF processor interface contract.

    Responsible for PDF-specific operations.
    """

    @abstractmethod
    def extract_text(self, pdf_document, page_range: Optional[Tuple[int, int]] = None) -> List:
        """
        Extract text from PDF pages.

        Args:
            pdf_document: PDF document handle
            page_range: Optional (start, end) page range

        Returns:
            List of PageText objects

        Raises:
            PDFProcessingError: Text extraction failed
        """
        pass


class IGraphStorage(ABC):
    """
    Graph storage interface contract.

    Responsible for persisting graphs.
    """

    @abstractmethod
    def save_graph(self, graph, file_path: str, format: GraphFormat) -> None:
        """
        Save graph to file.

        Args:
            graph: Knowledge graph
            file_path: Output file path
            format: Graph format

        Raises:
            StorageError: Save operation failed
        """
        pass

    @abstractmethod
    def load_graph(self, file_path: str, format: Optional[GraphFormat] = None):
        """
        Load graph from file.

        Args:
            file_path: Graph file path
            format: Optional graph format (auto-detected if not provided)

        Returns:
            Knowledge graph

        Raises:
            StorageError: Load operation failed
        """
        pass


class ILogger(ABC):
    """
    Logging interface contract.

    Responsible for logging system events.
    """

    @abstractmethod
    def log(self, level: LogLevel, message: str, context: Optional[Dict] = None) -> None:
        """
        Log message with context.

        Args:
            level: Log level
            message: Log message
            context: Optional context dictionary
        """
        pass


# ============================================================================
# Cross-Cutting Interfaces
# ============================================================================

class IValidator(ABC):
    """
    Validator interface contract.

    Responsible for validating data.
    """

    @abstractmethod
    def validate(self, value: Any) -> 'ValidationResult':
        """
        Validate value.

        Args:
            value: Value to validate

        Returns:
            ValidationResult with is_valid and errors
        """
        pass


@dataclass
class ValidationResult:
    """Validation result"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class ICache(ABC):
    """
    Cache interface contract.

    Responsible for caching values.
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cached value with optional TTL"""
        pass

    @abstractmethod
    def invalidate(self, key: str) -> None:
        """Invalidate cache entry"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear entire cache"""
        pass


class IPlugin(ABC):
    """
    Plugin interface contract.

    Base interface for all plugins.
    """

    @abstractmethod
    def get_name(self) -> str:
        """Return plugin name"""
        pass

    @abstractmethod
    def get_version(self) -> str:
        """Return plugin version"""
        pass

    @abstractmethod
    def initialize(self, config: Dict) -> None:
        """Initialize plugin with configuration"""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown plugin and cleanup resources"""
        pass
