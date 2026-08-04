FROM python:3.12-slim

WORKDIR /app
RUN mkdir -p /app/data
COPY pyproject.toml ./
COPY app ./app

RUN pip install --no-cache-dir uv && uv pip install --system .

ENV AGENTS_HOST=0.0.0.0
ENV AGENTS_PORT=8081
EXPOSE 8081

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"]
