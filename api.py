from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
import uvicorn

from main import process_search, process_single_url
from src.extraction.schema import FOARecord

app = FastAPI(
    title="FOA Intelligence API",
    description="API for ingesting and semantically tagging Funding Opportunity Announcements.",
    version="1.0.0"
)

# ──────────────────────────────────────────────────────────────
# Models
# ──────────────────────────────────────────────────────────────
class SearchRequest(BaseModel):
    query: str
    source: str = "grants_gov"
    max_results: int = 10
    use_embeddings: bool = False

# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "message": "Welcome to the FOA Intelligence API",
        "docs": "/docs",
        "endpoints": ["/search", "/ingest-url"]
    }

@app.get("/search", response_model=List[FOARecord])
async def search_foas(
    q: str = Query(..., description="Search keywords"),
    source: str = Query("grants_gov", enum=["grants_gov", "nsf"]),
    limit: int = Query(10, ge=1, le=50),
    use_embeddings: bool = Query(False)
):
    """Search for funding opportunities across supported sources."""
    try:
        records = process_search(
            keyword=q,
            source=source,
            max_results=limit,
            use_embeddings=use_embeddings
        )
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ingest-url", response_model=FOARecord)
async def ingest_url(
    url: str = Query(..., description="Full FOA URL"),
    use_embeddings: bool = Query(False)
):
    """Ingest and analyze a single FOA by URL."""
    try:
        record = process_single_url(url, use_embeddings=use_embeddings)
        return record
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
