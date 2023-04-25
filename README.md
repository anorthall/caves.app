# caves.app
[![Run Django Tests](https://github.com/anorthall/caves.app/actions/workflows/run-tests.yaml/badge.svg)](https://github.com/anorthall/caves.app/actions/workflows/run-tests.yaml)

A Django web application to log caving trips. Running online at [caves.app](https://caves.app/).

## Running the application
Use Docker.

 - Copy `etc/dev/dev.env.example` to `etc/dev/dev.env`
 - Run `docker compose up`
 - Go to http://127.0.0.1:8000/
 - Login with the user `admin@caving.log` and the password `admin`.
 - Have a look around! The development database is filled with my personal caving trips.
 
 You can also visit [caves.app](https://caves.app/) and try out the hosted version (which is identical
 to this one).
