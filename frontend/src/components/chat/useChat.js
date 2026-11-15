import { useCallback, useEffect, useRef, useState } from "react";
import { io } from "socket.io-client";

import { CHAT_TRANSPORT, NLP_URL, getCurrentUser, getToken } from "../../config";

const REST_ONLY = CHAT_TRANSPORT === "rest";

const GREETING = {
  type: "text",
  text: "Hi! I'm the ShopSense AI assistant. Ask me to find, recommend or compare products, or what customers think about one.",
  suggestions: [
    "Find wireless headphones under 3000",
    "Recommend something for me",
    "Compare Galaxy Tab A9 and Tab S9 FE",
    "What do people say about the HP printer?",
  ],
};

let nextId = 1;
const makeId = () => nextId++;

/**
 * Real-time connection to the NLP chatbot (Flask-SocketIO namespace /chat).
 * Falls back to the REST endpoint POST /api/nlp/chat if the socket is down.
 */
export default function useChat() {
  const [messages, setMessages] = useState(() =>
    REST_ONLY ? [{ id: makeId(), sender: "bot", data: GREETING }] : []
  );
  const [connected, setConnected] = useState(false);
  const [typing, setTyping] = useState(false);
  const socketRef = useRef(null);
  const sessionId = useRef(null);

  const addBotMessage = useCallback((data) => {
    setTyping(false);
    setMessages((prev) => [...prev, { id: makeId(), sender: "bot", data }]);
  }, []);

  useEffect(() => {
    if (REST_ONLY) return undefined;
    const socket = io(`${NLP_URL}/chat`, {
      transports: ["websocket", "polling"],
      reconnectionAttempts: 5,
      timeout: 5000,
    });
    socketRef.current = socket;

    socket.on("connect", () => setConnected(true));
    socket.on("disconnect", () => setConnected(false));
    socket.on("typing", () => setTyping(true));
    socket.on("response", addBotMessage);
    socket.on("connect_error", () => {
      setConnected(false);
      setMessages((prev) =>
        prev.length
          ? prev
          : [
              {
                id: makeId(),
                sender: "bot",
                data: GREETING,
              },
            ]
      );
    });

    return () => socket.disconnect();
  }, [addBotMessage]);

  const send = useCallback(
    async (text) => {
      const trimmed = (text || "").trim();
      if (!trimmed) return;

      setMessages((prev) => [...prev, { id: makeId(), sender: "user", text: trimmed }]);
      const user = getCurrentUser();
      const payload = {
        text: trimmed,
        token: getToken() || undefined,
        user_name: user?.name,
      };

      const socket = socketRef.current;
      if (socket?.connected) {
        setTyping(true);
        socket.emit("message", payload);
        return;
      }

      setTyping(true);
      if (!sessionId.current) {
        sessionId.current = `rest-${Math.random().toString(36).slice(2)}`;
      }
      try {
        const response = await fetch(`${NLP_URL}/api/nlp/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: trimmed,
            token: payload.token,
            user_name: payload.user_name,
            session_id: sessionId.current,
          }),
        });
        addBotMessage(await response.json());
      } catch {
        addBotMessage({
          type: "text",
          text: "I can't reach the AI service right now. Please make sure the NLP service is running on port 5002.",
        });
      }
    },
    [addBotMessage]
  );

  return { messages, send, connected, typing, transport: REST_ONLY ? "rest" : "websocket" };
}
