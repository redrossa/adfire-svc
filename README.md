# Adfire Server

Currently providing mock API routes for [adfire-web](https://github.com/redrossa/adfire-web).

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

3. Create database `adfire` in your Postgres server 

2. Set database URL in `alembic.ini`

   ```toml
   sqlalchemy.url = # postgresql://<username>:<password>@localhost:5432/adfire
   ```

3. Run migrations

   - To run initial migration

     ```shell
     alembic revision --autogenerate -m "Initial migration"
     ```
   
   - For subsequent migrations, or with `--autogenerate` to autogenerate migration code

     ```shell
     alembic revision -m "<MESSAGE>"
     ```

4. Apply changes to Postgres

   ```shell
   alembic upgrade head
   ```