import re
import logging
from typing import NamedTuple

logger = logging.getLogger(__name__)


class ClassificationResult(NamedTuple):
    is_legal: bool
    confidence: float
    reason: str


# Keywords that strongly signal legal/policy content
LEGAL_KEYWORDS = [
    # Core legal terms
    "act", "bill", "clause", "section", "subsection", "article", "amendment",
    "provision", "statute", "ordinance", "regulation", "gazette", "notification",
    # Indian legislative specific
    "lok sabha", "rajya sabha", "parliament", "ministry", "government of india",
    "central government", "state government", "president of india", "governor",
    "preamble", "schedule", "constitution", "judicial", "tribunal",
    # Policy language
    "whereas", "notwithstanding", "hereinafter", "aforesaid", "thereof",
    "pursuant", "hereby", "enacted", "promulgated", "shall be liable",
    "punishable", "penalty", "fine", "imprisonment", "offence", "compliance",
    # Financial/regulatory
    "tax", "duty", "levy", "tariff", "subsidy", "appropriation", "expenditure",
    "budget", "finance bill", "revenue", "fiscal",
]

# These strongly suggest non-legal content
REJECTION_KEYWORDS = [
    "recipe", "ingredients", "cooking", "workout", "fitness", "movie review",
    "song lyrics", "novel", "fiction", "short story", "sports score",
    "product review", "shopping", "tutorial for beginners",
]

# Minimum ratio of legal keywords to total words that we consider "legal"
MIN_KEYWORD_DENSITY = 0.003  # 0.3% — low bar, but filters obvious non-legal docs


def classify_document(text: str) -> ClassificationResult:
    """
    Lightweight classifier — runs before any LLM call.
    Keyword density + pattern matching. Fast and free.
    """
    if not text or len(text.strip()) < 50:
        return ClassificationResult(False, 0.0, "Document too short to classify.")

    text_lower = text.lower()
    word_count = max(len(text_lower.split()), 1)

    # Hard reject on obvious non-legal content
    for kw in REJECTION_KEYWORDS:
        if kw in text_lower:
            return ClassificationResult(
                False, 0.0, f"Document contains non-legal content (detected: '{kw}')."
            )

    # Count legal keyword hits
    hits = sum(1 for kw in LEGAL_KEYWORDS if kw in text_lower)
    density = hits / word_count

    # Strong structural signals — legislative docs almost always have these
    has_section_pattern = bool(re.search(r"section\s+\d+|article\s+\d+|\(\d+\)\s+[A-Z]", text))
    has_gazette_ref = bool(re.search(r"gazette|official\s+journal|g\.s\.r\.|s\.o\.\s*\d+", text_lower))
    has_enactment_lang = bool(re.search(r"be it enacted|enacted by|it is hereby", text_lower))

    structural_bonus = sum([has_section_pattern, has_gazette_ref, has_enactment_lang]) * 0.005

    effective_density = density + structural_bonus
    is_legal = effective_density >= MIN_KEYWORD_DENSITY and hits >= 3

    confidence = min(effective_density / (MIN_KEYWORD_DENSITY * 5), 1.0)

    reason = (
        f"Detected {hits} legal keyword(s), density {density:.4f}"
        if is_legal
        else f"Only {hits} legal keyword(s) found — doesn't appear to be a legal/policy document."
    )

    logger.info(f"Classification: is_legal={is_legal}, hits={hits}, density={density:.4f}")
    return ClassificationResult(is_legal, confidence, reason)
