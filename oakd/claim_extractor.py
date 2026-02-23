"""
Claim Extractor Module

Extracts verifiable claims from document text using pattern matching and NLP.
"""

import re
from typing import List, Optional, Dict
from dataclasses import dataclass


@dataclass
class Claim:
    """Represents an extracted claim from a document."""
    text: str
    section: str
    claim_type: str  # assertion, finding, hypothesis, etc.
    context: str = ""
    page_number: Optional[int] = None


class ClaimExtractor:
    """
    Extracts claims from parsed documents.

    Identifies assertions, findings, and hypotheses that can be verified.
    """

    # Patterns that often indicate claims
    CLAIM_INDICATORS = [
        r'we found that',
        r'our results show',
        r'we demonstrate',
        r'this suggests',
        r'we conclude',
        r'evidence indicates',
        r'our findings indicate',
        r'we observed',
        r'results indicate',
        r'data show',
        r'analysis reveals',
        r'we propose',
        r'we hypothesize',
        r'it is evident that',
        r'clearly demonstrates',
        r'proves that',
        r'confirms that',
    ]

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the ClaimExtractor.

        Args:
            config: Configuration dictionary for extractor settings
        """
        self.config = config or {}
        self.min_claim_length = self.config.get('min_claim_length', 10)
        self.max_claim_length = self.config.get('max_claim_length', 500)
        self.use_patterns = self.config.get('use_patterns', True)

    def extract_claims(self, parsed_document) -> List[Claim]:
        """
        Extract claims from a parsed document.

        Args:
            parsed_document: ParsedDocument object

        Returns:
            List of Claim objects
        """
        claims = []

        # Extract from abstract
        if parsed_document.abstract:
            abstract_claims = self._extract_from_text(
                parsed_document.abstract,
                section="Abstract"
            )
            claims.extend(abstract_claims)

        # Extract from sections
        for section in parsed_document.sections:
            section_claims = self._extract_from_text(
                section.content,
                section=section.title,
                page_number=section.page_number
            )
            claims.extend(section_claims)

        return claims

    def _extract_from_text(
        self,
        text: str,
        section: str,
        page_number: Optional[int] = None
    ) -> List[Claim]:
        """Extract claims from a text segment."""
        claims = []

        if self.use_patterns:
            claims.extend(self._pattern_based_extraction(text, section, page_number))

        # Also extract strong declarative sentences
        claims.extend(self._declarative_extraction(text, section, page_number))

        return claims

    def _pattern_based_extraction(
        self,
        text: str,
        section: str,
        page_number: Optional[int]
    ) -> List[Claim]:
        """Extract claims using indicator patterns."""
        claims = []

        # Split into sentences
        sentences = self._split_sentences(text)

        for sentence in sentences:
            # Check for claim indicators
            for indicator in self.CLAIM_INDICATORS:
                if re.search(indicator, sentence, re.IGNORECASE):
                    claim_text = self._extract_claim_from_sentence(sentence, indicator)
                    if claim_text and self._is_valid_claim(claim_text):
                        claims.append(Claim(
                            text=claim_text,
                            section=section,
                            claim_type="finding",
                            context=sentence,
                            page_number=page_number
                        ))
                    break

        return claims

    def _declarative_extraction(
        self,
        text: str,
        section: str,
        page_number: Optional[int]
    ) -> List[Claim]:
        """Extract strong declarative statements as potential claims."""
        claims = []

        sentences = self._split_sentences(text)

        # Look for sentences with strong verbs
        strong_verbs = r'\b(demonstrates?|proves?|shows?|indicates?|reveals?|confirms?|establishes?)\b'

        for sentence in sentences:
            if re.search(strong_verbs, sentence, re.IGNORECASE):
                if self._is_valid_claim(sentence):
                    claims.append(Claim(
                        text=sentence.strip(),
                        section=section,
                        claim_type="assertion",
                        context=sentence,
                        page_number=page_number
                    ))

        return claims

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitter
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _extract_claim_from_sentence(self, sentence: str, indicator: str) -> str:
        """Extract the claim portion from a sentence."""
        # Find the indicator and extract claim after it
        match = re.search(indicator, sentence, re.IGNORECASE)
        if match:
            claim_start = match.end()
            claim = sentence[claim_start:].strip()
            return claim

        return sentence.strip()

    def _is_valid_claim(self, claim: str) -> bool:
        """Check if extracted text is a valid claim."""
        # Check length constraints
        if len(claim) < self.min_claim_length or len(claim) > self.max_claim_length:
            return False

        # Should contain some content words
        words = claim.split()
        if len(words) < 3:
            return False

        return True
