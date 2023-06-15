#!/bin/bash

# Run caves.app django management commands via cron
# It is recommended to run this script once per minute
# in production. It will delete users that have not verified
# their email address in 24 hours, as well as delete trip
# photos which were not successfully uploaded to S3.


APP_ROOT=/home/andrew/apps/caves.app
DOCKER_CMD="docker compose -f docker-compose.prod.yml exec web"


cd $APP_ROOT || exit
$DOCKER_CMD python manage.py prune_inactive_users
$DOCKER_CMD python manage.py delete_invalid_photos
