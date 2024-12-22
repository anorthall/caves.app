default:
  just --list

lint:
  uv run ruff format
  uv run ruff check --fix
  BASE_DIR="app/" IMGPROXY_KEY="-" IMGPROXY_SALT="-" SECRET_KEY="-" REDIS_URL="-" mypy .
