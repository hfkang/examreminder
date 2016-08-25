FROM python:3-alpine
RUN  pip3 install gunicorn json-logging-py && mkdir /app
COPY ./* /app
EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/gunicorn", "--config", "/app/gunicorn.conf", "--log-config", "/logging.conf", "-b", ":8000", "myapp:app"]
