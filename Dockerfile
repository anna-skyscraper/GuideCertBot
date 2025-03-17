FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app
COPY bot.py /app
COPY questions.xlsx /app

RUN pip install --progress-bar off -r requirements.txt

