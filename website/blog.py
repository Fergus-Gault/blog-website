# IMPORTS
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

import shortuuid

from werkzeug.exceptions import abort

from website.auth import load_logged_in_user, login, login_required
from website.db import get_db

bp = Blueprint('blog', __name__)

@bp.route('/') # Creates a route in the base directory for the index page
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall() # Selects all data from the 'post' table
    return render_template('blog/index.html', posts=posts) # Renders the page

@bp.route('/create', methods=('GET', 'POST')) # Creates route 
@login_required # Requires login to create post
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['content']
        error = None

        if not title:
            error = 'Title is required.'
        if error is not None:
            flash(error)

        else:
            db = get_db()
            db.execute('INSERT INTO post (id, title, body, author_id) VALUES (?,?,?,?)',
                        (shortuuid.uuid(), title, body, g.user['id']))
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post was not found.")
    
    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post

@bp.route('/post/<string:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)
    
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['content']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title=?, body=?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))
    
    return render_template('blog/update.html', post=post)

@bp.route('/<string:id>/delete', methods=("POST",))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute(
        'DELETE FROM post WHERE id=?', (id,)
    )
    db.execute(
        'DELETE FROM comment WHERE post_id=?', (id,) # SOMETHING WRONG WITH THIS STATEMENT
    )
    db.commit()
    return redirect(url_for('blog.index'))


@bp.route('/user/<username>')
def profile(username):
    db = get_db()

    checkUser = db.execute('SELECT username FROM user WHERE username = ?', (username,)).fetchone()
    if checkUser is None:
        abort(404, f"Username doesn't exist.")

    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE username = ?'
        ' ORDER BY created DESC'
        ,(username,)).fetchall()

    return render_template('blog/profile.html', posts=posts, username=username)


@bp.route('/post/<string:id>', methods=('POST', 'GET',))
def viewPost(id):
    #SELECTS INFO FOR POST
    get_post(id, check_author=False) # Gets the post but doesn't check for author so anyone can view
    db = get_db() # Gets database
    post = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id' 
        ' WHERE p.id=?', (id,)
    ).fetchone() # Fetches one result

    #CODE FOR ADDING COMMENTS
    if request.method == 'POST': # Checks if the comment has been submitted
        body = request.form['content'] # Gets the content of the comment
        error = None

        if not body: # Prints error if no body
            error = 'Comment must contain text.'

        if error is not None:
            flash(error)
        
        else:
            db = get_db()
            db.execute(
                'INSERT INTO comment (commentID, body, author_id, post_id)'
                ' VALUES (?,?,?,?)',
                (shortuuid.uuid(), body, g.user['id'], id,) # Inserts the content of the comment, the id of the author, and the id of the post that the comment is on.
            )
            db.commit()

    comments = db.execute(
        'SELECT p.id, c.commentID, c.post_id, c.body, c.created, c.author_id, u.username'
        ' FROM comment c JOIN user u ON c.author_id = u.id'
        ' JOIN post p ON p.id = c.post_id'
        ' WHERE p.id = ?'
        ' ORDER BY c.created DESC',
        (id,)).fetchall()


    return render_template('blog/post.html', post=post, comments=comments)


@bp.route('/<string:postID>/<string:commID>/deleteComment')
@login_required
def deleteComment(commID, postID):
    db = get_db()
    db.execute(
        'DELETE FROM comment WHERE commentID=?', (commID,)
    )
    db.commit()
    return redirect(url_for('blog.viewPost', id=postID))