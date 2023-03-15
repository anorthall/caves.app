# Caving Log
A Django web application to log caving trips

### Test details
Use Docker.

 - Copy `app/cavinglog/settings.py.dev.example` to `app/cavinglog/settings.py`
 - Run `docker compose up`
 - Run `docker compose run web python manage.py migrate`
 - Run `docker compose run web python manage.py createsuperuser`
