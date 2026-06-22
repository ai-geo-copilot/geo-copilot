"use client";

import { FormEvent, useEffect, useState } from "react";
import type { ConversationHistory, ConversationMessageRequest } from "../../types/api";
import { RefChipList } from "./ref-chip";

type CopilotThreadProps = {
  history: ConversationHistory | null;
  error: string | null;
  sending: boolean;
  disabled: boolean;
  disabledReason?: string | null;
  selectedRef: string | null;
  onSend: (input: ConversationMessageRequest) => Promise<void>;
  onSelectRef: (value: string) => void;
};

export function CopilotThread({
  history,
  error,
  sending,
  disabled,
  disabledReason,
  selectedRef,
  onSend,
  onSelectRef,
}: CopilotThreadProps) {
  const [message, setMessage] = useState("");
  const [pendingMessage, setPendingMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const next = message.trim();
    if (!next) {
      return;
    }
    setPendingMessage(next);
    setMessage("");
    await onSend({ message: next, intent: "auto" });
  }

  useEffect(() => {
    setPendingMessage(null);
  }, [history]);

  return (
    <>
      <div className="thread">
        {error ? <p className="error-text">{error}</p> : null}
        {(history?.messages ?? []).length === 0 && !pendingMessage ? (
          <p className="muted">完成分析后可以围绕页面证据追问。</p>
        ) : (
          <>
            {history?.messages.map((item, index) => (
              <article className={`message ${item.role}`} key={`${item.role}-${index}`}>
                <strong>{item.role === "user" ? "你" : "Copilot"}</strong>
                <p>{item.content}</p>
                {item.role === "assistant" ? renderAssistantExtras(history, index, selectedRef, onSelectRef, setMessage) : null}
              </article>
            ))}
            {pendingMessage ? (
              <article className="message user">
                <strong>你</strong>
                <p>{pendingMessage}</p>
              </article>
            ) : null}
          </>
        )}
        {sending ? <p className="muted loading-indicator">正在生成回答...</p> : null}
      </div>
      <form className="composer" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="例如：优先改哪三个问题？"
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          disabled={disabled}
        />
        <button type="submit" disabled={disabled || sending}>
          发送
        </button>
      </form>
      {disabledReason ? <p className="disabled-reason">{disabledReason}</p> : null}
    </>
  );
}

function renderAssistantExtras(
  history: ConversationHistory,
  messageIndex: number,
  selectedRef: string | null,
  onSelectRef: (value: string) => void,
  setMessage: (value: string) => void,
) {
  const turn = getTurnForAssistantMessage(history, messageIndex);
  if (!turn) {
    return null;
  }

  const allRefs = [...turn.method_refs, ...turn.evidence_refs];

  return (
    <>
      {allRefs.length > 0 ? (
        <RefChipList refs={allRefs} selectedRef={selectedRef} onSelectRef={onSelectRef} />
      ) : null}
      {turn.follow_up_suggestions.length > 0 ? (
        <div className="follow-up-list">
          {turn.follow_up_suggestions.map((suggestion, i) => (
            <button
              key={i}
              type="button"
              className="follow-up-chip"
              onClick={() => setMessage(suggestion)}
            >
              {suggestion}
            </button>
          ))}
        </div>
      ) : null}
      {turn.unknowns.length > 0 ? (
        <div>
          {turn.unknowns.map((u) => (
            <div key={u.unknown_id} className="unknown-item">
              <strong>{u.question}</strong>
              <p>{u.reason}</p>
              <RefChipList refs={u.evidence_refs} selectedRef={selectedRef} onSelectRef={onSelectRef} />
            </div>
          ))}
        </div>
      ) : null}
    </>
  );
}

function getTurnForAssistantMessage(history: ConversationHistory, messageIndex: number) {
  const assistantIndex =
    history.messages.slice(0, messageIndex + 1).filter((msg) => msg.role === "assistant").length - 1;
  return history.turns[assistantIndex] ?? null;
}
