# Adfire Server

Backend for [adfire-web](https://github.com/redrossa/adfire-web).

## Getting started

1. Install dependencies

   ```shell
   pip install -r requirements.txt
   
   pip install "fastapi[standard]"
   ```

2. Populate environment variables

   ```shell
   cp .env.example .env.local
   ```

3. Run development server

   ```bash
   fastapi dev app/main.py
   ```

## Migrate Database

1. Install Alembic

   ```shell
   pip install alembic
   ```

2. Create database `adfire` in your Postgres server

3. Inside `adfire`, create schemas `authjs` and `core`

4. Set database URL in `alembic.ini`

   ```toml
   sqlalchemy.url = # postgresql://<username>:<password>@localhost:5432/adfire
   ```

5. Run migrations

   - To run initial migration

     ```shell
     alembic revision --autogenerate -m "Initial migration"
     ```
   
   - For subsequent migrations, or with `--autogenerate` to autogenerate migration code

     ```shell
     alembic revision -m "<MESSAGE>"
     ```

6. Apply changes to Postgres

   ```shell
   alembic upgrade head
   ```

## Run Tests

1. Install `httpx`

   ```shell
   pip install httpx
   ```

2. Populate environment variables

   ```shell
   cp .env.example .env.test
   ```

3. Run pytest

   ```shell
   pytest
   ```