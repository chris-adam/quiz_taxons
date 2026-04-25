# Quiz Taxons

This app is a quizz to help learning taxons required by [the naturalist training for the CNBs (Belgium)](https://cercles-naturalistes.be/formations/formations-guide-nature) and by [the Club Alpin Belge (MS Rando Initiateur)](https://www.clubalpin.be/blog/news-1/post/moniteur-randonnee-153).

## Development

Create a `.env` file with your secrets
```
ALLOWED_HOSTS=127.0.0.1
SECRET_KEY=django-insecure-*pwa$88^gu02ys&u^!n&@ncfzj^l5v)av@j1j&53&e75^9w=1k
DEBUG=1
XENOCANTO_API_KEY=xxx  # https://xeno-canto.org/explore/api
```

Initiate Django
```bash
docker compose build
docker compose up -d
docker compose exec -T quiz uv run python manage.py migrate
docker compose exec -T quiz uv run python manage.py import_taxons
docker compose exec -T quiz uv run python manage.py createsuperadmin
```

Visit http://127.0.0.1:8000 to play

Visit http://127.0.0.1:8000/admin to read the content of the database

### Tests

Run tests
```bash
docker compose run --rm -T quiz uv run python manage.py test
```

## Production

Create a `prod.env` file with your secrets
```
ALLOWED_HOSTS=my.domain
CSRF_TRUSTED_ORIGINS=https://my.domain
SECRET_KEY=django-insecure-*pwa$88^gu02ys&u^!n&@ncfzj^l5v)av@j1j&53&e75^9w=1k
XENOCANTO_API_KEY=xxx
NGROK_AUTHTOKEN=xxx
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
