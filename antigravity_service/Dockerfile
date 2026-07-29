FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=5005

WORKDIR /app

COPY main.py .

EXPOSE 5005

CMD ["python", "-u", "main.py"]
