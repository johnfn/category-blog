# category blog

A way to sort ideas into categories and dump them onto the web.

1. Install postgresql.

2. `createdb db && psql --dbname=db --file=schema.sql`. This will create the tables.

3. Setup: `python -c 'from main import init_db; init_db()'`

4. SQL: Most of it is pretty sloppy. I may rewrite it in the future.
