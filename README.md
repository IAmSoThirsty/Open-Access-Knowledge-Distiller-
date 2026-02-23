# OAKD - Open Access Knowledge Distiller

A production-grade structured knowledge engine that transforms research papers and technical documents into structured, verifiable knowledge graphs with epistemic stability guarantees, security hardening, and regulatory compliance.

## Overview

OAKD (Open Access Knowledge Distiller) is a **production-grade structured knowledge engine** designed for adversarial environments and regulatory scrutiny. It extracts structured knowledge from research papers with complete provenance tracking, deterministic processing, formal invariant enforcement, security hardening, and compliance controls.

### Key Differentiators

**Epistemic Stability:**
- ✅ **Deterministic Processing**: Same input → same graph (under same version)
- ✅ **Complete Provenance**: Every element traces back to source document via hash chains
- ✅ **Formal Invariants**: Enforced guarantees about knowledge integrity
- ✅ **Checkpoint/Replay**: Resume failed pipelines, replay executions
- ✅ **Version Management**: Backward-compatible scoring models and graph schemas
- ✅ **Graph Diffing**: Compare knowledge graphs across versions
- ✅ **Score Drift Detection**: Track confidence score stability over time

**Production Security:**
- 🔒 **Input Validation**: Path traversal protection, file type whitelisting, size limits
- 🔒 **Audit Logging**: Tamper-evident logs with cryptographic hash chains and HMAC
- 🔒 **Rate Limiting**: Token bucket algorithm for DoS protection
- 🔒 **Resource Protection**: Memory, CPU, and concurrency limits
- 🔒 **PII Detection**: Automatic detection and masking of personal information
- 🔒 **Circuit Breakers**: Fault isolation to prevent cascading failures

**Regulatory Compliance:**
- 📋 **GDPR Controls**: Data subject rights (access, erasure, portability)
- 📋 **Consent Management**: Lawful basis tracking and consent records
- 📋 **Data Retention**: Policy-driven retention with automatic enforcement
- 📋 **Data Minimization**: Purpose-limited data collection
- 📋 **Compliance Reporting**: Automated audit reports for regulators

**Operational Excellence:**
- 📊 **Performance Metrics**: Throughput, latency percentiles, error rates
- 📊 **Health Monitoring**: Resource usage, component health, liveness probes
- 📊 **SLA Tracking**: Availability, latency, error rate compliance
- 📊 **Alerting**: Deduplication, severity levels, notification callbacks

### Use Cases

- **Scientific transparency**: Verify and trace research claims with provenance
- **Policy research analysis**: Extract evidence with complete audit trails
- **Legislative drafting assistance**: Evidence-based policymaking with confidence scores
- **Public-access research synthesis**: Reproducible knowledge graph construction

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

### Basic Usage

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

### Production Pipeline (Recommended)

For production use with full security, compliance, and epistemic guarantees:

```python
from oakd import EpistemicPipeline

# Initialize production-grade pipeline
pipeline = EpistemicPipeline(
    config_path='config.yaml',

    # Epistemic stability
    enable_checkpoints=True,    # Checkpoint/replay capability
    enable_validation=True,     # Invariant enforcement
    enable_provenance=True,     # Complete provenance tracking

    # Security hardening
    enable_security=True,       # Input validation, audit logging, rate limiting
    allowed_directories={'/var/oakd/documents'},  # File access whitelist
    audit_log_path='/var/log/oakd/audit.log',

    # Compliance controls
    enable_compliance=True,     # GDPR, data retention, consent management
    compliance_dir='/var/oakd/compliance',

    # Operational monitoring
    enable_monitoring=True,     # Metrics, health checks, SLA tracking

    # Session tracking
    session_id='prod_session_123',
    user_id='researcher_456'
)

# Process with full guarantees
results = pipeline.process_deterministic(
    pdf_path='/var/oakd/documents/research_paper.pdf',
    output_path='/var/oakd/output/knowledge_graph.json'
)

# Access epistemic metadata
print(f"Document Hash: {results['document_hash']}")
print(f"Execution ID: {results['execution_id']}")
print(f"Validation: {results['validation_report'].get_summary()}")

# Check system health
health = pipeline.health_monitor.check_health()
print(f"System Status: {health['status']}")

# Verify audit log integrity
if pipeline.audit_logger.verify_integrity():
    print("✅ Audit log intact")
else:
    print("🚨 CRITICAL: Audit log tampered!")

# Get performance metrics
metrics = pipeline.metrics.get_percentiles('document_parsing_ms', percentiles=[50, 95, 99])
print(f"P95 Latency: {metrics[95]:.1f} ms")

# Check SLA compliance
sla = pipeline.sla_tracker.get_sla_compliance()
print(f"Availability: {sla['availability']['current']:.2f}%")
```

## Documentation

- **[Epistemic Stability Guide](EPISTEMIC_STABILITY.md)** - Complete guide to provenance tracking, deterministic processing, checkpointing, graph diffing, and invariant validation
- **[Production Security & Operations](PRODUCTION_SECURITY.md)** - Security hardening, compliance controls, monitoring, alerting, and incident response for production deployments
- **[Architecture Documentation](docs/ARCHITECTURE.md)** - System architecture, design decisions, and RFC-grade technical specifications

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
