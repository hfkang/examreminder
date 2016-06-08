# examreminder<sup>Alpha</sup>
Dashboard and reminder service for U of T exams 

### Deployment

Clone the repo and execute

    docker build -t exrem .

and to start the server,

    docker run -it --rm -p 5000:80 --name examreminder exrem

If you want local shell,

    docker exec -ti examreminder /bin/bash --login

Note that this application is configured to use the /remind/payload endpoint with github's webhooks for automatic
deployment. As a result, the apache user 'whiskey' has full ownership of the /app directory

New feature: a completely independent application /admin will be used to
administer the reminder service. It is as loosely coupled to the backend
as possible, so in the event of database issues you can revert to a clean
state over the web.
