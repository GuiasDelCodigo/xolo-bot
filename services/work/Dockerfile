FROM python:3.14-slim

WORKDIR /app

COPY work/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY work /app/services/work

EXPOSE 8000

CMD ["python", "-m", "services.work.main"]
