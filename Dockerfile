FROM python:3.11
WORKDIR /app

COPY poetry.lock pyproject.toml /app/
RUN pip install poetry
RUN poetry install
COPY app /app/app

EXPOSE 8000
CMD ["poetry", "run", "gunicorn", "app.main:app", "--workers", "4", "--threads", "16", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
