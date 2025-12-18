FROM ubuntu:latest
LABEL authors="andrew"

ENTRYPOINT ["top", "-b"]
