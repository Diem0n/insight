FROM python:3.11-slim

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python scripts/seed_db.py

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "app/streamlit_app.py", \
            "--server.port=8501", \
            "--server.address=0.0.0.0", \
            "--server.headless=true"]
