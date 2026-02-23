"""
Confidence Scorer Module

Assigns confidence scores to claims based on various factors including
citation support, linguistic patterns, and contextual analysis.
"""

import re
from typing import List, Optional, Dict
from dataclasses import dataclass


@dataclass
class ConfidenceScore:
    """Represents a confidence score for a claim."""
    claim_text: str
    overall_score: float  # 0.0 to 1.0
    citation_score: float = 0.0
    linguistic_score: float = 0.0
    context_score: float = 0.0
    factors: Dict[str, float] = None

    def __post_init__(self):
        if self.factors is None:
            self.factors = {}


class ConfidenceScorer:
    """
    Assigns confidence scores to claims.

    Evaluates claim reliability based on citation support, linguistic markers,
    and contextual factors.
    """

    # Hedging words that reduce confidence
    HEDGE_WORDS = [
        'may', 'might', 'could', 'possibly', 'perhaps', 'likely',
        'probably', 'potentially', 'suggest', 'indicate', 'appear',
        'seem', 'tend'
    ]

    # Boosting words that increase confidence
    BOOST_WORDS = [
        'clearly', 'definitely', 'certainly', 'undoubtedly',
        'prove', 'demonstrate', 'confirm', 'establish', 'show'
    ]

    # Uncertainty markers
    UNCERTAINTY_MARKERS = [
        'unclear', 'uncertain', 'unknown', 'debatable',
        'controversial', 'disputed'
    ]

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the ConfidenceScorer.

        Args:
            config: Configuration dictionary for scoring settings
        """
        self.config = config or {}
        self.min_confidence = self.config.get('min_confidence', 0.0)
        self.use_citation_count = self.config.get('use_citation_count', True)
        self.use_author_authority = self.config.get('use_author_authority', False)

    def score_claims(
        self,
        claims: List,
        claim_citation_links: List
    ) -> List[ConfidenceScore]:
        """
        Assign confidence scores to a list of claims.

        Args:
            claims: List of Claim objects
            claim_citation_links: List of ClaimCitationLink objects

        Returns:
            List of ConfidenceScore objects
        """
        scores = []

        # Create a lookup for citation links
        citation_lookup = {
            link.claim_text: link
            for link in claim_citation_links
        }

        for claim in claims:
            score = self._score_claim(claim, citation_lookup.get(claim.text))
            if score.overall_score >= self.min_confidence:
                scores.append(score)

        return scores

    def _score_claim(self, claim, citation_link) -> ConfidenceScore:
        """Score a single claim."""
        factors = {}

        # Citation-based scoring
        citation_score = 0.0
        if self.use_citation_count and citation_link:
            citation_score = self._score_citations(citation_link)
            factors['citation_support'] = citation_score

        # Linguistic-based scoring
        linguistic_score = self._score_linguistics(claim.text)
        factors['linguistic_confidence'] = linguistic_score

        # Context-based scoring
        context_score = self._score_context(claim)
        factors['contextual_strength'] = context_score

        # Calculate overall score (weighted average)
        weights = {
            'citation': 0.5,
            'linguistic': 0.3,
            'context': 0.2
        }

        overall = (
            citation_score * weights['citation'] +
            linguistic_score * weights['linguistic'] +
            context_score * weights['context']
        )

        return ConfidenceScore(
            claim_text=claim.text,
            overall_score=overall,
            citation_score=citation_score,
            linguistic_score=linguistic_score,
            context_score=context_score,
            factors=factors
        )

    def _score_citations(self, citation_link) -> float:
        """Score based on citation support."""
        if not citation_link or not citation_link.citations:
            return 0.3  # Base score for uncited claims

        num_citations = len(citation_link.citations)

        # More citations = higher confidence (with diminishing returns)
        citation_score = min(0.5 + (num_citations * 0.1), 1.0)

        # Adjust by link strength
        citation_score *= citation_link.link_strength

        return citation_score

    def _score_linguistics(self, claim_text: str) -> float:
        """Score based on linguistic patterns."""
        text_lower = claim_text.lower()
        words = text_lower.split()

        score = 0.7  # Base score

        # Check for hedging words (decrease confidence)
        hedge_count = sum(1 for word in self.HEDGE_WORDS if word in text_lower)
        score -= hedge_count * 0.05

        # Check for boosting words (increase confidence)
        boost_count = sum(1 for word in self.BOOST_WORDS if word in text_lower)
        score += boost_count * 0.05

        # Check for uncertainty markers (decrease confidence)
        uncertainty_count = sum(1 for marker in self.UNCERTAINTY_MARKERS if marker in text_lower)
        score -= uncertainty_count * 0.1

        # Question marks reduce confidence
        if '?' in claim_text:
            score -= 0.2

        # Longer, more detailed claims may be more reliable (to a point)
        word_count = len(words)
        if 10 <= word_count <= 50:
            score += 0.05
        elif word_count > 100:
            score -= 0.05

        # Clamp to valid range
        return max(0.0, min(1.0, score))

    def _score_context(self, claim) -> float:
        """Score based on contextual factors."""
        score = 0.6  # Base score

        # Claims from certain sections may be more reliable
        section = claim.section.lower() if claim.section else ""

        if any(key in section for key in ['result', 'finding', 'conclusion']):
            score += 0.2
        elif any(key in section for key in ['discussion', 'limitation', 'future work']):
            score += 0.0  # Neutral
        elif 'introduction' in section or 'background' in section:
            score -= 0.1  # Often more speculative

        # Claim type matters
        if claim.claim_type == 'finding':
            score += 0.1
        elif claim.claim_type == 'hypothesis':
            score -= 0.1

        # Clamp to valid range
        return max(0.0, min(1.0, score))

    def get_high_confidence_claims(
        self,
        confidence_scores: List[ConfidenceScore],
        threshold: float = 0.7
    ) -> List[ConfidenceScore]:
        """
        Filter claims by confidence threshold.

        Args:
            confidence_scores: List of ConfidenceScore objects
            threshold: Minimum confidence score (0.0 to 1.0)

        Returns:
            List of high-confidence claims
        """
        return [
            score for score in confidence_scores
            if score.overall_score >= threshold
        ]
