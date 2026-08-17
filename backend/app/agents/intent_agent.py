from sqlalchemy.orm import Session
from app.agents.base import AgentContext, BaseAgent
from app.rag.retrieval import RetrievalService


class RAGAgent(BaseAgent):
    name = "rag_agent"

    def __init__(self, db: Session):
        self.db = db

    async def _run(self, context: AgentContext):
        query = context.query or "Find evidence for applicant property recommendation"
        return RetrievalService(self.db).query(
            query=query,
            limit=context.limit,
            applicant_id=context.applicant_id,
            property_id=context.property_id,
        )

