FROM ghcr.io/astral-sh/uv:0.6.10-python3.12-alpine

RUN apk add git

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync

COPY templates templates
COPY *.py ./

ENV BASE_FOLDER=/base_folder

CMD [ "uv", "run", "gunicorn", "app:app", "-b", ":8000" ]
