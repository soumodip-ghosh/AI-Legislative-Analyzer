import logging
import os
from typing import Optional

import faiss
import numpy as np
import google.generativeai as genai

logger = logging.getLogger(__name__)

# These are imported lazily so the server starts even if embeddings are slow
_embeddings = None
_llm_initialized = False


def _get_api_key() -> str:
    """Get GOOGLE_API_KEY with proper error handling."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY environment variable not set. "
            "Please set it in your .env file or as an environment variable. "
            "Get your key from: https://aistudio.google.com/app/apikey"
        )
    return api_key


def _initialize_llm():
    global _llm_initialized
    if not _llm_initialized:
        genai.configure(api_key=_get_api_key())
        _llm_initialized = True
        logger.info("✓ LLM initialized with Google Generative AI (Gemini 2.5 Flash)")


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        from sentence_transformers import SentenceTransformer

        try:
            _embeddings = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("✓ Embeddings initialized with SentenceTransformer (all-MiniLM-L6-v2)")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            raise
    return _embeddings


def build_vectorstore(chunks: list[str]):
    """Build an in-memory FAISS index from text chunks. One-shot, no persistence needed."""
    model = get_embeddings()

    chunk_embeddings = model.encode(
        chunks,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    index = faiss.IndexFlatIP(chunk_embeddings.shape[1])
    index.add(np.array(chunk_embeddings, dtype=np.float32))

    return {"index": index, "docs": chunks}


def retrieve_relevant_chunks(vectorstore, query: str, k: int = 5) -> list[str]:
    """Pull the most semantically relevant chunks for a given query."""
    model = get_embeddings()
    query_embedding = model.encode(
        [query],
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype(np.float32)

    scores, ids = vectorstore["index"].search(query_embedding, k)
    return [vectorstore["docs"][int(i)] for i in ids[0] if i != -1]


def invoke_llm(prompt: str) -> str:
    _initialize_llm()
    response = genai.chat.completions.create(
        model="gemini-2.5-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_output_tokens=1500,
    )

    content = ""
    # `response` may be dict-like depending on package version
    if hasattr(response, "choices") and response.choices:
        message = response.choices[0].get("message", {})
        if isinstance(message, dict):
            content = message.get("content", "")
        else:
            content = getattr(message, "get", lambda *a, **k: "")("content", "")
    else:
        content = getattr(response, "last", "") or ""

    return content.strip()


ANALYSIS_PROMPT = """You are a legal analyst helping Indian citizens understand legislation.
Analyze the provided legal document text and extract structured information.

Document content:
{document_text}

Extracted facts from document:
{extracted_facts}

