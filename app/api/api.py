from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import List
import os
import uuid
import sqlite3
from app.rag.insights import generate_insights
from app.rag.ingest import ingest_document, extract_text_from_pdf
from app.rag.embeddings import get_embedding
from app.rag.retrieve import search
from rag_store import open_store, delete_document_chunks
from app.rag.pipeline import RAGPipeline
from app.rag.faithfulness import FaithfulnessEvaluator
from app.rag.night_optimizer import NightOptimizer
pipeline = RAGPipeline()
optimizer = NightOptimizer()
faithfulness_evaluator = FaithfulnessEvaluator()
router = APIRouter()

class HighlightRequest(BaseModel):
    highlight: str

class SearchRequest(BaseModel):
    highlight: str
    top_k: int = Field(default=5, ge=1, le=50)

class InsightsResponse(BaseModel):
    key_takeaways: List[str]
    did_you_know: List[str]
    contradictions: List[str]
    examples: List[str]
    inspirations: List[str]

@router.post("/rag/insights", response_model=InsightsResponse)
async def get_insights(req: HighlightRequest):
    result = generate_insights(req.highlight)
    return {
        "key_takeaways": result.get("key_takeaways", []),
        "did_you_know": result.get("did_you_know", []),
        "contradictions": result.get("contradictions", []),
        "examples": result.get("examples", []),
        "inspirations": result.get("inspirations", [])
    }

@router.post("/rag/search_snippets")
async def search_snippets(req: SearchRequest):
    """
    Configurable top_k search.
    NOTE: retrieve.search must accept top_k and use it.
    """
    query_emb = get_embedding(req.highlight)
    results = search(req.highlight, query_emb, top_k=req.top_k)
    return {"results": results}
@router.post("/rag/query")
async def rag_query(req: SearchRequest):

    result = pipeline.process_query(
        query=req.highlight,
        top_k=req.top_k
    )

    return result
@router.post("/rag/evaluate_faithfulness")
async def evaluate_faithfulness(req: SearchRequest):

    # =========================
    # RUN EXISTING PIPELINE
    # =========================

    result = pipeline.process_query(
        query=req.highlight,
        top_k=req.top_k
    )

    generated_answer = result["answer"]

    retrieved_docs = result["retrieved_docs"]

    # =========================
    # EXTRACT GENERATED TEXT
    # =========================

    generated_text_parts = []

    generated_text_parts.extend(
        generated_answer.get(
            "key_takeaways",
            []
        )
    )

    generated_text_parts.extend(
        generated_answer.get(
            "did_you_know",
            []
        )
    )

    generated_text_parts.extend(
        generated_answer.get(
            "examples",
            []
        )
    )

    generated_text = ". ".join(
        generated_text_parts
    )

    # =========================
    # RUN FAITHFULNESS CHECK
    # =========================

    faithfulness_result = (
        faithfulness_evaluator.evaluate(
            generated_text,
            retrieved_docs
        )
    )

    return {

        "query": req.highlight,

        "generated_answer": generated_answer,

        "faithfulness": faithfulness_result,

        "retrieved_docs": retrieved_docs
    }
@router.get("/rag/night_optimizer")
async def night_optimizer():

    result = optimizer.analyze_system()

    return result
@router.post("/rag/ingest_pdfs")
async def ingest_pdfs(files: List[UploadFile] = File(...)):
    total_chunks = 0
    uploaded_files = []

    upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    for file in files:
        file_path = os.path.join(upload_dir, f"{uuid.uuid4()}_{file.filename}")

        with open(file_path, "wb") as f:
            f.write(await file.read())

        text = extract_text_from_pdf(file_path)
        chunks = ingest_document(file.filename, text)

        total_chunks += chunks
        uploaded_files.append({"filename": file.filename, "chunks": chunks})

        os.remove(file_path)

    return {
        "message": f"Successfully ingested {len(files)} PDF(s) with {total_chunks} total chunks",
        "files": uploaded_files,
        "total_chunks": total_chunks
    }

