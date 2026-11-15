import { API_URL, getToken } from "../config";

async function request(path, { method = "GET", body, auth = false } = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (auth && token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  let data = {};
  try {
    data = await response.json();
  } catch {
    /* empty body */
  }
  if (!response.ok) {
    const error = new Error(data.error || data.msg || `Request failed (${response.status})`);
    error.status = response.status;
    throw error;
  }
  return data;
}

// ---- Semantic search (Member 4 via backend proxy) -------------------------
export const semanticSearch = (query, topK = 12) =>
  request("/search/semantic", { method: "POST", body: { query, top_k: topK } });

// ---- Review sentiment summary (Member 4) ----------------------------------
export const getReviewSummary = (productId) =>
  request(`/reviews/${productId}/summary?include_reviews=true`);

export const submitReview = (productId, rating, comment) =>
  request("/reviews/", {
    method: "POST",
    auth: true,
    body: { product_id: productId, rating, comment },
  });

// ---- Recommendations ------------------------------------------------------
export const getMyRecommendations = (limit = 10) =>
  request(`/recommendations/me?limit=${limit}`, { auth: true });

export const getPopular = (limit = 10) =>
  request(`/recommendations/popular?limit=${limit}`);

export const getSimilarProducts = (productId, limit = 5) =>
  request(`/similar/${productId}?limit=${limit}`);

// ---- Survey ---------------------------------------------------------------
const GUEST_SURVEY_KEY = "shopsense_survey_answers";

export const saveSurvey = (answers) =>
  request("/survey/", { method: "POST", auth: true, body: { answers } });

export const getSavedSurvey = async () => {
  if (getToken()) {
    try {
      return (await request("/survey/", { auth: true })).answers;
    } catch (error) {
      if (error.status !== 404) throw error;
    }
  }
  try {
    const raw = localStorage.getItem(GUEST_SURVEY_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

export const storeGuestSurvey = (answers) => {
  try {
    localStorage.setItem(GUEST_SURVEY_KEY, JSON.stringify(answers));
  } catch {
    /* storage unavailable */
  }
};

export const getSurveyRecommendations = (answers, topK = 8) =>
  request("/survey/recommendations", {
    method: "POST",
    auth: true,
    body: answers ? { answers, top_k: topK } : { top_k: topK },
  });
