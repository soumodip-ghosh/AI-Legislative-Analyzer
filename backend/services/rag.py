import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# These are imported lazily so the server starts even if embeddings are slow
_embeddings = None
_llm = None


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        _embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",  # free tier model
            google_api_key=os.environ["GOOGLE_API_KEY"],
        )
    return _embeddings


def get_llm():
    global _llm
    if _llm is None:
        from langchain_google_genai import ChatGoogleGenerativeAI

        _llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",  # free tier model - fast and capable
            temperature=0.1,            # low temp for factual extraction
            google_api_key=os.environ["GOOGLE_API_KEY"],
            request_timeout=60,
        )
    return _llm


def build_vectorstore(chunks: list[str]):
    """Build an in-memory FAISS index from text chunks. One-shot, no persistence needed."""
    from langchain_community.vectorstores import FAISS
    from langchain.schema import Document

    docs = [Document(page_content=chunk, metadata={"chunk_idx": i}) for i, chunk in enumerate(chunks)]
    vectorstore = FAISS.from_documents(docs, get_embeddings())
    return vectorstore


def retrieve_relevant_chunks(vectorstore, query: str, k: int = 5) -> list[str]:
    """Pull the most semantically relevant chunks for a given query."""
    results = vectorstore.similarity_search(query, k=k)
    return [r.page_content for r in results]


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
) -> dict:
    """
    RAG-augmented analysis:
    1. Build vectorstore from semantic chunks
    2. Retrieve chunks relevant to key query aspects
    3. Combine with compressed text
    4. Single LLM call with dense prompt
    """
    from langchain_core.messages import HumanMessage

    vectorstore = build_vectorstore(chunks)

    # Pull chunks relevant to the aspects we care most about
    queries = [
        "penalties and punishments",
        "who is affected and obligations",
        "financial amounts money fines",
        "dates timeline implementation",
    ]

    retrieved = set()
    for q in queries:
        for chunk in retrieve_relevant_chunks(vectorstore, q, k=3):
            retrieved.add(chunk[:500])  # cap each chunk contribution

    rag_context = "\n\n---\n\n".join(retrieved)

    # Merge: compressed main text + RAG-retrieved highlights
    # Keep total context reasonable
    combined = f"{compressed_text[:4000]}\n\n=== KEY SECTIONS (retrieved) ===\n\n{rag_context[:2000]}"

    facts_str = "\n".join(
        f"- {k}: {', '.join(str(v) for v in vals[:5])}"
        for k, vals in extracted_facts.items()
    ) or "None extracted"

    prompt = ANALYSIS_PROMPT.format(document_text=combined, extracted_facts=facts_str)

    llm = get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])

    import json
    text = response.content.strip()
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
