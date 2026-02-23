# OAKD - Open Access Knowledge Distiller

Transform research papers and technical documents into structured, verifiable knowledge graphs.

## Overview

OAKD (Open Access Knowledge Distiller) is a Python-based system designed to extract structured knowledge from research papers and technical documents. It parses PDFs, extracts claims and citations, scores confidence, and builds interconnected knowledge graphs suitable for:

- **Scientific transparency**: Verify and trace research claims
- **Policy research analysis**: Extract evidence from policy documents
- **Legislative drafting assistance**: Support evidence-based policymaking
- **Public-access research synthesis**: Make research more accessible and interconnected

## Core Components

### 1. Document Parser
Parses PDF documents into structured sections:
- Extracts title, abstract, authors
- Identifies document sections (Introduction, Methods, Results, etc.)
- Extracts references and bibliography

### 2. Claim Extractor
Identifies verifiable claims using:
- Pattern-based extraction (e.g., "we found that", "results show")
- Linguistic analysis of declarative statements
- Section-aware extraction for context

### 3. Citation Linker
Links claims to their supporting evidence:
- Parses references in multiple formats (APA, MLA, Chicago)
- Extracts DOIs, URLs, and metadata
- Creates claim-citation relationships

### 4. Confidence Scorer
Assigns confidence scores based on:
- Citation support (number and quality)
- Linguistic patterns (hedging vs. boosting words)
- Contextual factors (section type, claim type)

### 5. Graph Builder
Constructs knowledge graphs with:
- Nodes: documents, claims, citations
- Edges: containment, support, citation relationships
- Export formats: GEXF, GraphML, JSON, GML

## Installation

```bash
# Clone the repository
git clone https://github.com/IAmSoThirsty/Open-Access-Knowledge-Distiller-.git
cd Open-Access-Knowledge-Distiller-

# Install dependencies
pip install -r requirements.txt
```

### Dependencies
- `pypdf2>=3.0.0` - PDF text extraction
- `pdfplumber>=0.10.0` - Advanced PDF parsing
- `spacy>=3.7.0` - Natural language processing
- `networkx>=3.2.0` - Graph construction and analysis
- `numpy>=1.24.0` - Numerical operations
- `scikit-learn>=1.3.0` - Machine learning utilities
- `pydantic>=2.5.0` - Data validation

## Quick Start

```python
from oakd import KnowledgeDistillationPipeline

# Initialize the pipeline
pipeline = KnowledgeDistillationPipeline(config_path='config.yaml')

# Process a research paper
results = pipeline.process(
    pdf_path='research_paper.pdf',
    output_path='knowledge_graph.gexf'
)

# Access extracted information
print(f"Title: {results['parsed_document'].title}")
print(f"Claims: {len(results['claims'])}")
print(f"High-confidence claims: {len(results['high_confidence_claims'])}")
```

## Usage Examples

### Single Document Processing

```python
from oakd import KnowledgeDistillationPipeline

pipeline = KnowledgeDistillationPipeline(config_path='config.yaml')

# Process a PDF and generate knowledge graph
results = pipeline.process(
    pdf_path='path/to/paper.pdf',
    output_path='output/graph.gexf'
)

# Examine results
for claim in results['claims'][:5]:
    print(f"Claim: {claim.text}")
    print(f"Section: {claim.section}")
    print(f"Type: {claim.claim_type}\n")
```

### Batch Processing

```python
# Process multiple documents
pdf_files = ['paper1.pdf', 'paper2.pdf', 'paper3.pdf']

results = pipeline.process_batch(
    pdf_paths=pdf_files,
    output_dir='output/graphs'
)

for result in results:
    if result['status'] == 'success':
        stats = result['result']['graph_statistics']
        print(f"{result['pdf_path']}: {stats['num_nodes']} nodes")
```

### Filtering High-Confidence Claims

```python
# Get only high-confidence claims
from oakd import ConfidenceScorer

scorer = ConfidenceScorer()
high_confidence = scorer.get_high_confidence_claims(
    results['confidence_scores'],
    threshold=0.8
)

for score in high_confidence:
    print(f"{score.claim_text[:100]}...")
    print(f"Confidence: {score.overall_score:.2f}\n")
```

### Custom Configuration

