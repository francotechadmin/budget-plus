# FastAPI Dockerfile
FROM python:3.9

WORKDIR /app
COPY . /app

RUN pip install fastapi uvicorn pandas matplotlib mplcursors python-multipart elasticsearch sqlalchemy psycopg2 openpyxl

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
