#!/bin/sh
echo "Startup"
cd /app
nohup gunicorn --conf /app/gunicorn.conf wsgi_app:application > logs/gunicorn.log 2>&1 &
echo "Started gunicorn"
caddy

