from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.rag.retrieval import RetrievalService
from app.rag.provenance import get_provenance
from app.schemas.domain import SearchRequest

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query")
def rag_query(request: SearchRequest, db: Session = Depends(get_db)):
    return RetrievalService(db).query(request.query, request.limit, request.applicant_id, request.property_id)


@router.get("/provenance/{citation_id}")
def rag_provenance(citation_id: str, query: str | None = None, db: Session = Depends(get_db)):
    try:
        return get_provenance(db, citation_id, query)
    except KeyError:
        raise HTTPException(status_code=404, detail={"error_code": "CITATION_NOT_FOUND", "message": "Run the RAG query first or provide its query parameter."}) from None
    except LookupError as exc:
        raise HTTPException(status_code=404, detail={"error_code": "SOURCE_NOT_FOUND", "message": str(exc)}) from None
