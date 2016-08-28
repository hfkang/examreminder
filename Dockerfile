FROM python:3-alpine
COPY ./ /
RUN pip install -r /requirements.txt
CMD ["/usr/local/bin/gunicorn", "--conf", "gunicorn.conf", "wsgi_app:application"]
