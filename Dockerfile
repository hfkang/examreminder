FROM grahamdumpleton/mod-wsgi-docker:python-3.5-onbuild
ENV PYTHON_PATH /usr/local/python/bin/python
# whiskey user needs full write access in the app directory to perform git updates
RUN chown -R whiskey /app && \
    cd /app; git remote set-url origin https://github.com/hfkang/examreminder.git && \
    cd /app; git config user.email "whiskey@examreminder.not" && \
    cd /app; git config user.name "whiskey user" && \
    apt-get update; apt-get install cron && \
    crontab -l | { cat; echo "0 2 * * 1 /app/roomplz/update.sh"; } | crontab -
CMD [ "exrem.wsgi" ]
