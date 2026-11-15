"""Gunicorn entry point: gunicorn -w 1 --threads 16 wsgi:app"""
from app import create_app

app = create_app()
