FROM python:3.13.5-slim

RUN apt-get update

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

CMD ["python", "main.py"]