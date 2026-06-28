from pathlib import Path
from uuid import uuid4

from apps.api.app.conversations.models import ConversationMessageRequest, CopilotTurn
from apps.api.app.conversations.repository import SqlAlchemyConversationRepository
from apps.api.app.db.models import AnalysisRecord
from apps.api.app.db.sqlalchemy_store import SqlAlchemyAnalysisRepository, create_sqlalchemy_engine
from apps.api.app.page_evidence.storage import SnapshotStorage


def test_sqlalchemy_conversation_repository_round_trip(tmp_path: Path) -> None:
    engine = create_sqlalchemy_engine(f"sqlite:///{tmp_path / 'conversation.db'}")
    storage = SnapshotStorage(tmp_path / "snapshots")
    analyses = SqlAlchemyAnalysisRepository(engine, storage)
    analyses.create_schema()
    analysis_id = uuid4()
    analyses.save_record(
        AnalysisRecord(
            analysis_id=analysis_id,
            input_url="https://example.com/",
            status="completed",
            language="zh-CN",
        )
    )
    repository = SqlAlchemyConversationRepository(engine, storage)
    request = ConversationMessageRequest(message="先改什么？")
    turn = CopilotTurn(
        turn_id=uuid4(),
        analysis_id=analysis_id,
        intent="ask_unknown",
        answer="需要更多证据。",
        evidence_refs=[],
        method_refs=[],
    )

    repository.save_turn(analysis_id, request, turn, {"created_at": "2026-06-28T00:00:00Z"})
    history = repository.load_history(analysis_id)

    assert [message.role for message in history.messages] == ["user", "assistant"]
    assert history.messages[0].content == request.message
    assert history.turns == [turn]
    assert storage.load_conversation_history(analysis_id) == history
