import { useState } from "react";
import { useLocation } from "react-router-dom";
import { Bot, X } from "lucide-react";

import ChatPanel from "./ChatPanel";

/** Floating chat button (bottom-right) that opens the assistant on any page. */
function ChatWidget() {
  const [open, setOpen] = useState(false);
  const location = useLocation();

  // The full-page assistant already shows the chat.
  if (location.pathname === "/chatbot") return null;

  return (
    <>
      {open && (
        <div className="fixed bottom-24 right-4 z-[60] w-[calc(100vw-2rem)] max-w-md overflow-hidden rounded-2xl border border-brand-100 bg-white shadow-2xl sm:right-6">
          <div className="flex items-center gap-3 bg-gradient-to-r from-brand-700 to-brand-600 px-4 py-3 text-white">
            <Bot size={22} />
            <div className="flex-1">
              <p className="font-bold leading-tight">ShopSense AI Assistant</p>
              <p className="text-xs text-brand-100">Search · Recommend · Compare · Reviews</p>
            </div>
            <button onClick={() => setOpen(false)} aria-label="Close chat" className="rounded-lg p-1 hover:bg-white/20">
              <X size={20} />
            </button>
          </div>
          <ChatPanel heightClass="h-[min(420px,55vh)]" onNavigate={() => setOpen(false)} />
        </div>
      )}

      <button
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? "Close ShopSense AI Assistant" : "Open ShopSense AI Assistant"}
        className="fixed bottom-6 right-4 z-[60] flex items-center gap-2 rounded-full bg-gradient-to-r from-brand-700 to-brand-600 px-5 py-4 text-white shadow-xl transition hover:scale-105 sm:right-6"
      >
        {open ? <X size={22} /> : <Bot size={22} />}
        <span className="font-semibold">{open ? "Close" : "Ask AI"}</span>
      </button>
    </>
  );
}

export default ChatWidget;
