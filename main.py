import facebook
from flask import Flask
import httplib2
from flask import Flask, render_template, jsonify
from flask import make_response
from flask import redirect
from flask import request
from flask import session
from flask import url_for
from oauth2client.client import flow_from_clientsecrets
from pip._vendor import requests
from pyasn1_modules.rfc1902 import Integer
from sqlalchemy.orm import sessionmaker
import database
import json

app = Flask(__name__)
dbSession = sessionmaker(bind=database.engine)
Db = dbSession()


@app.route('/')
@app.route('/restaurants')
def Restaurants():
    # init all session with none values
    if 'state' not in session:
        session['state'] = None
    if 'username' not in session:
        session['username'] = None
    if 'id' not in session:
        session['id'] = None
    # getting all the restaurants from the DB
    restaurants = Db.query(database.Restaurant).all()
    # rendering list of restaurants
    return render_template(
        'list.html',
        state=session['state'],
        restaurants=restaurants)


@app.route('/restaurants/<int:restaurant_id>')
def Items(restaurant_id):
    restaurant = Db.query(
        database.Restaurant).filter_by(
        id=restaurant_id).one()
    # getting all the items for the selected restaurant from the DB
    items = Db.query(database.MenuItem).filter_by(restaurant_id=restaurant.id)
    id = session['id']
    return render_template(
        'items.html',
        state=session['state'],
        items=items,
        restaurant=restaurant,
        user_id=id)


@app.route('/restaurants/<int:restaurant_id>/newitem', methods=['GET', 'POST'])
def createMenuItem(restaurant_id):
    if request.method == 'GET':
        # check user login state
        if session['state'] is not None:
            # if user is logged in then he is authorised to add menu item
            return render_template(
                'create.html',
                restaurant_id=restaurant_id,
                state=session['state'])
        else:
            return "You should login to create items"
    else:
        # check user login state
        if session['state'] is not None:
            restaurant = Db.query(
                database.Restaurant).filter_by(
                id=restaurant_id).one()
            name = request.form['name']
            course = request.form['course']
            price = request.form['price']
            description = request.form['description']
            user_id = session['id']
            # validating the coming data
            if name != '' and course != ''\
                    and price != '' and description != '':
                newItem = database.MenuItem(
                    user_id=user_id,
                    course=course,
                    name=name,
                    price=price,
                    restaurant=restaurant,
                    description=description)
                Db.add(newItem)
                Db.commit()
                return redirect(
                    url_for(
                        "Items",
                        state=session['state'],
                        restaurant_id=restaurant.id))
            else:
                # show user empty field error in case of validation failure
                return render_template(
                    'create.html',
                    error='some fields are empty!',
                    name=name,
                    course=course,
                    price=price,
                    description=description)
            print session['id']


@app.route(
    '/restaurants/<int:restaurant_id>/edit/<int:item_id>',
    methods=[
        'GET',
        'POST'])
def editMenuItem(restaurant_id, item_id):
    # check user login state
    if session['state'] is not None:
        # get the item the user wants to edit form DB
        editedItem = Db.query(database.MenuItem).filter_by(id=item_id).one()
        if int(editedItem.user_id) == int(session['id']):
            if request.method == 'GET':
                return render_template(
                    'edit.html',
                    item=editedItem,
                    restaurant_id=restaurant_id,
                    state=session['state'])
            else:
                name = request.form['name']
                course = request.form['course']
                price = request.form['price']
                description = request.form['description']
                editedItem.name = name
                editedItem.price = price
                editedItem.description = description
                editedItem.course = course
                Db.add(editedItem)
                Db.commit()
                return redirect(
                    url_for(
                        'Items',
                        state=session['state'],
                        restaurant_id=restaurant_id))
        else:
            return "you can only edit your items"
    else:
        return 'You should login to edit items'


@app.route(
    '/restaurants/<int:restaurant_id>/delete/<int:item_id>',
    methods=[
        'GET',
        'POST'])
def deleteMenuItem(restaurant_id, item_id):
    # check user login state
    if session['state'] is not None:
        # get the item the user wants to delete form DB
        item_delete = Db.query(database.MenuItem).filter_by(id=item_id).one()
        if int(item_delete.user_id) == int(session['id']):
            if request.method == 'GET':
                return render_template(
                    'delete.html',
                    restaurant_id=restaurant_id,
                    item_id=item_id,
                    state=session['state'])
            else:
                Db.delete(item_delete)
                Db.commit()
                return redirect(url_for('Items', restaurant_id=restaurant_id))
        else:
            return "you can only delete your items"

    else:
        return 'You should login to delete item'

# JSON endpoint for restaurants


@app.route('/restaurants/JSON')
def restaurantsJSON():
    restaurants = Db.query(database.Restaurant).all()
    return jsonify(restaurants=[r.serialize for r in restaurants])

# JSON endpoint for restaurant menu items


