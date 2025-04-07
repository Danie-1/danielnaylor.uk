export $(cat .env | xargs)
uv run gunicorn app:app -b :$PORT -w 3
