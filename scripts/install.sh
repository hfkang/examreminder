#!/bin/sh

apk update
apk add curl

curl "https://caddyserver.com/download/build?os=linux&arch=amd64&features=cloudflare" -o "caddy.tar.gz"
tar xzvf caddy.tar.gz -C /usr/local/bin/ caddy
chmod +x /usr/local/bin/caddy

pip install -r /app/requirements.txt

mkdir -p /app/logs

echo "Init roomplz"
python osm.py --all
echo "Downloaded osm data"
echo "init db"
cd /app
python db_classes.py --startup
