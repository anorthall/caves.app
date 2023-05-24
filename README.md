# caves.app
[![Run Django Tests](https://github.com/anorthall/caves.app/actions/workflows/run-tests.yaml/badge.svg)](https://github.com/anorthall/caves.app/actions/workflows/run-tests.yaml) [![codecov](https://codecov.io/gh/anorthall/caves.app/branch/main/graph/badge.svg?token=HDZHAETW75)](https://codecov.io/gh/anorthall/caves.app)

A Django web application to log caving trips. Running online at [caves.app](https://caves.app/).


### Features
- Complete trip logbook functionality, including rich text trip reports and detailed nerdy stats.
- Comprehensive granular statistics and graphs of activity.
- Interactive social features: commenting and 'liking' other's trips, and following other users.
- The ability to create a public profile, making your trip log available online (if desired).
- A minimalist and mobile friendly user interface.


### Planned
- Automatically generated maps of caves visited.
- The ability to upload photos and surveys to trips.
- An equipment tracking system - keep track of how many batteries you've got left, or how old your rope is!


## Contributing
The project is written in Python and Django. Pull requests are more than welcome. Check the [GitHub issues](https://github.com/anorthall/caves.app/issues) for some ideas of what to do.


### Development environment
All development is done inside the Docker development environment. To set up the environment, build and run the docker image from the project root directory:

```
docker-compose up
```

Once the database has initialised, the server will be accessible at http://127.0.0.1:8000. An initial superuser account with the email address `admin@caves.app` and the password `admin` is created automatically.

Additional test data can be generated using the `maketestdata` Django management command. You can run the command via docker compose like so:

```
docker-compose exec web-dev ./manage.py maketestdata
```

By default, this will create 25 users and 6,000 trips, although this is configurable (see `manage.py maketestdata --help` for more information). Generation of users and trips may take a few minutes on slower systems. Please note that the `maketestdata` command can only create users once, as it will attempt to re-use the same sequential emails on the second attempt. If you wish to re-create users, you can stop the Docker instance and delete the `data/development` directory, before re-initialising the environment:

```
docker compose down -v
rm -r data/development/
docker compose up
```

### Hints
- Any emails generated whilst using the development environment will be printed directly to the console.
- Python requirements are listed in `config/requirements/development.txt` and can be installed locally (for linting, etc) with `pip install -r config/requirements/development.txt`.
- Tests can be run via `docker-compose exec web-dev ./manage.py test`.


## Feedback
Feedback of any kind is more than welcome. Please feel free to open an issue on GitHub, or contact me [directly via email](mailto:andrew@caver.dev) at `andrew@caver.dev`. You are also welcome to
[join the caves.app Discord server](https://discord.gg/jEvPbR4G4k) to discuss either using the
application or development.
