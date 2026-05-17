FROM python:3.10

WORKDIR /app

COPY backend ./backend
COPY data ./data

WORKDIR /app/backend

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["python", "app.py"]