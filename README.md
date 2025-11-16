# Quiz Taxons

This app is a quizz to help learning taxons required by [the naturalist training for the CNBs (Belgium)](https://cercles-naturalistes.be/formations/formations-guide-nature).

## Development

Create a `.env` file with your secrets
```
ALLOWED_HOSTS=localhost
SECRET_KEY=django-insecure-*pwa$88^gu02ys&u^!n&@ncfzj^l5v)av@j1j&53&e75^9w=1k
GOOGLE_SEARCH_ENGINE=my_engine_id
GOOGLE_SEARCH_API_KEY=my_search_api_hey
```

Initiate Django
```bash
docker compose build
docker compose up -d
docker compose exec -T quiz uv run python manage.py migrate
docker compose exec -T quiz uv run python manage.py import_taxons
docker compose exec -T quiz uv run python manage.py createsuperadmin
```

Visit http://localhost:8000 to play

Visit http://localhost:8000/admin to read the content of the database

## Production

Create a `prod.env` file with your secrets
```
ALLOWED_HOSTS=my.domain
CSRF_TRUSTED_ORIGINS=https://my.domain
SECRET_KEY=django-insecure-*pwa$88^gu02ys&u^!n&@ncfzj^l5v)av@j1j&53&e75^9w=1k
GOOGLE_SEARCH_ENGINE=my_engine_id
GOOGLE_SEARCH_API_KEY=my_search_api_hey
NGROK_AUTHTOKEN=my_ngrok_token
```

Update your Ngrok endpoint in [docker-compose.prod.yaml](docker-compose.prod.yaml)

Initiate Django
```bash
docker compose -f docker-compose.prod.yaml build
docker compose -f docker-compose.prod.yaml up -d
docker compose -f docker-compose.prod.yaml exec -T quiz uv run python manage.py migrate
docker compose -f docker-compose.prod.yaml exec -T quiz uv run python manage.py import_taxons
docker compose -f docker-compose.prod.yaml exec -T quiz uv run python manage.py createsuperadmin
```
