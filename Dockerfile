FROM grahamdumpleton/mod-wsgi-docker:python-3.5-onbuild
ENV PYTHON_PATH /usr/local/python/bin/python
# whiskey user needs full write access in the app directory to perform git updates
RUN chown -R whiskey /app
#RUN chown -R whiskey /app/.git
#RUN chmod -R g+w /app/.git
RUN cd /app; git remote set-url origin https://github.com/hfkang/examreminder.git
RUN cd /app; git config user.email "whiskey@examreminder.not"
RUN cd /app; git config user.name "whiskey user"
CMD [ "exrem.wsgi" ]
