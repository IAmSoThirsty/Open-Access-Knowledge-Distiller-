"""
Document Parser Module

Parses PDF documents into structured sections including title, abstract, sections, and references.
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


@dataclass
class DocumentSection:
    """Represents a section in a document."""
    title: str
    content: str
    level: int = 1
    page_number: Optional[int] = None


@dataclass
class ParsedDocument:
    """Represents a parsed document with all its components."""
    title: str
    abstract: str = ""
    authors: List[str] = field(default_factory=list)
    sections: List[DocumentSection] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class DocumentParser:
    """
    Parses PDF documents into structured sections.

    Extracts title, abstract, authors, sections, and references from research papers.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the DocumentParser.

        Args:
            config: Configuration dictionary for parser settings
        """
        if pdfplumber is None:
            raise ImportError("pdfplumber is required. Install with: pip install pdfplumber")

        self.config = config or {}
        self.max_pages = self.config.get('max_pages', None)
        self.extract_tables = self.config.get('extract_tables', True)

    def parse(self, pdf_path: str) -> ParsedDocument:
        """
        Parse a PDF document into structured sections.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            ParsedDocument object containing structured content
        """
        with pdfplumber.open(pdf_path) as pdf:
            pages = pdf.pages[:self.max_pages] if self.max_pages else pdf.pages

            # Extract all text
            full_text = ""
            page_texts = []
            for i, page in enumerate(pages):
                page_text = page.extract_text() or ""
                page_texts.append((i + 1, page_text))
                full_text += page_text + "\n"

            # Parse document structure
            title = self._extract_title(page_texts)
            abstract = self._extract_abstract(full_text)
            authors = self._extract_authors(page_texts)
            sections = self._extract_sections(page_texts)
            references = self._extract_references(full_text)

            return ParsedDocument(
                title=title,
                abstract=abstract,
                authors=authors,
                sections=sections,
                references=references,
                metadata={"num_pages": len(pages)}
            )

    def _extract_title(self, page_texts: List[tuple]) -> str:
        """Extract document title (typically from first page)."""
        if not page_texts:
            return "Untitled"

        first_page = page_texts[0][1]
        lines = [line.strip() for line in first_page.split('\n') if line.strip()]

        # Title is typically the first significant line
        for line in lines[:10]:
            if len(line) > 10 and not line.isupper():
                return line

        return lines[0] if lines else "Untitled"

    def _extract_abstract(self, full_text: str) -> str:
        """Extract abstract section."""
        # Look for abstract section
        pattern = r'(?:ABSTRACT|Abstract)\s*\n(.*?)(?:\n\s*(?:INTRODUCTION|Introduction|1\.|I\.)|\n\s*\n)'
        match = re.search(pattern, full_text, re.DOTALL | re.IGNORECASE)

        if match:
            abstract = match.group(1).strip()
            return re.sub(r'\s+', ' ', abstract)

        return ""

    def _extract_authors(self, page_texts: List[tuple]) -> List[str]:
        """Extract author names from the document."""
        if not page_texts:
            return []

        first_page = page_texts[0][1]
        authors = []

        # Simple heuristic: look for lines after title and before abstract
        lines = [line.strip() for line in first_page.split('\n') if line.strip()]

        # Skip title and look for author-like patterns
        for i, line in enumerate(lines[1:10]):
            # Authors often contain names with commas or "and"
            if ',' in line or ' and ' in line.lower():
                if not line.isupper() and len(line) < 200:
                    authors.extend([name.strip() for name in re.split(r',|and', line) if name.strip()])
                    break

        return authors[:10]  # Limit to reasonable number

    def _extract_sections(self, page_texts: List[tuple]) -> List[DocumentSection]:
        """Extract document sections based on headings."""
        sections = []

        # Common section heading patterns
        section_pattern = r'^(?:\d+\.?\s+|[IVX]+\.\s+)?([A-Z][A-Za-z\s]+)$'

        current_section = None
        current_content = []

        for page_num, page_text in page_texts:
            lines = page_text.split('\n')

            for line in lines:
                line_stripped = line.strip()

                # Check if this is a section heading
                if re.match(section_pattern, line_stripped) and len(line_stripped) < 100:
                    # Save previous section
                    if current_section:
                        sections.append(DocumentSection(
                            title=current_section,
                            content='\n'.join(current_content).strip(),
                            page_number=page_num
                        ))

                    current_section = line_stripped
                    current_content = []
                elif current_section:
                    current_content.append(line_stripped)

        # Add final section
        if current_section:
            sections.append(DocumentSection(
                title=current_section,
                content='\n'.join(current_content).strip(),
                page_number=page_num
            ))

        return sections

    def _extract_references(self, full_text: str) -> List[str]:
        """Extract references/bibliography."""
        # Look for references section
        pattern = r'(?:REFERENCES|References|BIBLIOGRAPHY|Bibliography)\s*\n(.*?)(?:\Z)'
        match = re.search(pattern, full_text, re.DOTALL | re.IGNORECASE)

        if match:
            ref_text = match.group(1).strip()
            # Split by common reference patterns (numbered or bulleted)
            refs = re.split(r'\n\s*(?:\[\d+\]|\d+\.)', ref_text)
            return [ref.strip() for ref in refs if ref.strip() and len(ref.strip()) > 20]

        return []
