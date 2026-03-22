import logging
import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.parser import validate_file, parse_document
from services.classifier import classify_document
from services.compressor import compress, chunk_by_section
from services.rag import analyze_with_rag, ask_question
from utils.cache import document_hash, get_cached_result, set_cached_result

logger = logging.getLogger(__name__)

router = APIRouter()


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

    # --- Step 5: Token guard (relaxed for large documents) ---
    from services.compressor import rough_token_count
    raw_tokens = rough_token_count(raw_text)
    
    # Allow documents up to 150K tokens since we aggressively compress them
    if raw_tokens > 150_000:
        raise HTTPException(
            status_code=413,
            detail=f"Document is too large ({raw_tokens:,} estimated tokens). Max: 150,000.",
        )
    
    if raw_tokens > 100_000:
        logger.warning(f"Processing large document with {raw_tokens:,} tokens. Will apply aggressive compression.")

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
                    original_token_count=compression_result.original_tokens,
                ),
            ),
            timeout=180,
        )

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Analysis timed out. Please try a smaller document.")
    except ValueError as e:
        # Handle API key errors specifically
        if "GOOGLE_API_KEY" in str(e):
            logger.error(f"API Key configuration error: {e}")
            raise HTTPException(
                status_code=500,
                detail="GOOGLE_API_KEY not configured. Please set it in your .env file. "
                       "Get your key from: https://aistudio.google.com/app/apikey"
            )
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Analysis error: {error_msg}", exc_info=True)
        
        # Better error messages for common issues
        if "GOOGLE_API_KEY" in error_msg or "api_key" in error_msg.lower():
            raise HTTPException(
                status_code=500,
                detail="GOOGLE_API_KEY configuration error. Please check your .env file."
            )
        
        raise HTTPException(status_code=500, detail=f"Analysis failed: {error_msg}")

    result = {
        **analysis,
        "is_legal": True,
        "tokens_saved": compression_result.tokens_saved,
        "original_tokens": compression_result.original_tokens,
        "compressed_tokens": compression_result.compressed_tokens,
        "compressed_text": compression_result.compressed_text,
        "doc_hash": doc_hash,
        "from_cache": False,
    }

    set_cached_result(doc_hash, result)
    return JSONResponse(content=result)


@router.post("/chat")
async def chat_question(request: dict):
    """Answer follow-up questions about an analyzed document."""
    try:
        question = request.get("question", "").strip()
        doc_hash = request.get("doc_hash", "").strip()
        
        if not question or not doc_hash:
            raise HTTPException(400, "Missing question or doc_hash")
        
        # Get cached result
        cached = get_cached_result(doc_hash)
        if not cached:
            raise HTTPException(404, "Document not found in cache. Please re-analyze the document.")
        
        compressed_text = cached.get("compressed_text", "")
        if not compressed_text:
            raise HTTPException(500, "Document data not available for questions")
        
        # Recreate chunks and answer
        chunks = chunk_by_section(compressed_text)
        answer = ask_question(compressed_text, chunks, question)
        
        return {"answer": answer}
    
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to answer question: {str(e)}")


@router.get("/cache-stats")
async def cache_stats():
    from utils.cache import cache_stats as _stats
    return _stats()
