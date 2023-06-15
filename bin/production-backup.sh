#!/bin/bash

# rsync backup script for *my particular* production instance of caves.app.
# This script may not work for other instances. It is stored in the
# repository for my convenience only, and may serve as an example to
# others.

# Configuration

APP_ROOT=/home/andrew/apps/caves.app
LOG_DIR=$APP_ROOT/data/production/logs/rsync
REMOTE=andrew@hartfield:/home/andrew/caves.app/backups


rsync -avzh --log-file=$LOG_DIR/rsync.log \
      --exclude CACHE \
      $APP_ROOT/data/production/backups \
      $APP_ROOT/data/production/logs \
      $APP_ROOT/data/production/media \
      $APP_ROOT/bin \
      $APP_ROOT/config \
      $REMOTE

rsync -avzh --log-file=$LOG_DIR/rsync-nginx.log \
      /etc/nginx/sites-available $REMOTE/nginx
