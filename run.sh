# export $(cat .env | xargs)
# uv run gunicorn app:app -b :$PORT -w 3
export BASE_FOLDER=/home/daniel/Documents/latex/notes/
export PORT=8000
docker compose build
docker compose up
