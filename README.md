# Caving Log
A Django web application to log caving trips

### Test details
Use Docker.

 - Copy `/app/cavinglog/settings.py.dev.example` to `/app/cavinglog/settings.py`
 - `docker compose up`
 - `docker compose run web python manage.py migrate`
 - `docker compose run web python manage.py createsuperuser`