@router.get("/rag/list_documents")
async def list_documents():
    """List all documents with their chunk counts."""
    store = open_store()
    doc_counts = {}

    for _, entry in store.items():
        doc_name = entry.get("metadata", {}).get("doc", "Unknown")
        doc_counts[doc_name] = doc_counts.get(doc_name, 0) + 1

    store.close()

    documents = [{"name": name, "chunks": count} for name, count in doc_counts.items()]
    return {"documents": documents, "total_documents": len(documents)}

@router.delete("/rag/documents/{doc_name}")
async def delete_document(doc_name: str):
    """
    Delete all chunks for a document by matching metadata.doc == doc_name.
    """
    stats = delete_document_chunks(doc_name)
    if stats["deleted_chunks"] == 0:
        raise HTTPException(status_code=404, detail=f"No chunks found for document: {doc_name}")
    return {"message": f"Deleted '{doc_name}' ({stats['deleted_chunks']} chunks)", **stats}

@router.delete("/rag/clear_database")
async def clear_database():
    """Clear all documents from the database."""
    try:
        store = open_store()
        store.clear()
        store.commit()
        store.close()
        return {"message": "Database cleared successfully"}
    except Exception as e:
        return {"error": str(e)}
    
@router.get("/rag/metrics")
async def get_metrics():

    conn = sqlite3.connect("rag_metrics.db")

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM query_metrics")

    rows = cursor.fetchall()

    conn.close()

    metrics = []

    for row in rows:

        metrics.append(dict(row))

    return {

        "metrics": metrics,

        "total_queries": len(metrics)

    }
@router.get("/rag/analytics")
async def analytics():

    conn = sqlite3.connect("rag_metrics.db")

    cursor = conn.cursor()

    # =========================
    # TOTAL QUERIES
    # =========================

    cursor.execute("""
        SELECT COUNT(*)
        FROM query_metrics
    """)

    total_queries = cursor.fetchone()[0]

    # =========================
    # AVG TOTAL LATENCY
    # =========================

    cursor.execute("""
        SELECT AVG(total_latency_ms)
        FROM query_metrics
    """)

    avg_total_latency = cursor.fetchone()[0]

    # =========================
    # AVG RETRIEVAL LATENCY
    # =========================

    cursor.execute("""
        SELECT AVG(retrieval_latency_ms)
        FROM query_metrics
    """)

    avg_retrieval_latency = cursor.fetchone()[0]

    # =========================
    # AVG GENERATION LATENCY
    # =========================

    cursor.execute("""
        SELECT AVG(generation_latency_ms)
        FROM query_metrics
    """)

    avg_generation_latency = cursor.fetchone()[0]

    # =========================
    # MAX LATENCY
    # =========================

    cursor.execute("""
        SELECT MAX(total_latency_ms)
        FROM query_metrics
    """)

    max_latency = cursor.fetchone()[0]

    # =========================
    # MIN LATENCY
    # =========================

    cursor.execute("""
        SELECT MIN(total_latency_ms)
        FROM query_metrics
    """)

    min_latency = cursor.fetchone()[0]
  # =========================
    # P95 LATENCY
    # =========================

    cursor.execute("""
        SELECT total_latency_ms
        FROM query_metrics
        ORDER BY total_latency_ms
    """)

    latencies = [row[0] for row in cursor.fetchall()]

    p95_latency = None

    if latencies:

        index = int(0.95 * len(latencies)) - 1

        index = max(index, 0)

        p95_latency = latencies[index]
    conn.close()
    
  

    return {

        "total_queries": total_queries,

        "avg_total_latency_ms": avg_total_latency,

        "avg_retrieval_latency_ms": avg_retrieval_latency,

        "avg_generation_latency_ms": avg_generation_latency,

        "max_latency_ms": max_latency,

        "min_latency_ms": min_latency,
        "p95_latency_ms": p95_latency
    }