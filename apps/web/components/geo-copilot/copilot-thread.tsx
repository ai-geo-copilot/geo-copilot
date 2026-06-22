"use client";

import { FormEvent, useState } from "react";
import type { ConversationHistory, ConversationMessageRequest } from "../../types/api";
import { RefChipList } from "./ref-chip";

type CopilotThreadProps = {
  history: ConversationHistory | null;
  error: string | null;
  sending: boolean;
  disabled: boolean;
  selectedRef: string | null;
  onSend: (input: ConversationMessageRequest) => Promise<void>;
  onSelectRef: (value: string) => void;
};

export function CopilotThread({
  history,
  error,
  sending,
  disabled,
  selectedRef,
  onSend,
  onSelectRef,
}: CopilotThreadProps) {
  const [message, setMessage] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const next = message.trim();
    if (!next) {
      return;
    }
    await onSend({ message: next, intent: "auto" });
    setMessage("");
  }

  return (
    <>
      <div className="thread">
        {error ? <p className="error-text">{error}</p> : null}
        {(history?.messages ?? []).length === 0 ? (
          <p className="muted">完成分析后可以围绕页面证据追问。</p>
        ) : (
          history?.messages.map((item, index) => (
            <article className={`message ${item.role}`} key={`${item.role}-${index}`}>
              <strong>{item.role === "user" ? "你" : "Copilot"}</strong>
              <p>{item.content}</p>
              {item.role === "assistant" && getTurnForAssistantMessage(history, index) ? (
                <RefChipList
                  refs={[
                    ...getTurnForAssistantMessage(history, index)!.method_refs,
                    ...getTurnForAssistantMessage(history, index)!.evidence_refs,
                  ]}
                  selectedRef={selectedRef}
                  onSelectRef={onSelectRef}
                />
              ) : null}
            </article>
          ))
        )}
        {sending ? <p className="muted">正在生成回答...</p> : null}
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
    </>
  );
}

function getTurnForAssistantMessage(history: ConversationHistory, messageIndex: number) {
  const assistantIndex = history.messages
    .slice(0, messageIndex + 1)
    .filter((message) => message.role === "assistant").length - 1;
  return history.turns[assistantIndex] ?? null;
}
