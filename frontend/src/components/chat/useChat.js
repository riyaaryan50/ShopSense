import { useCallback, useEffect, useRef, useState } from "react";
import { io } from "socket.io-client";

import { NLP_URL, getCurrentUser, getToken } from "../../config";

let nextId = 1;
const makeId = () => nextId++;

/**
 * Real-time connection to the NLP chatbot (Flask-SocketIO namespace /chat).
 * Falls back to the REST endpoint POST /api/nlp/chat if the socket is down.
 */
export default function useChat() {
  const [messages, setMessages] = useState([]);
  const [connected, setConnected] = useState(false);
  const [typing, setTyping] = useState(false);
  const socketRef = useRef(null);
  const sessionId = useRef(null);

  const addBotMessage = useCallback((data) => {
    setTyping(false);
    setMessages((prev) => [...prev, { id: makeId(), sender: "bot", data }]);
  }, []);

  useEffect(() => {
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
                data: {
                  type: "text",
                  text: "Hi! I'm the ShopSense AI assistant (offline mode – using the REST API). Ask me to find, recommend or compare products.",
                  suggestions: ["Find wireless headphones under 3000", "Recommend something for me"],
                },
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

  return { messages, send, connected, typing };
}
