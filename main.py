from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from sqlite3 import dbapi2 as sqlite3
from contextlib import closing
import datetime

app = Flask(__name__)
app.debug=True

DATABASE = 'posts.db'

def connect_db():
  return sqlite3.connect(DATABASE)

@app.before_request
def before_request():
  g.db = connect_db()
  g.user = None

@app.teardown_request
def teardown_request(ex):
  if hasattr(g, 'db'):
    g.db.close()

def init_db():
    """Creates the database tables."""
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()

def new_entry(title, text, id):
  if id is None:
    g.db.execute('insert into entries (title, text, created) values (?, ?, ?)',
        [title, text, datetime.datetime.now()])
  else:
    g.db.execute('update entries set title = ?, text = ?, created = ? where id = ?',
        [title, text, datetime.datetime.now(), id])

  g.db.commit()


@app.route("/admin")
def admin():
  return render_template('admin.html')

@app.route("/add", methods=['POST'])
def add_entry():
  new_entry(request.form['title'], request.form['content'], request.form['id'])

  return redirect(url_for('index'))

@app.route('/<int:id>/edit')
def edit(id):
  cur = g.db.execute('select title, text from entries where id = %d' % id)
  entry = cur.fetchall()[0]

  return render_template('admin.html', title = entry[0], content = entry[1], id = id)

@app.route('/<int:id>')
def post(id):
  cur = g.db.execute('select title, text, created, id from entries where id = %d order by id desc' % id)
  entries = [{title: row[0], content: row[1], date: row[2], id: row[3]} for row in cur.fetchall()]

  return render_template('post.html', entry = entries[0], title = "", content = "")

@app.route("/")
def index():
  cur = g.db.execute('select title, text, created, id from entries order by id desc')
  entries = [dict(title=row[0], content=row[1], date=row[2], id=row[3]) for row in cur.fetchall()]

  return render_template('index.html', entries=entries)

if __name__ == "__main__":
    app.run()
