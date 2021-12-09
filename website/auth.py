# IMPORTS
import functools

import shortuuid

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from website.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth') # Creates auth blueprint

@bp.route('/register', methods=('GET', 'POST')) # Creates route to the register page
def register():
    if request.method == 'POST': # If form submitted
        username = request.form['username'] # Get the username from the form
        email = request.form['email'] # Gets the email from the form
        password = request.form['password'] # Gets the password from the form
        
        db = get_db() # Gets the database
        error = None # No error

        #SHOULDN'T run as validation done client-side
        if not username:
            error = 'Username is required.' # Sets error if no username
        elif not email: 
            error = 'Email is required.' # Sets error if no email
        elif not password:
            error = 'Password is required.' # Sets error if no password
        
        if error is None: # If there is no error
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
                return redirect(url_for('blog.index')) # Retirects to index
        
        flash(error, 'error') # Flashes error is there is oe
    
    return render_template('auth/register.html') # Renders the page


@bp.route('/login', methods=('GET', 'POST')) # Creates route to the login page
def login():
    if request.method == 'POST': # If the form is submitted
        username = request.form['username'] # Gets username from form
        password = request.form['password'] # Gets password from form
        
        db = get_db() # Gets database
        error = None # Error is none

        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone() # Gets the user

        if user is None:
            error = 'Incorrect username.' # If username not found then throw error
        elif not check_password_hash(user['password'], password): # De-hashes password and checks
            error = 'Incorrect password.'

        if error is None: # If no error
            session.clear() # Clears previous session
            session['user_id'] = user['id'] # Creates new session for the new user
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


@bp.route('/logout') # Creates route to logout
def logout():
    session.clear() # Clears session
    return redirect(url_for('index')) # Redirects to index


def login_required(view): # Creates login_required function
    @functools.wraps(view) # Creates a decorator for the function
    def wrapped_view(**kwargs): # Function that is ran when decorator is called
        if g.user is None: # If there is no logged in user
            return redirect(url_for('auth.login')) # Redirect to login page
        return view(**kwargs)

    return wrapped_view