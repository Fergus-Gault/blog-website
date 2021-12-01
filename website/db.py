import sqlite3
from sqlite3.dbapi2 import register_adapter

import shortuuid

from werkzeug.security import generate_password_hash

import click
from flask import current_app, g
from flask.cli import with_appcontext

def get_db():
    if 'db' not in g:
        sqlite3.register_adapter(shortuuid.uuid, lambda u :u.bytes_le)
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    
    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

    db.execute(
        'INSERT INTO user (id, username, email, password, admin, emailConfirmed)'
        ' VALUES (?,?,?,?,?,?)', (shortuuid.uuid(), 'admin', 'ad@min.com', generate_password_hash('root'), 1, 1)
        )
    db.commit()

def make_admin(username):
    db = get_db()
    db.execute('UPDATE user SET admin=1, emailConfirmed=1 WHERE username = ?', (username,))
    db.commit()

def remove_admin(username):
    db = get_db()
    db.execute('UPDATE user SET admin=0, emailConfirmed=1 WHERE username = ?', (username,))
    db.commit()

@click.command('init-db')
@with_appcontext
def init_db_command():
    # Clears the exsiting data and create new tables
    init_db()
    click.echo('Initialised the database.')


@click.command('make-admin')
@click.argument('username')
@with_appcontext
def make_admin_command(username):
    # Makes user an admin.
    make_admin(username)
    click.echo(f'{username} is now an admin.')


@click.command('remove-admin')
@click.argument('username')
@with_appcontext
def remove_admin_command(username):
    # Removes admin from user
    remove_admin(username)
    click.echo(f'{username} is no longer an admin.')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(make_admin_command)
    app.cli.add_command(remove_admin_command)