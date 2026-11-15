// Service URLs. Override with VITE_API_URL / VITE_NLP_URL in frontend/.env
export const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:5000/api";

// Member 4's NLP service: semantic search, review sentiment and the chatbot
// WebSocket (Socket.IO namespace /chat).
export const NLP_URL =
  import.meta.env.VITE_NLP_URL || "http://127.0.0.1:5002";

export function getToken() {
  return (
    localStorage.getItem("access_token") ||
    sessionStorage.getItem("access_token")
  );
}

export function getCurrentUser() {
  try {
    const raw = localStorage.getItem("user") || sessionStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export const formatPrice = (value) =>
  `₹${Number(value || 0).toLocaleString("en-IN")}`;
