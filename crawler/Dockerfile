FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt backend_requirements.txt
RUN pip install --no-cache-dir -r backend_requirements.txt

COPY crawler/requirements.txt crawler_requirements.txt
RUN pip install --no-cache-dir -r crawler_requirements.txt

# backend app 模块（crawler 依赖 app.models/core）
COPY backend/app ./app
COPY crawler ./crawler

CMD ["python", "crawler/main.py"]
