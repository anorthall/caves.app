default:
  just --list

ruff:
  uv run ruff format
  uv run ruff check --fix

mypy +ARGS="":
  uv run dmypy run -- {{ ARGS }}

lint:
  just ruff
  just mypy

docker-run-sh +ARGS:
  docker compose exec django /app/conf/run.sh {{ ARGS }}

test +ARGS="--parallel":
  just docker-run-sh test {{ ARGS }}

manage +ARGS="":
  just docker-run-sh manage {{ ARGS }}
