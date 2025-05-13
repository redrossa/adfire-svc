# Adfire Server

Currently providing mock API routes for [adfire-web](https://github.com/redrossa/adfire-web).

## Getting started

Run development server with:

```bash
fastapi dev app/main.py
```

Migrate DB models with:

```bash
# commit changes
alembic revision --autogenerate -m "<MESSAGE>"

# push migration
alembic upgrade head
```