"""
Knowledge Distillation Pipeline

Main pipeline that orchestrates all components to transform research papers
into structured, verifiable knowledge graphs.
"""

import yaml
from pathlib import Path
from typing import Optional, Dict, Any

from .document_parser import DocumentParser, ParsedDocument
from .claim_extractor import ClaimExtractor
from .citation_linker import CitationLinker
from .confidence_scorer import ConfidenceScorer
from .graph_builder import GraphBuilder


class KnowledgeDistillationPipeline:
    """
    End-to-end pipeline for transforming research papers into knowledge graphs.

    Orchestrates document parsing, claim extraction, citation linking,
    confidence scoring, and graph construction.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the pipeline.

        Args:
            config_path: Path to YAML configuration file
        """
        # Load configuration
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = self._default_config()

        # Initialize components
        self.document_parser = DocumentParser(
            config=self.config.get('document_parser', {})
        )
        self.claim_extractor = ClaimExtractor(
            config=self.config.get('claim_extractor', {})
        )
        self.citation_linker = CitationLinker(
            config=self.config.get('citation_linker', {})
        )
        self.confidence_scorer = ConfidenceScorer(
            config=self.config.get('confidence_scorer', {})
        )
        self.graph_builder = GraphBuilder(
            config=self.config.get('graph_builder', {})
        )

    def process(self, pdf_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a PDF document through the complete pipeline.

        Args:
            pdf_path: Path to the PDF file
            output_path: Optional path to save the knowledge graph

        Returns:
            Dictionary containing all pipeline results
        """
        print(f"Processing document: {pdf_path}")

        # Step 1: Parse the document
        print("  [1/5] Parsing document...")
        parsed_doc = self.document_parser.parse(pdf_path)
        print(f"        Found {len(parsed_doc.sections)} sections, {len(parsed_doc.references)} references")

        # Step 2: Extract claims
        print("  [2/5] Extracting claims...")
        claims = self.claim_extractor.extract_claims(parsed_doc)
        print(f"        Extracted {len(claims)} claims")

        # Step 3: Link claims to citations
        print("  [3/5] Linking citations...")
        claim_citation_links = self.citation_linker.link_claims_to_citations(
            claims,
            parsed_doc.references
        )
        print(f"        Created {len(claim_citation_links)} claim-citation links")

        # Step 4: Score claim confidence
        print("  [4/5] Scoring confidence...")
        confidence_scores = self.confidence_scorer.score_claims(
            claims,
            claim_citation_links
        )
        print(f"        Scored {len(confidence_scores)} claims")

        # Get high confidence claims
        high_confidence = self.confidence_scorer.get_high_confidence_claims(
            confidence_scores,
            threshold=0.7
        )
        print(f"        Found {len(high_confidence)} high-confidence claims (>0.7)")

        # Step 5: Build knowledge graph
        print("  [5/5] Building knowledge graph...")
        graph = self.graph_builder.build_graph(
            parsed_doc,
            claims,
            claim_citation_links,
            confidence_scores
        )

        stats = self.graph_builder.get_graph_statistics()
        print(f"        Graph: {stats['num_nodes']} nodes, {stats['num_edges']} edges")

        # Export graph if output path provided
        if output_path:
            self.graph_builder.export_graph(output_path)
            print(f"\nKnowledge graph exported to: {output_path}")

        print("\nProcessing complete!")

        return {
            'parsed_document': parsed_doc,
            'claims': claims,
            'claim_citation_links': claim_citation_links,
            'confidence_scores': confidence_scores,
            'high_confidence_claims': high_confidence,
            'graph': graph,
            'graph_statistics': stats
        }

    def process_batch(self, pdf_paths: list, output_dir: Optional[str] = None) -> list:
        """
        Process multiple PDF documents.

        Args:
            pdf_paths: List of paths to PDF files
            output_dir: Optional directory to save knowledge graphs

        Returns:
            List of result dictionaries
        """
        results = []

        for i, pdf_path in enumerate(pdf_paths, 1):
            print(f"\n{'='*60}")
            print(f"Document {i}/{len(pdf_paths)}")
            print(f"{'='*60}")

            try:
                output_path = None
                if output_dir:
                    output_dir_path = Path(output_dir)
                    output_dir_path.mkdir(parents=True, exist_ok=True)

                    pdf_name = Path(pdf_path).stem
                    format_ext = self.config.get('graph_builder', {}).get('format', 'gexf')
                    output_path = str(output_dir_path / f"{pdf_name}_graph.{format_ext}")

                result = self.process(pdf_path, output_path)
                results.append({
                    'pdf_path': pdf_path,
                    'status': 'success',
                    'result': result
                })

            except Exception as e:
                print(f"Error processing {pdf_path}: {str(e)}")
                results.append({
                    'pdf_path': pdf_path,
                    'status': 'error',
                    'error': str(e)
                })

        return results

    @staticmethod
    def _default_config() -> Dict:
        """Return default configuration."""
        return {
            'document_parser': {
                'max_pages': None,
                'extract_images': False,
                'extract_tables': True
            },
            'claim_extractor': {
                'min_claim_length': 10,
                'max_claim_length': 500,
                'use_patterns': True
            },
            'citation_linker': {
                'formats': ['APA', 'MLA', 'Chicago'],
                'extract_doi': True,
                'extract_urls': True
            },
            'confidence_scorer': {
                'min_confidence': 0.0,
                'use_citation_count': True,
                'use_author_authority': False
            },
            'graph_builder': {
                'format': 'gexf',
                'include_metadata': True,
                'max_nodes': 10000
            }
        }
