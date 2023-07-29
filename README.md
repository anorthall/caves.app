# caves.app

[![Run Django Tests](https://github.com/anorthall/caves.app/actions/workflows/run-tests.yaml/badge.svg)](https://github.com/anorthall/caves.app/actions/workflows/run-tests.yaml) [![codecov](https://codecov.io/gh/anorthall/caves.app/branch/main/graph/badge.svg?token=HDZHAETW75)](https://codecov.io/gh/anorthall/caves.app)

A Django web application to log caving trips. Running online at [caves.app](https://caves.app/).

### Features

- Complete trip logbook functionality, with as many or as few data points as you like.
- Easily upload photos from inside the cave and share them.
- Add a rich text trip report (like a blog post) to truly capture the experience.
- View social news feed of your friends' recent caving activity.
- Comment on your friends' trips, or 'like' them.
- Comprehensive granular statistics and pretty charts.
- View a map of all the caves you've visited.
- Automatically import and export data from CSV files.
- Search through trips by location, cave, or any other data point.
- Create a public profile to share your trips with the world (or just your friends, if you prefer).
- A minimalist and mobile friendly user interface.

### Planned

- An equipment tracking system - keep track of how many batteries you've got left, or how old your rope is!

## Contributing

The project is written in Python and Django. Pull requests are more than welcome. Check the
[GitHub issues](https://github.com/anorthall/caves.app/issues) for some ideas of what to do.

### Development environment

All development is done inside the Docker development environment. To set up the environment, copy the example
`development.env` file and build and run the docker image from the project root directory:

```
$ cp config/docker/development.env.example config/docker/development.env
$ docker-compose up
```

Once the database has initialised, the server will be accessible at http://127.0.0.1:8000. An initial superuser account with the email address `admin@caves.app` and the password `admin` is created automatically.

Additional test data can be generated using the `make_test_data` Django management
command. You can run the command via docker compose like so:

```
$ docker-compose exec web ./manage.py make_test_data
```

By default, this will create 25 users and 6,000 trips, although this is configurable
(see `manage.py make_test_data --help` for more information). Generation of users
and trips may take a few minutes on slower systems. Please note that the
`make_test_data` command can only create users once, as it will attempt to re-use
the same sequential emails on the second attempt. If you wish to re-create users,
you can stop the Docker instance and delete the `data/development` directory, before
re-initialising the environment:

```
$ docker compose down -v
$ rm -r data/development/
$ docker compose up
```

#### Trip photo uploads

In order to use the photo upload feature of trips (powered by [uppy](https://uppy.io/)),
you will need to set up details for AWS S3 in the
`config/docker/development.env` file. It is possible to reconfigure Uppy
and Django to use a different storage backend, but this is beyond the scope of
this README and would require significant code changes. For more information, check
out the [django-storages](https://django-storages.readthedocs.io/) and
[uppy](https://uppy.io/docs/) documentation.

### Hints

- Any emails generated whilst using the development environment will be printed directly to the console.
- Python requirements are listed in `config/requirements/development.txt` and can be installed locally (for linting, etc) with `pip install -r config/requirements/development.txt`.
- Tests can be run via `docker-compose exec web ./manage.py test`.

## Feedback

Feedback of any kind is more than welcome. Please feel free to open an issue on GitHub, or contact me [directly via email](mailto:andrew@caver.dev) at `andrew@caver.dev`. You are also welcome to
[join the caves.app Discord server](https://discord.gg/jEvPbR4G4k) to discuss either using the
application or development.
