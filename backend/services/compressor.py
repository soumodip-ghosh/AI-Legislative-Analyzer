import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Legal boilerplate that carries almost zero information density
FILLER_PATTERNS = [
    # Standard legislative preamble noise
    r"be it enacted by the parliament of india in the .{0,50}year of the republic of india as follows[:\-]?",
    r"an act (to|for) (further )?amend(ing)?",
    r"whereas it is expedient",
    r"it is hereby declared",
    r"for the purposes of this act",
    r"subject to the provisions of",
    r"in accordance with the provisions of",
    r"nothing in this section shall",
    r"save as otherwise provided",
    r"notwithstanding anything (contained|to the contrary)",
    # Repetitive reference language
    r"the provisions of (the )?section \d+ shall",
    r"as the case may be",
    r"in the manner (prescribed|specified)",
    # Signature blocks and official footers
    r"secretary to the government of india",
    r"printed and published by",
    r"registered no\. d\.l\.-",
    r"extraordinary\s+part (i|ii|iii)",
]

COMPILED_FILLERS = [re.compile(p, re.IGNORECASE) for p in FILLER_PATTERNS]

# Patterns we actually want to keep — these carry real meaning
MEANINGFUL_PATTERNS = {
    "dates": re.compile(
        r"\b(\d{1,2}(st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|"
        r"september|october|november|december)[,\s]+\d{4}|\d{4}-\d{2}-\d{2})\b",
        re.IGNORECASE,
    ),
    "money": re.compile(
        r"(rs\.?\s*[\d,]+(\.\d{2})?|rupees\s+[\d,]+|inr\s+[\d,]+|₹\s*[\d,]+(\s*(crore|lakh|thousand))?)",
        re.IGNORECASE,
    ),
    "penalties": re.compile(
        r"(fine|penalty|imprisonment|punishable|liable to|shall pay)[^.]{0,150}\.",
        re.IGNORECASE,
    ),
    "sections": re.compile(r"section\s+\d+[A-Z]?\s*[\.\-]?\s*[A-Z][^.]{20,200}\.", re.IGNORECASE),
}


@dataclass
class CompressionResult:
    compressed_text: str
    original_tokens: int
    compressed_tokens: int
    tokens_saved: int
    extracted_facts: dict


def rough_token_count(text: str) -> int:
    """~4 chars per token is close enough for GPT-family models."""
    return len(text) // 4


def strip_legal_filler(text: str) -> str:
    """Remove boilerplate that adds length without adding meaning."""
    for pattern in COMPILED_FILLERS:
        text = pattern.sub(" ", text)

    # Collapse multiple whitespace/newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)

    return text.strip()


def extract_key_facts(text: str) -> dict:
    """Pull out the high-value facts we want to emphasize in the prompt."""
    facts = {}

    for fact_type, pattern in MEANINGFUL_PATTERNS.items():
        matches = pattern.findall(text) if fact_type != "sections" else pattern.findall(text)
        if matches:
            # Flatten tuples from groups, deduplicate
            cleaned = []
            for m in matches:
                item = m[0] if isinstance(m, tuple) else m
                if item and item not in cleaned:
                    cleaned.append(item)
            if cleaned:
                facts[fact_type] = cleaned[:10]  # cap at 10 per type

    return facts


def chunk_by_section(text: str, max_chunk_chars: int = 3000) -> list[str]:
    """
    Semantic chunking — split on section/article boundaries instead of
    arbitrary character counts. Falls back to paragraph splits.
    """
    # Try to split on section headers first
    section_breaks = re.split(r"\n(?=section\s+\d+|article\s+\d+|\d+\.\s+[A-Z])", text, flags=re.IGNORECASE)

    chunks = []
    for segment in section_breaks:
        if len(segment) <= max_chunk_chars:
            chunks.append(segment.strip())
        else:
            # Segment too big — split by paragraph
            paragraphs = segment.split("\n\n")
            current = ""
            for para in paragraphs:
                if len(current) + len(para) < max_chunk_chars:
                    current += "\n\n" + para
                else:
                    if current.strip():
                        chunks.append(current.strip())
                    current = para
            if current.strip():
                chunks.append(current.strip())

    return [c for c in chunks if len(c) > 50]


def compress(text: str, max_output_tokens: int = 6000) -> CompressionResult:
    """
    Main compression pipeline:
    1. Strip filler
    2. Extract key facts
    3. Chunk semantically
    4. Select highest-value chunks to fit token budget
    """
    original_tokens = rough_token_count(text)
    facts = extract_key_facts(text)

    cleaned = strip_legal_filler(text)
    chunks = chunk_by_section(cleaned)

    # Score chunks by density of meaningful terms
    def chunk_score(chunk: str) -> float:
        score = 0
        for pattern in MEANINGFUL_PATTERNS.values():
            score += len(pattern.findall(chunk))
        # Prefer earlier sections (they usually contain key provisions)
        return score

    ranked = sorted(enumerate(chunks), key=lambda x: chunk_score(x[1]), reverse=True)

    # Build compressed output within token budget
    selected_chunks = []
    budget = max_output_tokens * 4  # convert tokens → chars

    for _, chunk in ranked:
        if len("\n\n".join(selected_chunks)) + len(chunk) < budget:
            selected_chunks.append(chunk)

    # Restore original order for coherence
    original_indices = {c: i for i, (_, c) in enumerate(ranked)}
    selected_chunks.sort(key=lambda c: original_indices.get(c, 0))

    compressed = "\n\n".join(selected_chunks)
    compressed_tokens = rough_token_count(compressed)
    tokens_saved = max(0, original_tokens - compressed_tokens)

    logger.info(
        f"Compression: {original_tokens} → {compressed_tokens} tokens "
        f"({tokens_saved} saved, {round((1 - compressed_tokens/max(original_tokens,1))*100)}% reduction)"
    )

    return CompressionResult(
        compressed_text=compressed,
        original_tokens=original_tokens,
        compressed_tokens=compressed_tokens,
        tokens_saved=tokens_saved,
        extracted_facts=facts,
    )
