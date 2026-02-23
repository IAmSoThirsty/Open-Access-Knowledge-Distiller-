"""
Graph Builder Module

Constructs knowledge graphs from extracted claims, citations, and confidence scores.
"""

import json
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict

try:
    import networkx as nx
except ImportError:
    nx = None


@dataclass
class GraphNode:
    """Represents a node in the knowledge graph."""
    node_id: str
    node_type: str  # claim, citation, document
    label: str
    attributes: Dict[str, Any] = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}


@dataclass
class GraphEdge:
    """Represents an edge in the knowledge graph."""
    source: str
    target: str
    edge_type: str  # supports, cites, contains
    weight: float = 1.0
    attributes: Dict[str, Any] = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}


class GraphBuilder:
    """
    Builds knowledge graphs from extracted claims and citations.

    Creates structured graph representations with nodes for claims, citations,
    and documents, and edges representing relationships.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the GraphBuilder.

        Args:
            config: Configuration dictionary for graph building settings
        """
        if nx is None:
            raise ImportError("networkx is required. Install with: pip install networkx")

        self.config = config or {}
        self.format = self.config.get('format', 'gexf')
        self.include_metadata = self.config.get('include_metadata', True)
        self.max_nodes = self.config.get('max_nodes', 10000)

        self.graph = nx.DiGraph()
        self.nodes = []
        self.edges = []

    def build_graph(
        self,
        parsed_document,
        claims: List,
        claim_citation_links: List,
        confidence_scores: List
    ) -> nx.DiGraph:
        """
        Build a knowledge graph from document analysis results.

        Args:
            parsed_document: ParsedDocument object
            claims: List of Claim objects
            claim_citation_links: List of ClaimCitationLink objects
            confidence_scores: List of ConfidenceScore objects

        Returns:
            NetworkX DiGraph object
        """
        self.graph = nx.DiGraph()
        self.nodes = []
        self.edges = []

        # Create document node
        doc_node_id = self._add_document_node(parsed_document)

        # Create confidence score lookup
        confidence_lookup = {
            score.claim_text: score
            for score in confidence_scores
        }

        # Create citation link lookup
        citation_lookup = {
            link.claim_text: link
            for link in claim_citation_links
        }

        # Add claim nodes
        claim_node_ids = {}
        for claim in claims:
            confidence = confidence_lookup.get(claim.text)
            claim_node_id = self._add_claim_node(claim, confidence)
            claim_node_ids[claim.text] = claim_node_id

            # Link claim to document
            self._add_edge(
                doc_node_id,
                claim_node_id,
                edge_type="contains",
                weight=1.0
            )

        # Add citation nodes and links
        citation_node_ids = {}
        for link in claim_citation_links:
            claim_node_id = claim_node_ids.get(link.claim_text)
            if not claim_node_id:
                continue

            for citation in link.citations:
                # Add citation node if not already added
                if citation.citation_id not in citation_node_ids:
                    cit_node_id = self._add_citation_node(citation)
                    citation_node_ids[citation.citation_id] = cit_node_id
                else:
                    cit_node_id = citation_node_ids[citation.citation_id]

                # Link claim to citation
                self._add_edge(
                    claim_node_id,
                    cit_node_id,
                    edge_type="supports",
                    weight=link.link_strength
                )

        # Build NetworkX graph
        for node in self.nodes:
            self.graph.add_node(
                node.node_id,
                node_type=node.node_type,
                label=node.label,
                **node.attributes
            )

        for edge in self.edges:
            self.graph.add_edge(
                edge.source,
                edge.target,
                edge_type=edge.edge_type,
                weight=edge.weight,
                **edge.attributes
            )

        return self.graph

    def _add_document_node(self, parsed_document) -> str:
        """Add a document node to the graph."""
        node_id = f"doc_{hash(parsed_document.title) % 10000}"

        attributes = {}
        if self.include_metadata:
            attributes = {
                'title': parsed_document.title,
                'authors': ', '.join(parsed_document.authors),
                'num_sections': len(parsed_document.sections),
                'num_references': len(parsed_document.references)
            }

        self.nodes.append(GraphNode(
            node_id=node_id,
            node_type="document",
            label=parsed_document.title[:100],
            attributes=attributes
        ))

        return node_id

    def _add_claim_node(self, claim, confidence) -> str:
        """Add a claim node to the graph."""
        node_id = f"claim_{hash(claim.text) % 100000}"

        attributes = {
            'section': claim.section,
            'claim_type': claim.claim_type,
        }

        if confidence:
            attributes['confidence'] = confidence.overall_score
            attributes['citation_score'] = confidence.citation_score
            attributes['linguistic_score'] = confidence.linguistic_score

        if self.include_metadata and claim.page_number:
            attributes['page_number'] = claim.page_number

        self.nodes.append(GraphNode(
            node_id=node_id,
            node_type="claim",
            label=claim.text[:100],
            attributes=attributes
        ))

        return node_id

    def _add_citation_node(self, citation) -> str:
        """Add a citation node to the graph."""
        node_id = f"cit_{citation.citation_id}"

        attributes = {}
        if self.include_metadata:
            attributes = {
                'authors': ', '.join(citation.authors),
                'title': citation.title,
                'year': citation.year,
                'doi': citation.doi,
                'url': citation.url,
                'format': citation.citation_format
            }

        label = f"{', '.join(citation.authors[:2])} ({citation.year})" if citation.authors else citation.citation_id

        self.nodes.append(GraphNode(
            node_id=node_id,
            node_type="citation",
            label=label[:100],
            attributes=attributes
        ))

        return node_id

    def _add_edge(self, source: str, target: str, edge_type: str, weight: float = 1.0):
        """Add an edge to the graph."""
        self.edges.append(GraphEdge(
            source=source,
            target=target,
            edge_type=edge_type,
            weight=weight
        ))

    def export_graph(self, output_path: str, format: Optional[str] = None):
        """
        Export the graph to a file.

        Args:
            output_path: Path to save the graph
            format: Export format (gexf, graphml, json, gml)
        """
        export_format = format or self.format

        if export_format == 'gexf':
            nx.write_gexf(self.graph, output_path)
        elif export_format == 'graphml':
            nx.write_graphml(self.graph, output_path)
        elif export_format == 'gml':
            nx.write_gml(self.graph, output_path)
        elif export_format == 'json':
            self._export_json(output_path)
        else:
            raise ValueError(f"Unsupported format: {export_format}")

    def _export_json(self, output_path: str):
        """Export graph as JSON."""
        graph_data = {
            'nodes': [
                {
                    'id': node.node_id,
                    'type': node.node_type,
                    'label': node.label,
                    'attributes': node.attributes
                }
                for node in self.nodes
            ],
            'edges': [
                {
                    'source': edge.source,
                    'target': edge.target,
                    'type': edge.edge_type,
                    'weight': edge.weight,
                    'attributes': edge.attributes
                }
                for edge in self.edges
            ]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)

    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph."""
        return {
            'num_nodes': self.graph.number_of_nodes(),
            'num_edges': self.graph.number_of_edges(),
            'num_claims': len([n for n in self.nodes if n.node_type == 'claim']),
            'num_citations': len([n for n in self.nodes if n.node_type == 'citation']),
            'num_documents': len([n for n in self.nodes if n.node_type == 'document']),
            'density': nx.density(self.graph),
            'is_connected': nx.is_weakly_connected(self.graph) if self.graph.number_of_nodes() > 0 else False
        }
