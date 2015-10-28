# first, install python
# then, install flask using pip install Flask
# install watchdog with pip install watchdog [failed on win10] (why?)
# pip install flask-debugtoolbar
# pip install flask-sqlalchemy
# create this file, run python thisfile.py, starts a server on :1337
# http://www.wtfpl.net/about/
import os
from flask import Flask, request, render_template, abort, redirect, url_for, g
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, desc, asc
from flask.ext.sqlalchemy import SQLAlchemy # needed?
from datetime import datetime, timedelta
from random import randint

# For logging
import logging
from logging.handlers import TimedRotatingFileHandler
from flask_debugtoolbar import DebugToolbarExtension

app = Flask(__name__)

# config section (move to config file later)
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'db', 'sqlite.db'),
    DEBUG=True,
    SECRET_KEY='totallysecretkeyImgoingtouploadtogithub',
    USERNAME='admin',
    PASSWORD='default',
    # Set to True to intercept redirects for debugging purposes..
    DEBUG_TB_INTERCEPT_REDIRECTS=False
))

app.config.from_envvar('FLASKR_SETTINGS', silent=True)

# Get debug toolbar with included log messages etc on every successfully rendered page.
toolbar = DebugToolbarExtension(app)

# Logging
handler = TimedRotatingFileHandler('log/foo.log', when='midnight', interval=1)
handler.setLevel(logging.INFO)

# Format log strings to include timestamp and function names automatically.
formatter = logging.Formatter( "%(asctime)s | %(pathname)s:%(lineno)d | %(funcName)s | %(levelname)s | %(message)s ")
handler.setFormatter(formatter)

# Add handler to app.
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# Enable SQL and bind variable logging from sqlalchemy...
logging.getLogger('sqlalchemy').setLevel(logging.DEBUG)

# SQLAlchemy instead of the horrible stuff...
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        engine = create_engine('sqlite:///'+app.config['DATABASE'], convert_unicode=True)
        metadata = g._metadata = MetaData(bind=engine)
        db = g._database = engine.connect()
    return db

# Way 1 to perform queries with sqlalchemy, returns proxy with rows to iterate over
#systemlistsql = engine.execute('select * from collectionsystem where systemid = :1', 1)
#app.logger.info('Clean run:')
#for row in systemlistsql:
#    app.logger.info('System: %s', row['systemname'])

# Way 2 to perform queries with sqlalchemy, returns proxy with rows to iterate over
#systemsobj = Table('collectionsystem', metadata, autoload=True)
# fetchall or first or fetchone or
#sysresult = systemsobj.select(systemsobj.c.systemid ==1).execute().fetchall()
#sysresult = systemsobj.select().execute().fetchall()
#for row in sysresult:
#    app.logger.info(row['threshold'])

def getTable(table):
    get_db()
    return Table(table, g._metadata, autoload=True)

def runTestQuery(table):
    result =table.select().execute().fetchall()
    for row in result:
        app.logger.info(row['systemname'])
    return True

