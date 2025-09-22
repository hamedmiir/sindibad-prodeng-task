FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY autotag ./autotag

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "autotag.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
