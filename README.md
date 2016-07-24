# examreminder<sup>Alpha</sup>
Dashboard and reminder service for U of T exams 

### Data Sources

ArtSci calendar: http://www.artsci.utoronto.ca/current/exams/june16 
Engineering: http://www.apsc.utoronto.ca/timetable/fes.aspx
Engineering Summer: http://www.undergrad.engineering.utoronto.ca/Assets/UndergradEng+Digital+Assets/2016+Summer+F+Session+Engineering+Exam+Schedule+2.pdf

### Deployment

Clone the repo and execute

    docker build -t exrem .

and to start the server,

    docker run -it --rm -p 80:80 --name examreminder exrem

If you want local shell,

    docker exec -ti examreminder /bin/bash --login

Note that this application is configured to use the /remind/payload endpoint with github's webhooks for automatic
deployment. As a result, the apache user 'whiskey' has full ownership of the /app directory

New feature: a completely independent application /admin will be used to
administer the reminder service. It is as loosely coupled to the backend
as possible, so in the event of database issues you can revert to a clean
state over the web.

Some useful info: 
Server URL         : http://localhost/
Server Root        : /tmp/mod_wsgi-localhost:80:0
Server Conf        : /tmp/mod_wsgi-localhost:80:0/httpd.conf
Error Log File     : /dev/stderr (warn)
Startup Log File   : /dev/stderr
