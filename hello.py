# first, install python
# then, install flask using pip install Flask
# install watchdog with pip install watchdog [failed on win10] (why?)
# create this file, run python thisfile.py, starts a server on :1337
# http://www.wtfpl.net/about/
import sqlite3, os
from flask import g
from flask import Flask, request, render_template, abort, redirect, url_for
from datetime import datetime
from random import randint
#from flask import render_template
# For logging
import logging

app = Flask(__name__)

# config section (move to config file later)
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'db\sqlite.db'),
    DEBUG=True,
    SECRET_KEY='totallysecretkeyImgoingtouploadtogithub',
    USERNAME='admin',
    PASSWORD='default'
))

logging.basicConfig(filename='example.log', filemode='w', level=logging.INFO)
#handler.setLevel(logging.INFO)
#app.logger.addHandler(handler)

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
    return render_template('base.html', performed='init_db()')

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
    if percentage == 'random':
        percentage = randint(0,100)
    args = [now,system,percentage]
    res = insert_db("insert into healthstatus ('when', 'system', 'status') values (?, ?, ?)", args)
    #return render_template('base.html', performed='register_health()', data = args)
    return redirect('/system/list')

@app.route('/system/view/<system>/')
@app.route('/system/view/<system>/<modifier>')
def display_system(system, modifier = False):
    app.logger.info('display_system: %s', system)
    systemHealthPoints = getSystemHealth(system, modifier)
    return render_template('systemViewSingle.html', healthData=systemHealthPoints, system=system)

def getSystemHealth(system,modifier = None):
    system = [system]
    #logging.info('getSystemHealth: %s %s', system, modifier)
    #sql = 'SELECT "when","status","who","meta" FROM healthstatus WHERE "system"=?'
    # Standard display is today
    sql = 'SELECT "when","status","who","meta" FROM healthstatus WHERE "system"=? AND "when" BETWEEN datetime(\'now\', \'start of day\') AND datetime(\'now\', \'localtime\')'
    if modifier == 'all':
        sql = 'SELECT "when","status","who","meta" FROM healthstatus WHERE "system"=?'
    elif modifier == 'week':
        sql = 'SELECT "when","status","who","meta" FROM healthstatus WHERE "system"=? AND "when" BETWEEN datetime(\'now\', \'-6 days\') AND datetime(\'now\', \'localtime\')'
    elif modifier == 'month':
        sql = 'SELECT "when","status","who","meta" FROM healthstatus WHERE "system"=? AND "when" BETWEEN datetime(\'now\', \'start of month\') AND datetime(\'now\', \'localtime\')'
    systemHealthPoints = query_db(sql, system)
    logging.info('getSystemHealth: %s', str(systemHealthPoints))
    return systemHealthPoints

def getSystemHealthTodayOnly(system):
        #system = [system
        app.logger.info('getSystemHealthTodayOnly: %s %s', system)
        args = [system]
        systemHealthPoints = query_db('SELECT "when","status","who","meta" FROM healthstatus WHERE "system"=? AND "when" BETWEEN datetime(\'now\', \'start of day\') AND datetime(\'now\', \'localtime\')', args)
        app.logger.info('getSystemHealth: %s', str(systemHealthPoints))
        return systemHealthPoints

@app.route('/system/list')
def list_systems():
    systems = query_db('select distinct system,count(*) from healthstatus group by system')
    #systemAdded[0] = None
    i = 0
    logging.info('list_systems_result: %s', str(systems[0][0]))
    for system in systems:
        latestSystemData = (getSystemHealth(str(system[0])))
        newSystem = (system[0],system[1],latestSystemData)
        systems[i] = newSystem
        i = i + 1
        #systemLatest = list(getSystemHealth(system[0]))
        #systems[3] = systemLatest
        #i = i + 1
        #systemAddedInfo =
    #    thisSystemHealth = getSystemHealth(systems)
    #    systems[i][3] = 'moo'
    #    app.logger.info('list_systems_loop: %s', str(systems[i]))
    #    #systems[i].append("moooo")
    #    i += 1
    logging.info('list_systems_result2: %s', str(systems))


    return render_template('systemList.html', systems = systems)
        #print ("system['system']")

if __name__ == '__main__':
    # internal only (turn off debug mode before running anything else)
    #app.run()
    #app.debug = True # enable debug mode to make server reload on code changes.
    app.run(host='0.0.0.0',port=1337,debug = True)
