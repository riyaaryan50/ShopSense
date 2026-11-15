"""ShopSense NLP microservice (Member 4).

REST
    GET  /health
    POST /api/nlp/search                      {query, top_k, category?, min_price?, max_price?}
    GET  /api/nlp/similar/<product_id>?top_k=5
    POST /api/nlp/sentiment                   {text} or {texts: [...]}
    GET  /api/nlp/reviews/<product_id>/summary?include_reviews=true
    POST /api/nlp/survey/recommend            {answers, top_k?, exclude_ids?}
    POST /api/nlp/chat                        {message, context?}  (REST fallback for the socket)
    POST /api/nlp/reindex                     rebuild FAISS + clear caches

WebSocket (Flask-SocketIO, namespace /chat)
    client -> "message"  {text, token?, user_name?}
    server -> "response" {intent, type, text, products, comparison, summary, suggestions}
"""

import logging
import time

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit

import config
from chatbot.handlers import ChatEngine
from common.services import NLPServices, product_card
from survey.recommender import survey_recommend

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("nlp-service")

socketio = SocketIO(cors_allowed_origins=config.CORS_ORIGINS, async_mode="threading")


def _int_arg(value, default, low, high):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, value))


def _float_or_none(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def create_app(services=None):
    app = Flask(__name__)
    CORS(app, origins=config.CORS_ORIGINS)

    services = services or NLPServices()
    services.sync()
    chat = ChatEngine(services)
    app.extensions["nlp_services"] = services
    app.extensions["chat_engine"] = chat
    sessions = {}

    # ------------------------------------------------------------------ #
    @app.get("/health")
    def health():
        return jsonify({
            "status": "healthy",
            "service": "shopsense-nlp",
            "embedding_engine": services.index.engine,
            "indexed_products": services.index.size,
            "sentiment_model": services.analyzer.name,
            "data_source": services.data.last_source,
        })

    @app.post("/api/nlp/search")
    def semantic_search():
        body = request.get_json(silent=True) or {}
        query = str(body.get("query") or "").strip()
        if not query:
            return jsonify({"error": "query is required"}), 400
        top_k = _int_arg(body.get("top_k"), 10, 1, 50)

        services.sync()
        started = time.perf_counter()
        hits = services.index.search(
            query, top_k=top_k, category=body.get("category"),
            min_price=_float_or_none(body.get("min_price")),
            max_price=_float_or_none(body.get("max_price")),
            min_score=_float_or_none(body.get("min_score")),
        )
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        results = [product_card(services.product(h["product_id"]), score=h["score"])
                   for h in hits]
        return jsonify({
            "query": query,
            "results": results,
            "product_ids": [h["product_id"] for h in hits],
            "scores": [h["score"] for h in hits],
            "total": len(results),
            "engine": services.index.engine,
            "latency_ms": latency_ms,
        })

    @app.get("/api/nlp/similar/<int:product_id>")
    def similar(product_id):
        services.sync()
        top_k = _int_arg(request.args.get("top_k"), 5, 1, 20)
        hits = services.index.similar(product_id, top_k=top_k)
        if hits is None:
            return jsonify({"error": "Product not found"}), 404
        return jsonify({
            "product_id": product_id,
            "recommendations": [product_card(services.product(h["product_id"]),
                                             similarity_score=h["score"]) for h in hits],
            "engine": services.index.engine,
        })

    @app.post("/api/nlp/sentiment")
    def sentiment():
        body = request.get_json(silent=True) or {}
        if isinstance(body.get("texts"), list):
            return jsonify({"results": [services.analyzer.analyze(str(t))
                                        for t in body["texts"][:500]]})
        text = str(body.get("text") or "").strip()
        if not text:
            return jsonify({"error": "text or texts is required"}), 400
        return jsonify(services.analyzer.analyze(text))

    @app.get("/api/nlp/reviews/<int:product_id>/summary")
    def review_summary(product_id):
        include = request.args.get("include_reviews", "false").lower() in ("1", "true", "yes")
        fresh = request.args.get("fresh", "false").lower() in ("1", "true", "yes")
        summary = services.review_summary(product_id, include_reviews=include, force=fresh)
        if summary is None:
            return jsonify({"error": "Product not found"}), 404
        return jsonify(summary)

    @app.post("/api/nlp/survey/recommend")
    def survey():
        body = request.get_json(silent=True) or {}
        answers = body.get("answers")
        if not isinstance(answers, dict):
            return jsonify({"error": "answers object is required"}), 400
        top_k = _int_arg(body.get("top_k"), 8, 1, 20)
        result = survey_recommend(answers, services, top_k=top_k,
                                  exclude_ids=body.get("exclude_ids"))
        for item in result["recommendations"]:
            item["product"] = product_card(services.product(item["product_id"]))
        return jsonify(result)

    @app.post("/api/nlp/chat")
    def chat_rest():
        body = request.get_json(silent=True) or {}
        message = str(body.get("message") or "")
        session_id = str(body.get("session_id") or "rest")
        context = sessions.setdefault(session_id, {})
        context["token"] = _bearer(request) or body.get("token")
        context["user_name"] = body.get("user_name")
        return jsonify(chat.respond(message, context))

    @app.post("/api/nlp/reindex")
    def reindex():
        services.invalidate()
        rebuilt = services.sync(force=True)
        return jsonify({"rebuilt": rebuilt, "indexed_products": services.index.size,
                        "engine": services.index.engine})

    @app.post("/api/nlp/reviews/<int:product_id>/invalidate")
    def invalidate_reviews(product_id):
        services.invalidate(product_id)
        return jsonify({"invalidated": product_id})

    # ------------------------------------------------------------------ #
    # Socket.IO chat
    # ------------------------------------------------------------------ #
    @socketio.on("connect", namespace="/chat")
    def on_connect():
        sessions[request.sid] = {}
        emit("response", {
            "intent": "greeting", "type": "text", "products": [],
            "text": "Hi! I'm the ShopSense AI assistant. Ask me to find, recommend or "
                    "compare products, or ask what customers think about one.",
            "suggestions": ["Find wireless headphones under 3000",
                            "Recommend something for me",
                            "Compare Galaxy Tab A9 and Tab S9 FE"],
        })

    @socketio.on("disconnect", namespace="/chat")
    def on_disconnect(*_args):
        sessions.pop(request.sid, None)

    @socketio.on("message", namespace="/chat")
    def on_message(data):
        if isinstance(data, str):
            data = {"text": data}
        data = data or {}
        context = sessions.setdefault(request.sid, {})
        if data.get("token"):
            context["token"] = data["token"]
        if data.get("user_name"):
            context["user_name"] = data["user_name"]
        emit("typing", {"typing": True})
        response = chat.respond(str(data.get("text") or ""), context)
        emit("response", response)

    socketio.init_app(app)
    return app


def _bearer(req):
    header = req.headers.get("Authorization", "")
    return header.split(" ", 1)[1] if header.startswith("Bearer ") else None


if __name__ == "__main__":
    application = create_app()
    log.info("NLP service on http://%s:%s", config.HOST, config.PORT)
    socketio.run(application, host=config.HOST, port=config.PORT,
                 allow_unsafe_werkzeug=True)
