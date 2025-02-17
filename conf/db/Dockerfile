FROM postgres:17-bullseye

# postgis/postgis docker images do not provide an arm64 build which leads
# to very poor performance on Apple Silicon. This is a workaround to
# use the official postgres arm64 build and then install postgis
# on top. The below is copied from the postgis/postgis Dockerfile with a
# custom initdb script to load the blank database with an admin user only.

ENV POSTGIS_MAJOR 3
ENV POSTGIS_VERSION 3.5.2+dfsg-1.pgdg110+1

RUN apt-get update \
      && apt-cache showpkg postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR \
      && apt-get install -y --no-install-recommends \
           # ca-certificates: for accessing remote raster files;
           #   fix: https://github.com/postgis/docker-postgis/issues/307
           ca-certificates \
           \
           postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR=$POSTGIS_VERSION \
           postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR-scripts \
      && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /docker-entrypoint-initdb.d
COPY ./conf/db/initdb-postgis.sh /docker-entrypoint-initdb.d/10_postgis.sh
COPY ./conf/db/update-postgis.sh /usr/local/bin
