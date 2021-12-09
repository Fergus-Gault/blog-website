# IMPORTS
import sqlite3
from sqlite3.dbapi2 import register_adapter

import shortuuid

from werkzeug.security import generate_password_hash

import click
from flask import current_app, g
from flask.cli import with_appcontext

#Gets the database connection
def get_db():
    if 'db' not in g: # If not already connected, connect
        sqlite3.register_adapter(shortuuid.uuid, lambda u :u.bytes_le) # Registers the adapter to allow UUID's
        g.db = sqlite3.connect(
            current_app.config['DATABASE'], # Gets the database from the DATABASE field in __init__.py
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row # Converts rows into dictionary
    
    return g.db

def close_db(e=None): # Closes database
    db = g.pop('db', None) # Removes the database from g

    if db is not None:
        db.close() # Closes database connection

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f: # Opens SQL file
        db.executescript(f.read().decode('utf8')) # Executes the script, creating the tables

    db.execute(
        'INSERT INTO user (id, username, email, password, admin, emailConfirmed)'
        ' VALUES (?,?,?,?,?,?)', (shortuuid.uuid(), 'admin', 'ad@min.com', generate_password_hash('root'), 1, 1)
        ) # Creates an admin account
    db.commit() # Commits changes to the database

def make_admin(username): # Allows user to make an account admin (Command Line only)
    db = get_db()
    db.execute('UPDATE user SET admin=1, emailConfirmed=1 WHERE username = ?', (username,))
    db.commit()

def remove_admin(username): # Allows the user to remove an account with admin (Command Line only)
    db = get_db()
    db.execute('UPDATE user SET admin=0, emailConfirmed=1 WHERE username = ?', (username,))
    db.commit()

@click.command('init-db') # Creates a command to init-db
@with_appcontext # Ensures the command is being ran within the website environment
def init_db_command():
    # Clears the exsiting data and create new tables
    init_db() # Initialises the database
    click.echo('Initialised the database.')


@click.command('make-admin') # Creates a command to make-admin
@click.argument('username') # Adds an arguement which gets the text that follows the command call
@with_appcontext # Ensures context
def make_admin_command(username):
    # Makes user an admin.
    make_admin(username)
    click.echo(f'{username} is now an admin.')


@click.command('remove-admin') # Creates a command to remove-admin
@click.argument('username') # Adds arguement
@with_appcontext
def remove_admin_command(username):
    # Removes admin from user
    remove_admin(username)
    click.echo(f'{username} is no longer an admin.')


def init_app(app):
    app.teardown_appcontext(close_db) # When the app is stopped/closed the database is closed
    app.cli.add_command(init_db_command) # Adds the command to the app
    app.cli.add_command(make_admin_command) # "                         "
    app.cli.add_command(remove_admin_command) # "                           "