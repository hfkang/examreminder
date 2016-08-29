FROM python:3-alpine
COPY . /app
EXPOSE 5000
RUN /app/scripts/install.sh
ENTRYPOINT ["/app/scripts/runme.sh"]