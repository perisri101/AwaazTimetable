FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# We don't need to copy app/ here since it's mounted as a volume in docker-compose.yml
# COPY app/ .

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0"] 