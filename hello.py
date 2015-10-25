# first, install python
# then, install flask using pip install Flask
# install watchdog with pip install watchdog [failed on win10]
# create this file, run python thisfile.py, starts a server on :1337
# fetch bootstrap http://getbootstrap.com/getting-started/#download
#
import sqlite3, os
from flask import g
from flask import Flask, request, render_template
from datetime import datetime
#from flask import render_template
# For logging
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

# config section (move to config file later)
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'db\sqlite.db'),
    DEBUG=True,
    SECRET_KEY='totallysecretkeyImgoingtouploadtogithub',
    USERNAME='admin',
    PASSWORD='default'
))

app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


def init_db():
    # doc imports closing from contextlib and iterates over
    # closing(connect_db() as db) instead...
    with app.app_context():
        db = get_db()
        with app.open_resource('db\schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_db()
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def insert_db(query, args=(), one=False):
    db = get_db()
    app.logger.info('insert_db: Inserted %s', args)
    res = g._database.execute(query, args)
    g._database.commit()
    return True

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/')
def showDefault():
    return render_template('base.html')

@app.route('/refreshdb')
def refreshDB():
    init_db()
    return 'Init complete'

@app.route('/user/')
@app.route('/user/<string:username>')
def show_greeting(username):
    # renders template hello.html and passes username from URI til name variable in template
    return render_template('base.html', name=username)
    #return 'User %s' % username

@app.route('/system/register/<system>/<percentage>')
@app.route('/system/register/<system>/<percentage>/<meta>')
def register_health(system, percentage, meta = None):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    args = [now,system,percentage]
    res = insert_db("insert into healthstatus ('when', 'system', 'status') values (?, ?, ?)", args)
    return render_template('base.html', performed='register_health()', data = args)

@app.route('/system/view/<system>/')
def display_system(system):
    app.logger.info('display_system: %s', system)
    systemHealthPoints = getSystemHealth(system)
    return render_template('systemViewSingle.html', healthData=systemHealthPoints)

def getSystemHealth(system):
    system = [system]
    app.logger.info('getSystemHealth: %s', system)
    systemHealthPoints = query_db('select "when","status","who","meta" from healthstatus where "system"=?', system)
    app.logger.info('getSystemHealth: %s', str(systemHealthPoints))
    return systemHealthPoints

@app.route('/system/list')
def list_systems():
    systems = query_db('select distinct system,count(*) from healthstatus group by system')
    return render_template('systemlist.html', systems = systems)
        #print ("system['system']")

if __name__ == '__main__':
    # internal only (turn off debug mode before running anything else)
    #app.run()
    #app.debug = True # enable debug mode to make server reload on code changes.
    handler = RotatingFileHandler('foo.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.run(host='0.0.0.0',port=1337,debug = True)