```python
# Create custom configuration
custom_config = {
    'claim_extractor': {
        'min_claim_length': 20,
        'max_claim_length': 300,
    },
    'confidence_scorer': {
        'min_confidence': 0.5,
    },
    'graph_builder': {
        'format': 'json',
        'include_metadata': True,
    }
}

# Initialize with custom config
pipeline = KnowledgeDistillationPipeline()
pipeline.config = custom_config
```

## Configuration

Edit `config.yaml` to customize pipeline behavior:

```yaml
document_parser:
  max_pages: null  # null for unlimited
  extract_images: false
  extract_tables: true

claim_extractor:
  min_claim_length: 10
  max_claim_length: 500
  use_patterns: true

citation_linker:
  formats:
    - APA
    - MLA
    - Chicago
  extract_doi: true
  extract_urls: true

confidence_scorer:
  min_confidence: 0.0
  use_citation_count: true
  use_author_authority: false

graph_builder:
  format: gexf  # gexf, graphml, json, gml
  include_metadata: true
  max_nodes: 10000
```

## Graph Visualization

The generated knowledge graphs can be visualized using various tools:

### Using Gephi (GEXF format)
1. Download [Gephi](https://gephi.org/)
2. Open the `.gexf` file
3. Apply layout algorithms (ForceAtlas2, Fruchterman Reingold)
4. Color nodes by type or confidence score

### Using Python (NetworkX)

```python
import networkx as nx
import matplotlib.pyplot as plt

# Load the graph
graph = nx.read_gexf('knowledge_graph.gexf')

# Visualize
pos = nx.spring_layout(graph)
nx.draw(graph, pos, with_labels=True, node_color='lightblue')
plt.show()
```

## Use Cases

### Scientific Transparency
Track how claims evolve across papers, identify highly-cited findings, and verify research chains.

### Policy Research Analysis
Extract evidence-based claims from policy documents to support decision-making.

### Legislative Drafting
Link legislative proposals to supporting research and evidence.

### Research Synthesis
Create interconnected knowledge bases from multiple papers on the same topic.

## Architecture

```
┌─────────────┐
│   PDF Doc   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Document Parser │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│ Claim Extractor │────▶│ Citation Linker  │
└────────┬────────┘     └─────────┬────────┘
         │                        │
         ▼                        ▼
┌──────────────────┐     ┌────────────────┐
│ Confidence Scorer│◀────┤ Graph Builder  │
└─────────┬────────┘     └────────┬───────┘
          │                       │
          └───────────┬───────────┘
                      ▼
              ┌───────────────┐
              │ Knowledge Graph│
              └───────────────┘
```

## API Reference

### KnowledgeDistillationPipeline

Main pipeline class for end-to-end processing.

**Methods:**
- `process(pdf_path, output_path)` - Process single document
- `process_batch(pdf_paths, output_dir)` - Process multiple documents

### DocumentParser

Parse PDF documents into structured sections.

**Methods:**
- `parse(pdf_path)` - Returns ParsedDocument object

### ClaimExtractor

Extract claims from parsed documents.

**Methods:**
- `extract_claims(parsed_document)` - Returns list of Claim objects

### CitationLinker

Link claims to citations.

**Methods:**
- `link_claims_to_citations(claims, references)` - Returns ClaimCitationLink objects

### ConfidenceScorer

Score claim confidence.

**Methods:**
- `score_claims(claims, claim_citation_links)` - Returns ConfidenceScore objects
- `get_high_confidence_claims(scores, threshold)` - Filter by threshold

### GraphBuilder

Build knowledge graphs.

**Methods:**
- `build_graph(parsed_doc, claims, links, scores)` - Returns NetworkX graph
- `export_graph(output_path, format)` - Export to file
- `get_graph_statistics()` - Returns graph statistics

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

MIT License - see LICENSE file for details.

## Citation

If you use OAKD in your research, please cite:

```bibtex
@software{oakd2026,
  title = {OAKD: Open Access Knowledge Distiller},
  author = {Jeremy Karrick},
  year = {2026},
  url = {https://github.com/IAmSoThirsty/Open-Access-Knowledge-Distiller-}
}
```

## Contact

For questions or support, please open an issue on GitHub.
