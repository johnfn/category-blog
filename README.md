# category blog

A way to sort ideas into categories and dump them onto the web.

## fun stuff

Setting up Flask, psycopg and Heroku in combination is notoriously undocumented. If you're interested in exactly how to get something like this set up, you should take a peek at the `connect_db()` function in `main.py` where most of the tricky stuff takes place. The rest of the trouble really just boils down to dependency bashing.

## how to run it yourself

1. Install postgresql.

2. Run `python -c 'from main import init_db; init_db()'`

## notes

Some of my SQL is pretty sloppy. I may rewrite it in the future.
