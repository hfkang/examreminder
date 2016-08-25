FROM python:3-alpine
RUN  pip3 install gunicorn json-logging-py && mkdir /app
COPY ./* /app
EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/gunicorn", "--conf", "/app/gunicorn.conf", "-b", ":8000", "wsgi_app:application"]