def init_db():
    # TODO: Update to sqlalchemy
    with app.app_context():
        db = get_db()
        with app.open_resource('db\schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.teardown_appcontext
#def close_connection(exception):
    #db = getattr(g, '_database', None)
    #if db is not None:
        #db.close()


@app.route('/')
def showDefault():
    return render_template('base.html')

@app.route('/refreshdb')
def refreshDB():
    init_db()
    return render_template('base.html', performed='init_db()', data = None)

@app.route('/user/')
@app.route('/user/<string:username>')
def show_greeting(username):
    # renders template hello.html and passes username from URI to name variable in template
    return render_template('base.html', name=username)

@app.route('/system/register/<system>/<percentage>')
@app.route('/system/register/<system>/<percentage>/<meta>')
def register_health(system, percentage, meta = None):
    now = datetime.utcnow() #.strftime("%Y-%m-%d %H:%M:%S") sqlalchemy won't accept pre-formatted strings
    if percentage == 'random':
        percentage = randint(0,100)

    systemInfo = getSystem(system)
    healthTable = getTable('healthstatus')
    if systemInfo:
        app.logger.info('Inserting data point for %s system (%s) at current time', system, percentage)
        result = healthTable.insert().values(systemid=systemInfo['systemid'],when=now,status=percentage).execute()
        return redirect('/system/list')
    else:
        return redirect('/')

@app.route('/system/view/<system>/')
@app.route('/system/view/<system>/<modifier>')
def display_system(system, modifier = False):
    app.logger.info('Displaying data for %s system', system)
    systemHealthPoints = getSystemHealth(system, modifier)
    modifiedHealthPoints = {}
    for point in systemHealthPoints:
        modifiedHealthPoints[point['when'].strftime("%Y-%m-%d %H:%M:%S")] = {
            'status': point['status'],
            'who': point['who'],
            'meta': point['meta']
            }
    app.logger.info('Modified data: %s', str(modifiedHealthPoints))
    return render_template('systemViewSingle.html', healthData=modifiedHealthPoints, system=system)

def getSystem(system = None):
    # TODO: also accept ID
    if system != None:
        app.logger.info('Looking up %s', system)
        systemTable = getTable('collectionsystem')
        systemInfo = systemTable.select(systemTable.c.systemname == system).execute().first()
        app.logger.info('Got %s', str(systemInfo))
    else:
        app.logger.info('Looking up all systems')
        systemTable = getTable('collectionsystem')
        systemInfo = systemTable.select().order_by(desc(systemTable.c.systemname)).execute().fetchall()
        app.logger.info('Got %s', str(systemInfo))
    return systemInfo

def getSystemHealth(system,modifier = None):
    thisSystemInfo = getSystem(system)
    # TODO: also accept ID
    app.logger.info("Getting health data for ID %s, name %s", thisSystemInfo['systemid'], thisSystemInfo['systemname'])
    dateNow = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    dateToday = datetime.utcnow().date()
    dateCurrentStart = dateToday.strftime("%Y-%m-%d %H:%M:%S")
    healthTable = getTable('healthstatus')
    if modifier == 'all':
        healthInfo = healthTable.select(healthTable.c.systemid == thisSystemInfo['systemid']).order_by(desc(healthTable.c.when)).execute().fetchall()
        app.logger.info("Got data: %s", str(healthInfo))
        return healthInfo
    elif modifier == 'week':
        dateCurrentStart = (dateToday - timedelta(weeks=1)).strftime("%Y-%m-%d %H:%M:%S")
    elif modifier == 'month':
        dateCurrentStart = (dateToday - timedelta(weeks=4)).strftime("%Y-%m-%d %H:%M:%S")
    healthInfo = healthTable.select(healthTable.c.systemid == thisSystemInfo['systemid']).where(healthTable.c.when.between(dateCurrentStart,dateNow)).order_by(desc(healthTable.c.when)).execute().fetchall()
    app.logger.info("Got data (fromdate %s): %s", dateCurrentStart, healthInfo)
    return healthInfo

@app.route('/system/list')
def list_systems():
    app.logger.info('running getSystem with no parameters')
    systems = getSystem()
    app.logger.info('got these systems in return: %s', str(systems))
    systemList = {}
    for system in systems:
        app.logger.info('looking up health from %s', str(system['systemname']))
        thisSystemHealthPoints = getSystemHealth(system['systemname'])
        thisModifiedHealthPoints = {}
        for point in thisSystemHealthPoints:
            thisModifiedHealthPoints[point['when'].strftime("%Y-%m-%d %H:%M:%S")] = {
                'status': point['status'],
                'who': point['who'],
                'meta': point['meta']
                }
        systemList[system['systemname']] = {
            'systemname': system['systemname'],
            'threshold': system['threshold'],
            'description': system['description'],
            'healthdata': thisModifiedHealthPoints,
            's_t': False
        }

    app.logger.info('Built systemlist: %s', str(systemList))
    return render_template('systemList.html', systems = systemList)

if __name__ == '__main__':
    #app.debug = True # enable debug mode to make server reload on code changes.
    app.run(host='0.0.0.0',port=1337,debug = True)
