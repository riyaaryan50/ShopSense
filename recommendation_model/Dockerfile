# Content-based (Member 1) + SVD (Member 2) recommendation API on port 5001.
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY . .
EXPOSE 5001
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5001", "recommendation_api:app"]
