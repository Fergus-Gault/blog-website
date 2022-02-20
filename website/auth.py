# IMPORTS
import functools

import shortuuid

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from website.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth') # Creates auth blueprint


#Register function
@bp.route('/register', methods=('GET', 'POST')) # Creates route to the register page
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        db = get_db()
        error = None

        #SHOULDN'T RUN as validation done client-side
        if not username:
            error = 'Username is required.'
        elif len(username) < 3 or len(username) > 15:
            error= 'Username must be between 3 and 15 characters long.'
        elif not email: 
            error = 'Email is required.'
        elif len(email) < 3 or len(email) > 15:
            error= 'Email must be between 3 and 15 characters long.'
        elif not password:
            error = 'Password is required.'
        elif len(password) < 3 or len(password) > 24:
            error= 'Password must be between 3 and 24 characters long.'
        
        if error is None:
            try: # Tries to add data to table
                db.execute(
                    "INSERT INTO user (id, username, email, password) VALUES (?,?,?,?)",
                    (shortuuid.uuid(), username, email, generate_password_hash(password)), # Inserts data with a hashed password
                )
                db.commit()
                user = db.execute(
                    'SELECT * FROM user WHERE username = ?', (username,)
                    ).fetchone() # Gets the username that was entered
                session['user_id'] = user['id'] # Sets session id to the user id

            except db.IntegrityError as e: # If the username or email is already entered
                if "username" in str(e):
                    error = f'Username is already registered.'
                elif "email" in str(e):
                    error = f'Email is already registered.'
            else:
                flash('Account creation successful', 'message')
                return redirect(url_for('blog.index')) # Retirects to index
        
        flash(error, 'error') # Flashes error is there is one
    
    return render_template('auth/register.html') # Renders the page


# Login function
@bp.route('/login', methods=('GET', 'POST')) # Creates route to the login page
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        error = None

        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone() # Gets the user

        if user is None:
            error = 'Incorrect username.' # If username not found then throw error
        elif not check_password_hash(user['password'], password): # De-hashes password and checks
            error = 'Incorrect password.'

        if error is None:
            session.clear() # Clears previous session
            session['user_id'] = user['id'] # Creates new session for the new user
            flash('Login successful', 'message')
            return redirect(url_for('index')) # Redirects to index

        flash(error, 'error') # Flashes error

    return render_template('auth/login.html') # Renders the page


@bp.before_app_request # Before the website is loaded
def load_logged_in_user():
    user_id = session.get('user_id') # Gets logged in user

    if user_id is None:
        g.user = None # If no user, set g.user to None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone() # Sets g.user to logged in user


# Logout function
@bp.route('/logout') # Creates route to logout
def logout():
    session.clear()
    return redirect(url_for('index')) # Redirects to index


def login_required(view): # Creates login_required function
    @functools.wraps(view) # Creates a decorator for the function
    def wrapped_view(**kwargs): # Function that is ran when decorator is called
        if g.user is None: # If there is no logged in user
            return redirect(url_for('auth.login')) # Redirect to login page
        return view(**kwargs)

    return wrapped_view