@app.route('/restaurants/<int:restaurant_id>/JSON')
def restaurantMenuJSON(restaurant_id):
    restaurant = Db.query(
        database.Restaurant).filter_by(
        id=restaurant_id).one()
    items = Db.query(database.MenuItem).filter_by(
        restaurant_id=restaurant_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])

# JSON endpoint for restaurant menu item


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    Menu_Item = Db.query(database.MenuItem).filter_by(id=menu_id).one()
    return jsonify(Menu_Item=Menu_Item.serialize)


@app.route('/signup', methods=['POST', 'GET'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        # check user login state
        if session['state'] is None:
            if request.method == 'POST':
                name = request.form['username']
                password = request.form['password']
                verify = request.form['verify']
                email = request.form['email']
                # validating the coming data
                if name != '' and email != ''\
                        and password != '' and verify != '':
                    if password == verify:
                        newUser = database.User(
                            name=name, password=password, email=email)
                        Db.add(newUser)
                        Db.commit()
                        session['provider'] = 'localauth'
                    else:
                        return render_template(
                            'register.html',
                            error='passwords does not match',
                            username=name,
                            email=email)
                else:
                    return render_template(
                        'register.html',
                        error='some fields are empty',
                        username=name,
                        email=email)
                return redirect(url_for('Restaurants'))
        else:
            return "You already logged in!"


@app.route('/fbLogin', methods=['POST'])
def fbLogin():
    print 'fb login'
    if session['state'] is None:  # validate user state
        access_token = request.data  # get access token from client
        # authenticate with facebook server this token
        app_id = json.loads(open('fb_client_oAuth.json', 'r').read())[
            'web']['app_id']
        app_secret = json.loads(
            open('fb_client_oAuth.json', 'r').read())['web']['app_secret']
        url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
            app_id, app_secret, access_token)
        h = httplib2.Http()
        result = json.loads(h.request(url, 'GET')[1])
        # now token is authenticated
        token = result['access_token']
        # get user data using graph request
        graph = facebook.GraphAPI(token)
        profile = graph.get_object('me')
        args = {'fields': 'id,name,email', }
        profile = graph.get_object('me', **args)
        session['state'] = profile['email']
        session['username'] = profile['name']
        id = int(profile['id'])
        session['id'] = id % 1000
        session['provider'] = 'facebook'
        session['access_token'] = access_token
        print profile['name']
        return redirect(url_for('Restaurants'))


@app.route('/googleLogin', methods=['POST'])
def googleLogin():
    print 'google login'
    if (session['state'] is None):  # validate user state
        code = request.data  # get google code
        oauth_flow = flow_from_clientsecrets(
            'google_client_oAuth.json', scope='', redirect_uri='postmessage')
        credentials = oauth_flow.step2_exchange(code)
        access_token = credentials.access_token
        url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
               % access_token)
        # request with google server to authenticate the code
        h = httplib2.Http()
        result = json.loads(h.request(url, 'GET')[1])
        if result.get('error') is not None:
            response = make_response(json.dumps(result.get('error')), 500)
            response.headers['Content-Type'] = 'application/json'
            print 'in if one'
            return response
        gplus_id = credentials.id_token['sub']

        if result['user_id'] != gplus_id:
            response = make_response(
                json.dumps("Token's user ID doesn't match given user ID."), 401)
            response.headers['Content-Type'] = 'application/json'
            print 'in if two'
            return response
        # the code is authenticated now fetch user data
        userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        params = {'access_token': credentials.access_token, 'alt': 'json'}
        answer = requests.get(userinfo_url, params=params)
        data = answer.json()
        session['state'] = data['email']
        session['username'] = data['name']
        id = int(data['id'])
        session['id'] = id % 1000
        session['access_token'] = access_token
        session['provider'] = 'google'
        print id
        print session['id']
        return redirect(url_for('Restaurants'))


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    if request.method == 'POST':
        if session['provider'] == 'facebook' and session['state'] is not None:
            access_token = session['access_token']
            facebook_id = session['id']
            # logout user from facebook
            url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (
                facebook_id, access_token)
            h = httplib2.Http()
            result = h.request(url, 'DELETE')[1]
            # delete user session
            del session['state']
            del session['username']
            del session['access_token']
            del session['id']

        elif session['provider'] == 'google' and session['state'] is not None:
            access_token = session['access_token']
            # logout user from google
            url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
            h = httplib2.Http()
            result = h.request(url, 'GET')[0]
            # delete user session and logout user from menu item app
            del session['state']
            del session['username']
            del session['access_token']
            del session['id']

        elif session['provider'] == 'localauth':
            # local authtication just delete user session
            del session['state']
            del session['username']
            del session['id']
        return redirect(url_for('Restaurants'))


if __name__ == '__main__':
    app.secret_key = 'awesome_catalog_app_udacity'
    app.debug = True
    app.run(host='0.0.0.0', port=4000)
