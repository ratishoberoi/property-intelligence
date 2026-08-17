from app.rag.answer import GroundedAnswerGenerator
from app.schemas.intelligence import Citation


def _citation(text: str) -> Citation:
    return Citation(source="Synthetic conversation", document_type="conversation", excerpt=text)


def test_unanswerable_personal_questions_refuse_without_supported_fact():
    generator = GroundedAnswerGenerator()
    for question in (
        "Did Sarah tell the agent she owns a Tesla?",
        "What is Sarah's exact salary?",
        "What school does Sarah's child attend?",
        "Did Sarah say she has two dogs?",
        "Does Sarah own a Tesla?",
    ):
        result = generator.generate(question, "", [_citation("Sarah asked about transport and tenancy terms.")], [])
        assert "do not establish" in result.answer.lower()
        assert "tesla" not in result.answer.lower()
        assert "salary" not in result.answer.lower()


def test_no_evidence_returns_safe_answer():
    result = GroundedAnswerGenerator().generate("What is Sarah's exact salary?", "", [], [])
    assert "could not retrieve enough evidence" in result.answer.lower()
