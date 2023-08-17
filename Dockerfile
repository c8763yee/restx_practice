FROM python:3.10-alpine
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8763
CMD ["gunicorn", "-b", "0.0.0.0:8763", "app:app", "--preload"]
