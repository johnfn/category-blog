from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, Response
from functools import wraps
from sqlite3 import dbapi2 as sqlite3
from contextlib import closing
import datetime

DATABASE = 'posts.db'
SECRET_KEY = open('secretkey').readlines()[0]
PASSWORD = open('password').readlines()[0][:-1]

app = Flask(__name__)
app.debug=True
app.secret_key = SECRET_KEY

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

def tag_id(value):
  cur = g.db.execute('select id from tags where value = ?', [value])
  elems = cur.fetchall()

  if len(elems) == 0:
    g.db.execute('insert into tags (value) values (?)', [value])
    g.db.commit()

    cur = g.db.execute('select id from tags where value = ?', [value])
    elems = cur.fetchall()

  return elems[0][0]

def new_entry(title, text, id, date, tags):
  if date is None: date = datetime.datetime.now().strftime("%m/%d/%Y %I:%M%p")

  if id is None:
    g.db.execute('insert into entries (title, text, created) values (?, ?, ?)',
        [title, text, date])
  else:
    #TODO: This actually makes the name of this function incorrect.
    g.db.execute('update entries set title = ?, text = ?, created = ? where id = ?',
        [title, text, date, id])

  g.db.commit()

  # read id back
  id = g.db.execute('select id from entries where title = ? and text = ?', [title, text]).fetchall()[0][0]

  if tags is not None:
    #TODO: Remove all old tagz.

    taglist = [tag.strip() for tag in tags.split(",")]

    for tag in taglist:
      g.db.execute('insert into entry_tags (entryid, tagid) values (?, ?)', [id, tag_id(tag)])

def check_auth(username, password):
  return username == 'johnfn' and password == [l[:-1] for l in file('password')][0]

def authenticate():
  return Response('Are you trying to hack my website? :) email me at johnfn@gmail.com' , 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

@app.route("/admin")
def admin():
  if session.get('authed') is None: authenticate()

  return render_template('admin.html')

@app.route("/login", methods=['POST'])
def login_post():
  if request.form['username'] == "johnfn" and request.form['password'] == "password":
    session['authed'] = True
    return redirect(url_for('index'))

@app.route("/logout")
def logout():
  session.pop('authed', None)
  return redirect(url_for('index'))

@app.route("/login", methods=['GET'])
def login():
  return render_template("login.html")

@app.route("/add", methods=['POST'])
def add_entry():
  if session.get('authed') is None: authenticate()

  new_entry( request.form['title']
           , request.form['content']
           , request.form['id'] if request.form['id'].strip() != "" else None
           , request.form['date'] + " " + request.form['time'] if request.form['date'] else None
           , request.form['tags'] if request.form['tags'].strip() != "" else None)

  return redirect(url_for('index'))

@app.route('/<int:id>/edit')
def edit(id):
  if session.get('authed') is None: authenticate()

  cur = g.db.execute('select title, text, created from entries where id = %d' % id)
  entry = cur.fetchall()[0]
  date, time = entry[2].split(" ")

  return render_template('admin.html', title = entry[0], content = entry[1], id = id, date = date, time = time)

def merge(o1, o2):
  return dict(o1.items() + o2.items())

def tag_value(tagid):
  return g.db.execute('select value from tags where id = ?', [tagid]).fetchall()[0][0]

def all_tags(e):
  tag_list = [tag_value(entry[0]) for entry in g.db.execute('select tagid from entry_tags where entryid = ?', [e['id']])]

  return {'tags': tag_list}

@app.route('/<int:id>')
def post(id):
  cur = g.db.execute('select title, text, created, id from entries where id = %d order by created asc' % id)
  entries = [{'title': row[0], 'content': row[1], 'date': row[2], 'id': row[3]} for row in cur.fetchall()]

  return render_template('post.html', entry = entries[0], title = "", content = "")

def get_entry(id):
  e = g.db.execute('select title, text, created from entries where id = ?', [id]).fetchall()[0]
  return {'title': e[0], 'content': e[1], 'date': e[2], 'id': id}

@app.route('/tagged/<tag>')
def tagged(tag):
  entryids = g.db.execute('select entryid from entry_tags where tagid = ?', [tag_id(tag)]).fetchall()
  entries = [get_entry(e[0]) for e in entryids]

  return render_template('tagged.html', entries=entries, tag=tag)

def delete_post(id):
  g.db.execute('delete from entries where id = ?', [id])
  g.db.execute('delete from entry_tags where entryid = ?', [id])
  g.db.commit()

@app.route('/<int:id>/delete/definitely', methods=['POST'])
def definitely_delete(id):
  if session.get('authed') is None: authenticate()

  delete_post(id)

  return redirect(url_for('index'))

@app.route('/dump')
def dump():
  result = ""

  for line in g.db.iterdump():
    result += line + '<br>'

  return render_template('dump.html', dump=result)

@app.route('/<int:id>/delete')
def delete(id):
  if session.get('authed') is None: authenticate()

  return render_template('delete.html', id=id)

@app.route("/")
def index():
  cur = g.db.execute('select title, text, created, id from entries order by id desc')
  entries = [{'title': row[0], 'content': row[1], 'date': row[2], 'id': row[3]} for row in cur.fetchall()]

  entries = [merge(e, all_tags(e)) for e in entries]

  return render_template('index.html', entries=entries, auth=session.get('authed'))

if __name__ == "__main__":
    app.run()
