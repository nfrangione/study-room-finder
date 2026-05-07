FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY seed_and_simulate.py .

ENV AWS_DEFAULT_REGION=us-west-1
ENV DYNAMODB_TABLE=SSURooms
ENV UPDATE_INTERVAL_SECONDS=60
ENV SIMULATE=false

CMD ["python", "seed_and_simulate.py"]