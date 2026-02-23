#!/usr/bin/env python3
"""
Example usage of the OAKD (Open Access Knowledge Distiller) pipeline.

This script demonstrates how to process a research paper PDF and generate
a knowledge graph.
"""

from oakd import KnowledgeDistillationPipeline


def main():
    """Main example function."""
    # Initialize the pipeline with configuration
    pipeline = KnowledgeDistillationPipeline(config_path='config.yaml')

    # Example 1: Process a single PDF
    print("Example 1: Processing a single document")
    print("-" * 60)

    # Process a research paper (replace with your PDF path)
    results = pipeline.process(
        pdf_path='path/to/your/research_paper.pdf',
        output_path='output/knowledge_graph.gexf'
    )

    # Access the results
    print("\nResults Summary:")
    print(f"  Title: {results['parsed_document'].title}")
    print(f"  Authors: {', '.join(results['parsed_document'].authors)}")
    print(f"  Claims extracted: {len(results['claims'])}")
    print(f"  High-confidence claims: {len(results['high_confidence_claims'])}")
    print(f"  Graph nodes: {results['graph_statistics']['num_nodes']}")
    print(f"  Graph edges: {results['graph_statistics']['num_edges']}")

    # Example 2: Process multiple PDFs in batch
    print("\n\nExample 2: Batch processing")
    print("-" * 60)

    pdf_files = [
        'path/to/paper1.pdf',
        'path/to/paper2.pdf',
        'path/to/paper3.pdf'
    ]

    batch_results = pipeline.process_batch(
        pdf_paths=pdf_files,
        output_dir='output/graphs'
    )

    print(f"\nProcessed {len(batch_results)} documents")
    for result in batch_results:
        print(f"  {result['pdf_path']}: {result['status']}")

    # Example 3: Access specific claims with high confidence
    print("\n\nExample 3: High-confidence claims")
    print("-" * 60)

    for i, score in enumerate(results['high_confidence_claims'][:5], 1):
        print(f"\n{i}. Claim: {score.claim_text[:100]}...")
        print(f"   Confidence: {score.overall_score:.2f}")
        print(f"   Citation support: {score.citation_score:.2f}")
        print(f"   Linguistic confidence: {score.linguistic_score:.2f}")


if __name__ == '__main__':
    main()
