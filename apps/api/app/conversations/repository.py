from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import func, select
from sqlalchemy.engine import Engine

from apps.api.app.db.sqlalchemy_store import conversation_threads_table, messages_table
from apps.api.app.page_evidence.storage import SnapshotStorage

from .models import ConversationHistory, ConversationMessage, ConversationMessageRequest, CopilotTurn


class ConversationRepository(Protocol):
    def save_turn(
        self,
        analysis_id: UUID,
        request: ConversationMessageRequest,
        turn: CopilotTurn,
        metadata: dict[str, object],
    ) -> None:
        ...

    def load_history(self, analysis_id: UUID) -> ConversationHistory:
        ...


class SnapshotConversationRepository:
    def __init__(self, storage: SnapshotStorage) -> None:
        self._storage = storage

    def save_turn(
        self,
        analysis_id: UUID,
        request: ConversationMessageRequest,
        turn: CopilotTurn,
        metadata: dict[str, object],
    ) -> None:
        self._storage.save_copilot_turn(analysis_id, request, turn, metadata)

    def load_history(self, analysis_id: UUID) -> ConversationHistory:
        return self._storage.load_conversation_history(analysis_id)


class SqlAlchemyConversationRepository:
    """Postgres conversation source of truth with snapshot artifact mirroring."""

    def __init__(self, engine: Engine, storage: SnapshotStorage) -> None:
        self._engine = engine
        self._snapshot = SnapshotConversationRepository(storage)

    def save_turn(
        self,
        analysis_id: UUID,
        request: ConversationMessageRequest,
        turn: CopilotTurn,
        metadata: dict[str, object],
    ) -> None:
        thread_id = _default_thread_id(analysis_id)
        now = datetime.now().astimezone()
        with self._engine.begin() as connection:
            thread = connection.execute(
                select(conversation_threads_table)
                .where(conversation_threads_table.c.id == thread_id)
                .with_for_update()
            ).first()
            if thread is None:
                connection.execute(
                    conversation_threads_table.insert().values(
                        id=thread_id,
                        analysis_id=analysis_id,
                        title="Default",
                        created_at=now,
                        updated_at=now,
                    )
                )
                next_sequence = 1
            else:
                current = connection.execute(
                    select(func.max(messages_table.c.sequence)).where(messages_table.c.thread_id == thread_id)
                ).scalar_one_or_none()
                next_sequence = (current or 0) + 1
                connection.execute(
                    conversation_threads_table.update()
                    .where(conversation_threads_table.c.id == thread_id)
                    .values(updated_at=now)
                )
            connection.execute(
                messages_table.insert(),
                [
                    {
                        "id": uuid5(thread_id, f"message:{next_sequence}"),
                        "thread_id": thread_id,
                        "sequence": next_sequence,
                        "role": "user",
                        "content": request.message,
                        "turn_json": None,
                        "created_at": now,
                    },
                    {
                        "id": uuid5(thread_id, f"message:{next_sequence + 1}"),
                        "thread_id": thread_id,
                        "sequence": next_sequence + 1,
                        "role": "assistant",
                        "content": turn.answer,
                        "turn_json": turn.model_dump(mode="json"),
                        "created_at": now,
                    },
                ],
            )
        self._snapshot.save_turn(analysis_id, request, turn, metadata)

    def load_history(self, analysis_id: UUID) -> ConversationHistory:
        thread_id = _default_thread_id(analysis_id)
        with self._engine.begin() as connection:
            rows = connection.execute(
                select(messages_table)
                .where(messages_table.c.thread_id == thread_id)
                .order_by(messages_table.c.sequence)
            ).mappings().all()
        if not rows:
            return self._snapshot.load_history(analysis_id)
        messages = [ConversationMessage(role=row["role"], content=row["content"]) for row in rows]
        turns = [CopilotTurn.model_validate(row["turn_json"]) for row in rows if row["turn_json"] is not None]
        return ConversationHistory(analysis_id=analysis_id, messages=messages, turns=turns)


def _default_thread_id(analysis_id: UUID) -> UUID:
    return uuid5(NAMESPACE_URL, f"geo-copilot:{analysis_id}:default")
