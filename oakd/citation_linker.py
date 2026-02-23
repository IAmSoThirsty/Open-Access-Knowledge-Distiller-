"""
Citation Linker Module

Links claims to their supporting citations and extracts citation metadata.
"""

import re
from typing import List, Optional, Dict, Set
from dataclasses import dataclass, field


@dataclass
class Citation:
    """Represents a citation extracted from a document."""
    citation_id: str
    raw_text: str
    authors: List[str] = field(default_factory=list)
    title: str = ""
    year: Optional[int] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    citation_format: str = "unknown"


@dataclass
class ClaimCitationLink:
    """Represents a link between a claim and its supporting citations."""
    claim_text: str
    citations: List[Citation]
    link_strength: float = 1.0  # How strong the link is (0-1)


class CitationLinker:
    """
    Links claims to their supporting citations.

    Extracts citation information and creates relationships between claims and references.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the CitationLinker.

        Args:
            config: Configuration dictionary for citation linking settings
        """
        self.config = config or {}
        self.formats = self.config.get('formats', ['APA', 'MLA', 'Chicago'])
        self.extract_doi = self.config.get('extract_doi', True)
        self.extract_urls = self.config.get('extract_urls', True)

    def link_claims_to_citations(
        self,
        claims: List,
        references: List[str]
    ) -> List[ClaimCitationLink]:
        """
        Link claims to their supporting citations.

        Args:
            claims: List of Claim objects
            references: List of reference strings

        Returns:
            List of ClaimCitationLink objects
        """
        # Parse references into Citation objects
        parsed_citations = self._parse_references(references)

        # Create citation lookup by ID
        citation_lookup = {cit.citation_id: cit for cit in parsed_citations}

        links = []

        for claim in claims:
            # Find citation markers in claim text and context
            cited_ids = self._find_citation_markers(claim.text + " " + claim.context)

            # Get corresponding citations
            claim_citations = [
                citation_lookup[cid]
                for cid in cited_ids
                if cid in citation_lookup
            ]

            if claim_citations:
                links.append(ClaimCitationLink(
                    claim_text=claim.text,
                    citations=claim_citations,
                    link_strength=self._calculate_link_strength(claim, claim_citations)
                ))

        return links

    def _parse_references(self, references: List[str]) -> List[Citation]:
        """Parse reference strings into Citation objects."""
        citations = []

        for i, ref in enumerate(references):
            citation_id = str(i + 1)

            # Extract DOI
            doi = None
            if self.extract_doi:
                doi = self._extract_doi(ref)

            # Extract URL
            url = None
            if self.extract_urls:
                url = self._extract_url(ref)

            # Extract year
            year = self._extract_year(ref)

            # Extract authors (simplified)
            authors = self._extract_authors(ref)

            # Extract title (simplified)
            title = self._extract_title(ref)

            citations.append(Citation(
                citation_id=citation_id,
                raw_text=ref,
                authors=authors,
                title=title,
                year=year,
                doi=doi,
                url=url,
                citation_format=self._detect_format(ref)
            ))

        return citations

    def _find_citation_markers(self, text: str) -> Set[str]:
        """Find citation markers in text (e.g., [1], [2,3], (Smith 2020))."""
        markers = set()

        # Numeric citations: [1], [2,3], [1-3]
        numeric_pattern = r'\[(\d+(?:[-,]\s*\d+)*)\]'
        for match in re.finditer(numeric_pattern, text):
            citation_str = match.group(1)
            # Handle ranges and lists
            if '-' in citation_str:
                start, end = citation_str.split('-')
                markers.update(str(i) for i in range(int(start), int(end) + 1))
            elif ',' in citation_str:
                markers.update(citation_str.replace(' ', '').split(','))
            else:
                markers.add(citation_str)

        # Author-year citations: (Smith 2020), (Smith et al. 2020)
        author_year_pattern = r'\(([A-Z][a-z]+(?:\s+et\s+al\.)?)\s+(\d{4})\)'
        for match in re.finditer(author_year_pattern, text):
            author = match.group(1)
            year = match.group(2)
            markers.add(f"{author}_{year}")

        return markers

    def _extract_doi(self, text: str) -> Optional[str]:
        """Extract DOI from reference text."""
        doi_pattern = r'10.\d{4,9}/[-._;()/:A-Z0-9]+'
        match = re.search(doi_pattern, text, re.IGNORECASE)
        return match.group(0) if match else None

    def _extract_url(self, text: str) -> Optional[str]:
        """Extract URL from reference text."""
        url_pattern = r'https?://[^\s]+'
        match = re.search(url_pattern, text)
        return match.group(0) if match else None

    def _extract_year(self, text: str) -> Optional[int]:
        """Extract publication year from reference."""
        year_pattern = r'\b(19|20)\d{2}\b'
        match = re.search(year_pattern, text)
        return int(match.group(0)) if match else None

    def _extract_authors(self, text: str) -> List[str]:
        """Extract author names from reference (simplified)."""
        # Very simplified - just take the first part before year or title
        parts = text.split('.')
        if parts:
            first_part = parts[0].strip()
            # Authors often separated by commas or "and"
            authors = re.split(r',|and', first_part)
            return [a.strip() for a in authors[:5] if a.strip()]
        return []

    def _extract_title(self, text: str) -> str:
        """Extract title from reference (simplified)."""
        # Title often appears in quotes or after authors
        quote_pattern = r'"([^"]+)"'
        match = re.search(quote_pattern, text)
        if match:
            return match.group(1)

        # Otherwise, try to extract from structure
        parts = text.split('.')
        if len(parts) > 1:
            return parts[1].strip()[:200]  # Limit length

        return ""

    def _detect_format(self, text: str) -> str:
        """Detect citation format (APA, MLA, Chicago, etc.)."""
        # Simplified detection
        if re.search(r'\(\d{4}\)', text):
            return "APA"
        elif re.search(r'\d{4}\.', text):
            return "MLA"
        return "unknown"

    def _calculate_link_strength(self, claim, citations: List[Citation]) -> float:
        """Calculate how strongly a claim is linked to citations."""
        # Simple heuristic: more citations = stronger link
        base_strength = min(len(citations) / 3.0, 1.0)

        # Boost if citations are recent
        if citations:
            avg_year = sum(c.year or 2000 for c in citations) / len(citations)
            if avg_year > 2015:
                base_strength = min(base_strength * 1.2, 1.0)

        return base_strength
