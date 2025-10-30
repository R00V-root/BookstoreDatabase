# Bookstore Database

This repository delivers a Dockerised Django + PostgreSQL implementation of the Bookstore e-commerce database described in the coursework plan.

## Project Layout

```
bookstore/         # Django project and app
store/             # Application models, views, templates
Dockerfile
docker-compose.yml
requirements.txt
/db                # SQL schema and init scripts
/seed              # Synthetic data generation
/tests             # Pytest test suite
/docs              # Documentation set
/perf              # Performance artefacts
/demo              # Demo runbook
```

## Prerequisites
- Docker Engine 20+
- docker-compose plugin

## Quickstart

```bash
git clone <repo>
cd BookstoreDatabase
docker-compose up --build
```

The web interface will be available at `http://localhost:8000/store/login/`.
Load demo credentials once the stack is running:

```bash
docker-compose run --rm web python bookstore/manage.py loaddata \
    store/fixtures/groups.json store/fixtures/users.json
docker-compose run --rm web python bookstore/manage.py bootstrap_roles
```

Sign in using `admin` / `admin123` or `employee` / `admin123`.

## Environment Variables

- `POSTGRES_DB` (default: `bookstore`)
- `POSTGRES_USER` (default: `bookstore`)
- `POSTGRES_PASSWORD` (default: `bookstore`)
- `DJANGO_SECRET_KEY` (default: `insecure-docker-secret`)
- `DJANGO_DEBUG` (default: `true`)

## Database Management

Initial extensions (`pg_trgm`, `pgcrypto`) are created via `db/init/01_extensions.sql`.
To apply manual schema changes outside of Django ORM, run:

```bash
docker-compose exec -T db psql -U $POSTGRES_USER -d $POSTGRES_DB < db/schema.sql
```

## Synthetic Data

Generate datasets with deterministic seeds:

```bash
docker-compose run --rm web python seed/generate_data.py dev
```

Outputs are written under `seed/output/<tier>`.

## Testing

```bash
docker-compose run --rm web pytest
```

## Backup & Restore

Use the provided scripts (see `db/backup.sh` and `db/restore.sh`) to snapshot and restore the database.

## Demo Flow

A sample walkthrough is documented in `demo/script.md`.
