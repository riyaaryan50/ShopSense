import { useEffect, useRef, useState } from "react";
import { Send, Sparkles } from "lucide-react";

import ChatMessage from "./ChatMessage";
import useChat from "./useChat";

const STARTERS = [
  "Find wireless headphones under 3000",
  "Recommend something for me",
  "Compare Galaxy Tab A9 and Tab S9 FE",
  "What do people say about the HP printer?",
];

/** Full chat UI used by both the floating widget and the /chatbot page. */
function ChatPanel({ heightClass = "h-[460px]", onNavigate }) {
  const { messages, send, connected, typing, transport } = useChat();
  const [input, setInput] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, typing]);

  const lastBot = [...messages].reverse().find((m) => m.sender === "bot");
  const suggestions = lastBot?.data?.suggestions?.length
    ? lastBot.data.suggestions
    : STARTERS;

  const submit = (text) => {
    send(text);
    setInput("");
  };

  return (
    <div className="flex flex-col">
      <div className="flex items-center justify-end gap-2 border-b border-violet-50 bg-white px-4 py-1.5 text-[11px] text-gray-500">
        <span
          className={`h-2 w-2 rounded-full ${
            connected || transport === "rest" ? "bg-green-500" : "bg-amber-400"
          }`}
        />
        {transport === "rest"
          ? "Online (REST)"
          : connected
            ? "Live (WebSocket)"
            : "Connecting… (REST fallback)"}
      </div>

      <div className={`${heightClass} space-y-4 overflow-y-auto bg-slate-50 p-4`}>
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} onNavigate={onNavigate} />
        ))}
        {typing && (
          <div className="flex items-center gap-1 pl-10 text-violet-400" aria-label="Assistant is typing">
            <span className="h-2 w-2 animate-bounce rounded-full bg-violet-400" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-violet-400 [animation-delay:0.15s]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-violet-400 [animation-delay:0.3s]" />
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-gray-100 bg-white px-4 pt-3">
        <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-gray-500">
          <Sparkles size={13} className="text-violet-600" /> Try asking
        </p>
        <div className="flex gap-2 overflow-x-auto pb-2">
          {suggestions.slice(0, 4).map((s) => (
            <button
              key={s}
              onClick={() => submit(s)}
              className="shrink-0 rounded-full border border-violet-200 px-3 py-1.5 text-xs font-medium text-violet-700 transition hover:bg-violet-50"
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit(input);
        }}
        className="flex items-center gap-2 bg-white p-3"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about products, reviews, comparisons…"
          aria-label="Chat message"
          className="min-w-0 flex-1 rounded-xl border border-violet-200 bg-gray-50 px-3 py-2.5 text-sm outline-none focus:border-violet-500"
        />
        <button
          type="submit"
          disabled={!input.trim()}
          aria-label="Send message"
          className="rounded-xl bg-violet-700 p-2.5 text-white transition hover:bg-violet-800 disabled:opacity-40"
        >
          <Send size={18} />
        </button>
      </form>
    </div>
  );
}

export default ChatPanel;
