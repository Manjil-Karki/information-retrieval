FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .


RUN echo "0 2 * * 0 cd /app && python -m src.crawler.run_crawl >> /var/log/crawler.log 2>&1" \
    > /etc/cron.d/crawler-cron

RUN chmod 0644 /etc/cron.d/crawler-cron \
    && crontab /etc/cron.d/crawler-cron

RUN touch /var/log/crawler.log

EXPOSE 8000 8501


CMD cron && \
    uvicorn server:app --host 0.0.0.0 --port 8000 & \
    streamlit run app.py --server.address=0.0.0.0 --server.port=8501
