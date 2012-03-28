from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, Response
from functools import wraps
import psycopg2
from contextlib import closing
import datetime

DATABASE = 'posts.db'
SECRET_KEY = open('secretkey').readlines()[0]
PASSWORD = open('password').readlines()[0][:-1]

app = Flask(__name__)
app.debug=True
app.secret_key = SECRET_KEY

def connect_db():
  return psycopg2.connect("dbname=db user=postgres")

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
    g.db.execute('insert into tags (value, description, longdesc) values (?, ?, ?)', [value, "", ""])
    g.db.commit()

    cur = g.db.execute('select id from tags where value = ?', [value])
    elems = cur.fetchall()

  return elems[0][0]

def new_entry(title, text, id, date, tags):
  if date is None: date = datetime.datetime.now().strftime("%m/%d/%Y %I:%M%p")

  if id is None:
    cur = g.db.cursor()

    cur.execute('insert into entries (title, text, created) values (?, ?, ?)',
        [title, text, date])

    # read id back
    id = cur.lastrowid
  else:
    #TODO: This actually makes the name of this function incorrect.
    g.db.execute('update entries set title = ?, text = ?, created = ? where id = ?',
        [title, text, date, id])

  if tags is not None:
    g.db.execute('delete from entry_tags where entryid = ?', [id])

    taglist = [tag.strip() for tag in tags.split(",")]

    for tag in taglist:
      g.db.execute('insert into entry_tags (entryid, tagid) values (?, ?)', [id, tag_id(tag)])

    g.db.commit()

def check_auth(username, password):
  return username == 'johnfn' and password == [l[:-1] for l in file('password')][0]

def authenticate():
  return Response('Are you trying to hack my website? :) email me at johnfn@gmail.com' , 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

@app.route("/admin")
def admin():
  if session.get('authed') is None: return authenticate()

  return render_template('admin.html')

@app.route("/login", methods=['POST'])
def login_post():
  if request.form['username'] == "johnfn" and request.form['password'] == PASSWORD:
    session['authed'] = True
    return redirect(url_for('index'))
  else:
    return authenticate()

@app.route("/logout")
def logout():
  session.pop('authed', None)
  return redirect(url_for('index'))

@app.route("/login", methods=['GET'])
def login():
  return render_template("login.html")

@app.route("/add", methods=['POST'])
def add_entry():
  if session.get('authed') is None: return authenticate()

  new_entry( request.form['title']
           , request.form['content']
           , request.form['id'] if request.form['id'].strip() != "" else None
           , request.form['date'] + " " + request.form['time'] if request.form['date'] else None
           , request.form['tags'] if request.form['tags'].strip() != "" else None)

  return redirect(url_for('index'))

@app.route('/<int:id>/edit')
def edit(id):
  if session.get('authed') is None: return authenticate()

  cur = g.db.execute('select title, text, created from entries where id = ?', [id])
  entry = cur.fetchall()[0]
  date, time = entry[2].split(" ")
  tags = ",".join(all_tags(id)['tags'])

  return render_template('admin.html', title = entry[0], content = entry[1], id = id, date = date, time = time, tags = tags)

def merge(o1, o2):
  return dict(o1.items() + o2.items())

def tag_value(tagid):
  return g.db.execute('select value from tags where id = ?', [tagid]).fetchall()[0][0]

def all_tags(id):
  tag_list = [tag_value(entry[0]) for entry in g.db.execute('select tagid from entry_tags where entryid = ?', [id])]

  return {'tags': tag_list}

@app.route('/<int:id>')
def post(id):
  cur = g.db.execute('select title, text, created, id from entries where id = ? order by created asc', [id])
  entries = [{'title': row[0], 'content': row[1], 'date': row[2], 'id': row[3]} for row in cur.fetchall()]

  return render_template('post.html', entry = entries[0], title = "", content = "")

def get_entry(id):
  e = g.db.execute('select title, text, created from entries where id = ?', [id]).fetchall()[0]
  return {'title': e[0], 'content': e[1], 'date': e[2], 'id': id}

@app.route('/tagged/<tag>/edit', methods=['POST'])
def edit_tag(tag):
  if session.get('authed') is None: return authenticate()

  if len(g.db.execute('select * from tags where value = ?', [tag]).fetchall()) > 0:
    id = tag_id(tag)
    g.db.execute('update tags set description = ?, longdesc = ? where id = ?', [request.form['desc'], request.form['longdesc'], id])
  else:
    g.db.execute('insert into tags (value, description, longdesc) values (?, ?, ?)', [tag, request.form['desc'], request.form['longdesc']])

  g.db.commit()
  return redirect(url_for('tagged', tag=tag))

@app.route('/tagged/<tag>')
def tagged(tag):
  entryids = g.db.execute('select entryid from entry_tags where tagid = ?', [tag_id(tag)]).fetchall()
  entries = [get_entry(e[0]) for e in entryids]
  description = ""
  longdesc = ""

  row = g.db.execute('select description, longdesc from tags where id = ?', [tag_id(tag)]).fetchall()
  if len(row) > 0:
    description = row[0][0]
    longdesc = row[0][1]

  return render_template('tagged.html', desc=description, longdesc=longdesc, entries=entries, tag=tag, auth=session.get('authed'))

def delete_post(id):
  g.db.execute('delete from entries where id = ?', [id])
  g.db.execute('delete from entry_tags where entryid = ?', [id])
  g.db.commit()

@app.route('/<int:id>/delete/definitely', methods=['POST'])
def definitely_delete(id):
  if session.get('authed') is None: return authenticate()

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
  if session.get('authed') is None: return authenticate()

  return render_template('delete.html', id=id)

@app.route("/")
def index():
  cur = g.db.execute('select title, text, created, id from entries order by id desc')
  entries = [{'title': row[0], 'content': row[1], 'date': row[2], 'id': row[3]} for row in cur.fetchall()]
  res = []
  tag_info = []
  every_tag = g.db.execute('select value, description, longdesc, id from tags').fetchall()
  for row in every_tag:
    count = len(g.db.execute('select * from entry_tags where tagid = ?', [row[3]]).fetchall())
    tag_info.append({'tag': row[0], 'desc': row[1], 'longdesc': row[2], 'count': count})

  entries = [merge(e, all_tags(e['id'])) for e in entries]

  return render_template('index.html', entries=entries, auth=session.get('authed'), tag_info=tag_info)

if __name__ == "__main__":
    app.run()