Respond ONLY with a valid JSON object. No markdown, no explanation, just JSON:
{{
  "summary": "2-3 sentence plain-English summary of what this law/bill does",
  "key_changes": [
    {{"title": "short title", "description": "what specifically changes", "impact_level": "high|medium|low"}}
  ],
  "affected_entities": [
    {{"entity": "who is affected", "how": "specific impact on them"}}
  ],
  "financial_impact": {{
    "description": "summary of financial aspects",
    "figures": ["list of specific monetary amounts or percentages mentioned"],
    "who_pays": "who bears the financial burden",
    "who_benefits": "who gains financially"
  }},
  "timeline": [
    {{"date": "date or timeframe", "event": "what happens on this date"}}
  ],
  "simplified_explanation": "Explain this like the person is a regular Indian citizen with no legal background. Use simple language. 3-4 sentences.",
  "penalties_and_compliance": "What happens if someone doesn't comply? What are the penalties?",
  "document_type": "Act|Bill|Amendment|Policy|Notification|Other"
}}"""


def analyze_with_rag(
    compressed_text: str,
    chunks: list[str],
    extracted_facts: dict,
    document_title: Optional[str] = None,
    original_token_count: int = 0,
) -> dict:
    """
    RAG-augmented analysis with token-aware context window:
    1. Build vectorstore from semantic chunks
    2. Retrieve chunks relevant to key query aspects
    3. Combine with compressed text (adaptive context size based on compression ratio)
    4. Single LLM call with dense prompt
    
    For 100K+ token documents:
    - Uses aggressive context window management
    - Prioritizes high-value chunks (penalties, amounts, dates)
    - Removes redundancy to fit within LLM token limits
    """

    # Adaptive context sizing based on original document size
    if original_token_count > 100000:
        compressed_text_limit = 3000      # ~750 tokens max from compressed text
        rag_context_limit = 2000          # ~500 tokens max from RAG retrieval
        chunk_preview_limit = 300         # snippets only
        logger.info(f"100K+ token document: using aggressive context window (3500 chars max for LLM)")
    elif original_token_count > 50000:
        compressed_text_limit = 4000
        rag_context_limit = 2000
        chunk_preview_limit = 400
    else:
        compressed_text_limit = 5000
        rag_context_limit = 3000
        chunk_preview_limit = 500

    vectorstore = build_vectorstore(chunks)

    # Pull chunks relevant to the aspects we care most about
    # Prioritize high-value queries for large documents
    queries = [
        "penalties fines imprisonment punishable",
        "financial impact amount rupees crore lakh",
        "affected entities obligations responsibilities",
        "date timeline implementation effective",
        "key changes amendments modifications",
    ]

    retrieved = set()
    k_results = 3 if original_token_count <= 50000 else 2  # Fewer results for large docs
    
    for q in queries:
        for chunk in retrieve_relevant_chunks(vectorstore, q, k=k_results):
            retrieved.add(chunk[:chunk_preview_limit])  # cap each chunk contribution

    rag_context = "\n\n---\n\n".join(retrieved)
    logger.info(f"RAG retrieved {len(retrieved)} relevant chunks ({len(rag_context)} chars)")

    # Merge: compressed main text + RAG-retrieved highlights
    # Adaptive context window based on document size
    combined = f"{compressed_text[:compressed_text_limit]}\n\n=== KEY SECTIONS (retrieved) ===\n\n{rag_context[:rag_context_limit]}"

    facts_str = "\n".join(
        f"- {k}: {', '.join(str(v) for v in vals[:5])}"
        for k, vals in extracted_facts.items()
    ) or "None extracted"

    prompt = ANALYSIS_PROMPT.format(document_text=combined, extracted_facts=facts_str)

    # Log context information for large documents
    if original_token_count > 100000:
        prompt_tokens_estimate = rough_token_count(prompt)
        logger.info(
            f"Large document analysis: "
            f"Original={original_token_count:,} tokens, "
            f"Compressed≈{len(combined)//4:,} tokens, "
            f"Prompt≈{prompt_tokens_estimate:,} tokens"
        )

    response_text = invoke_llm(prompt)

    import json
    text = response_text.strip()
    # Strip any accidental markdown fences
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("LLM returned invalid JSON, attempting partial parse")
        # Return a graceful fallback rather than crashing
        return {
            "summary": text[:500],
            "key_changes": [],
            "affected_entities": [],
            "financial_impact": {"description": "Could not extract structured data.", "figures": [], "who_pays": "", "who_benefits": ""},
            "timeline": [],
            "simplified_explanation": text[:300],
            "penalties_and_compliance": "",
            "document_type": "Unknown",
        }


def ask_question(compressed_text: str, chunks: list, question: str) -> str:
    """Answer a follow-up question using RAG on the compressed document."""
    vectorstore = build_vectorstore(chunks)

    # Retrieve relevant chunks
    relevant_docs = retrieve_relevant_chunks(vectorstore, question, k=5)
    combined = "\n\n".join(relevant_docs)

    # Create question-answering prompt
    prompt = f"""
You are a legal document assistant. Answer the user's question based on the provided document context.

Document Context:
{combined}

User Question: {question}

Provide a clear, concise answer based only on the document content. If the answer isn't in the document, say so.
"""

    response_text = invoke_llm(prompt)
    return response_text.strip()


def rough_token_count(text: str) -> int:
    """Estimate token count (approximately 4 characters per token for LLMs)."""
    return len(text) // 4
