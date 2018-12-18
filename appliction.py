# python 3.7

from flask import (Flask,
                   render_template,
                   request,
                   redirect,
                   jsonify,
                   url_for,
                   flash)
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Items, User
from flask import session as login_session
import random
import string
from sqlalchemy.pool import SingletonThreadPool
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from datetime import datetime

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db?check_same_thread=False')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        print (login_session['state'])
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1].decode())
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
                                'Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '''" style = "width: 300px;
     height: 300px;border-radius: 150px;-webkit-border-radius: 150px;
     -moz-border-radius: 150px;"> '''
    flash("you are now logged in as %s" % login_session['username'])
    print ("done!")
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        del login_session['gplus_id']
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['user_id']
        return redirect(url_for('Home'))
    else:
        response = make_response(json.dumps(
                        'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs
@app.route('/catalog.json')
def catalogJSON():
    item = session.query(Items).all()
    return jsonify(items=[i.serialize for i in item])


@app.route('/')
@app.route('/catalog')
def Home():
    category = session.query(Category).all()
    items = session.query(Items).order_by(Items.time.desc()).all()
    return render_template('Home.html', category=category, items=items)


@app.route('/catalog/<id>/items')
def showCategory(id):
    category = session.query(Category).all()
    category1 = session.query(Category).filter_by(name=id).one()
    items = session.query(Items).filter_by(category_id=category1.id).all()
    return render_template(
                'showCategory.html',
                category=category, categoryName=category1.name, items=items)


@app.route('/catalog/<category>/<item>')
def showItem(category, item):
    category = session.query(Category).filter_by(name=category).one()
    item = session.query(Items).filter_by(
           category_id=category.id, name=item).first()
    return render_template('showItem.html', category=category, item=item)


@app.route('/catalog/new', methods=['GET', 'POST'])
def NewItem():
    category = session.query(Category).all()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        categoryId = session.query(Category).filter_by(
                                          name=request.form['category']).one()
        item = Items(
                    name=request.form['name'],
                    description=request.form['description'],
                    time=str(datetime.now()),
                    category_id=categoryId.id,
                    user_id=login_session['user_id']
        )
        session.add(item)
        session.commit()
        return redirect(url_for('showItem',
                                category=categoryId.name, item=item.name))
    else:
        return render_template('newItem.html', category=category)


@app.route('/catalog/<category>/<item>/edit', methods=['GET', 'POST'])
def EditItem(category, item):
    AllCategory = session.query(Category).all()
    category = session.query(Category).filter_by(name=category).one()
    item = session.query(Items).filter_by(
                                category_id=category.id, name=item).one()
    if 'username' not in login_session:
        return redirect('/login')
    if login_session['user_id'] != item.user_id:
        return """<script>function myFunction()
        {alert('You are not authorized to edit this itme.');
        window.location.href = '/';}</script
        ><body onload='myFunction()'>"""
    if request.method == 'POST':
        if request.form['name']:
            item.name = request.form['name']
            item.time = str(datetime.now())
        if request.form['description']:
            item.description = request.form['description']
            item.time = str(datetime.now())
        if request.form['category']:
            NewCategory = session.query(Category).filter_by(
                          name=request.form['category']).one()
            item.category_id = NewCategory.id
            item.time = str(datetime.now())
        session.add(item)
        session.commit()
        return redirect(url_for('showItem',
                        category=NewCategory.name, item=item.name))
    else:
        return render_template(
                'editItem.html',
                AllCategory=AllCategory, category=category.name, item=item)


@app.route('/catalog/<category>/<item>/delete', methods=['GET', 'POST'])
def DeleteItem(category, item):
    category = session.query(Category).filter_by(name=category).one()
    item = session.query(Items).filter_by(
            category_id=category.id, name=item).one()
    if 'username' not in login_session:
        return redirect('/login')
    if login_session['user_id'] != item.user_id:
        return """<script>function myFunction()
        {alert('You are not authorized to delete this item.');
        window.location.href = '/';}</script>
        <body onload='myFunction()'>"""
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        return redirect(url_for('showCategory', id=category.name))
    else:
        return render_template(
                'deleteItem.html', category=category.name, item=item)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
