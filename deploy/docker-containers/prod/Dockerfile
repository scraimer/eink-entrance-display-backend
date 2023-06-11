FROM eink-entrance-display-backend-base:latest

COPY . /app

ENTRYPOINT bash -c "cd /app ; /usr/local/bin/uvicorn eink_backend.main:app --host 0.0.0.0 --port 8321"
EXPOSE 8321
