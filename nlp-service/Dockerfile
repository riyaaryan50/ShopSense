FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    HF_HOME=/app/.cache/huggingface \
    NLP_HOST=0.0.0.0 \
    NLP_PORT=5002

# CPU-only torch keeps the image small (~1GB instead of ~5GB with CUDA).
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bake the MiniLM model into the image so startup does not need the internet.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

COPY . .

EXPOSE 5002
# One worker: Socket.IO sessions and the FAISS index live in process memory.
CMD ["gunicorn", "--worker-class", "gthread", "--threads", "16", "-w", "1", \
     "-b", "0.0.0.0:5002", "--timeout", "120", "wsgi:app"]
