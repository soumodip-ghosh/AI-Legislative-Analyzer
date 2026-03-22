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


def compress(text: str, max_output_tokens: int = None) -> CompressionResult:
    """
    Main compression pipeline with adaptive token budgeting:
    1. Estimate document size
    2. Apply aggressive compression for 100K+ token documents
    3. Strip filler and extract key facts
    4. Chunk semantically and rank by value
    5. Select highest-value chunks to fit token budget
    
    Args:
        text: Input document text
        max_output_tokens: Max tokens for output. If None, auto-calculate based on input size.
                         For 100K+ tokens, defaults to ~4000 tokens (aggressive compression)
    """
    original_tokens = rough_token_count(text)
    
    # Adaptive token budget based on document size
    if max_output_tokens is None:
        if original_tokens > 100000:
            max_output_tokens = 4000  # Aggressive: ~96% compression for 100K+ docs
            logger.info(f"Large document detected ({original_tokens} tokens). Using aggressive compression.")
        elif original_tokens > 50000:
            max_output_tokens = 5000  # ~90% compression for 50K-100K docs
        elif original_tokens > 20000:
            max_output_tokens = 6000  # Standard compression for 20K-50K docs
        else:
            max_output_tokens = 8000  # Less aggressive for smaller docs
    
    facts = extract_key_facts(text)

    cleaned = strip_legal_filler(text)
    chunks = chunk_by_section(cleaned, max_chunk_chars=2000)  # Smaller chunks for better ranking

    # Score chunks by density of meaningful terms
    def chunk_score(chunk: str) -> float:
        score = 0
        for pattern in MEANINGFUL_PATTERNS.values():
            matches = pattern.findall(chunk)
            score += len(matches) if matches else 0
        
        # Boost score for sections with penalties, financial info, dates
        if re.search(r"(fine|penalty|imprisonment|punishable)", chunk, re.IGNORECASE):
            score += 50
        if re.search(r"(₹|rs\.?|rupees|crore|lakh)", chunk, re.IGNORECASE):
            score += 40
        if re.search(r"\d{1,2}\s+(january|february|march|april|may|june|july|august|september|october|november|december)", chunk, re.IGNORECASE):
            score += 30
        
        return score

    ranked = sorted(enumerate(chunks), key=lambda x: chunk_score(x[1]), reverse=True)

    # Build compressed output within token budget
    selected_chunks = []
    budget = max_output_tokens * 4  # convert tokens → chars
    current_size = 0

    for _, chunk in ranked:
        chunk_size = len(chunk)
        if current_size + chunk_size < budget:
            selected_chunks.append(chunk)
            current_size += chunk_size + 4  # account for "\n\n"

    # Restore original order for coherence
    original_indices = {id(c): i for i, (_, c) in enumerate(ranked)}
    selected_chunks.sort(key=lambda c: [i for i, (_, ch) in enumerate(ranked) if id(ch) == id(c)][0] if any(id(ch) == id(c) for _, ch in ranked) else 999)

    compressed = "\n\n".join(selected_chunks)
    compressed_tokens = rough_token_count(compressed)
    tokens_saved = max(0, original_tokens - compressed_tokens)
    compression_ratio = round((1 - compressed_tokens/max(original_tokens, 1)) * 100)

    logger.info(
        f"Compression: {original_tokens:,} → {compressed_tokens:,} tokens "
        f"(saved {tokens_saved:,}, {compression_ratio}% reduction, "
        f"{len(selected_chunks)} chunks selected from {len(chunks)} total)"
    )

    return CompressionResult(
        compressed_text=compressed,
        original_tokens=original_tokens,
        compressed_tokens=compressed_tokens,
        tokens_saved=tokens_saved,
        extracted_facts=facts,
    )
