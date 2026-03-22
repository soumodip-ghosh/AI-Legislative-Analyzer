import logging
import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.parser import validate_file, parse_document
from services.classifier import classify_document
from services.compressor import compress, chunk_by_section
from services.rag import analyze_with_rag
from utils.cache import document_hash, get_cached_result, set_cached_result

logger = logging.getLogger(__name__)

router = APIRouter()

# Hard token ceiling — refuse documents that would blow the context budget even after compression
MAX_ALLOWED_TOKENS = 50_000


class AnalysisResponse(BaseModel):
    summary: str
    key_changes: list
    affected_entities: list
    financial_impact: dict
    timeline: list
    simplified_explanation: str
    penalties_and_compliance: str
    document_type: str
    tokens_saved: int
    original_tokens: int
    compressed_tokens: int
    is_legal: bool
    from_cache: bool = False


@router.post("/analyze")
async def analyze_document(file: UploadFile = File(...)):
    content = await file.read()
    filename = file.filename or "upload"

    # --- Step 1: File validation ---
    valid, error_msg = validate_file(filename, content)
    if not valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # --- Step 2: Cache check (before any heavy work) ---
    doc_hash = document_hash(content)
    cached = get_cached_result(doc_hash)
    if cached:
        cached["from_cache"] = True
        return JSONResponse(content=cached)

    # --- Step 3: Parse document ---
    try:
        raw_text = parse_document(filename, content)
    except Exception as e:
        logger.error(f"Parse error for '{filename}': {e}")
        raise HTTPException(status_code=422, detail=f"Could not read document: {str(e)}")

    # --- Step 4: Domain classification (cheap, no LLM) ---
    classification = classify_document(raw_text)
    if not classification.is_legal:
        return JSONResponse(
            status_code=200,
            content={
                "is_legal": False,
                "summary": "This system is designed only for legal and policy documents.",
                "detail": classification.reason,
                "key_changes": [],
                "affected_entities": [],
                "financial_impact": {},
                "timeline": [],
                "simplified_explanation": "",
                "penalties_and_compliance": "",
                "document_type": "Unknown",
                "tokens_saved": 0,
                "original_tokens": 0,
                "compressed_tokens": 0,
                "from_cache": False,
            },
        )

    # --- Step 5: Token guard ---
    from services.compressor import rough_token_count
    raw_tokens = rough_token_count(raw_text)
    if raw_tokens > MAX_ALLOWED_TOKENS:
        raise HTTPException(
            status_code=413,
            detail=f"Document is too large ({raw_tokens:,} estimated tokens). Max: {MAX_ALLOWED_TOKENS:,}.",
        )

    # --- Step 6: Compression + RAG analysis ---
    try:
        compression_result = compress(raw_text)
        chunks = chunk_by_section(compression_result.compressed_text)

        # Wrap in asyncio timeout — LLM calls can hang
        analysis = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: analyze_with_rag(
                    compression_result.compressed_text,
                    chunks,
                    compression_result.extracted_facts,
                ),
            ),
            timeout=90,
        )

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Analysis timed out. Please try a smaller document.")
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    result = {
        **analysis,
        "is_legal": True,
        "tokens_saved": compression_result.tokens_saved,
        "original_tokens": compression_result.original_tokens,
        "compressed_tokens": compression_result.compressed_tokens,
        "from_cache": False,
    }

    set_cached_result(doc_hash, result)
    return JSONResponse(content=result)


@router.get("/cache-stats")
async def cache_stats():
    from utils.cache import cache_stats as _stats
    return _stats()
