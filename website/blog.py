# IMPORTS
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

import shortuuid

from werkzeug.exceptions import abort

from website.auth import load_logged_in_user, login, login_required
from website.db import get_db

bp = Blueprint('blog', __name__) # Creates blueprint for 'blog'

@bp.route('/') # Creates a route in the base directory for the index page
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts) # Renders the page


@bp.route('/create', methods=('GET', 'POST')) # Creates route for the create page
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['content']
        error = None

        if not title:
            error = 'Title is required.'
        if len(title) > 40:
            error = 'Title must be less than 40 characters long.'
        if len(body) > 500:
            error = 'Body must be less than 500 characters long.'
        if error is not None:
            flash(error, 'error') # Flashes error

        else: # If valid the inserts into post table with random UUID and redirects to home page
            db = get_db() 
            db.execute('INSERT INTO post (id, title, body, author_id) VALUES (?,?,?,?)',
                        (shortuuid.uuid(), title, body, g.user['id']))
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html') # Renders the page


def get_post(id, check_author=True): # Gets post and checks for author by default
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone() # Gets specific post

    if post is None: # If post doesn't exist then error is thrown
        abort(404, f"Post was not found.")
    
    if (check_author and post['author_id'] != g.user['id']) and (g.user['admin'] != 1): # Makes sure user is the author or an admin.
        abort(403)

    return post


def get_favs(id): # Gets the favourite posts for the user
    favs = get_db().execute(
        'SELECT p.id, title, body, created, p.author_id, username, f.post_id'
        ' FROM post p JOIN user u ON p.author_id = u.id JOIN favourite f ON f.post_id = p.id'
        ' WHERE f.author_id = ?'
        ' ORDER BY p.created DESC', (id,)
    ).fetchall()

    return favs # Returns all favourite posts


@bp.route('/post/<string:id>/update', methods=('GET', 'POST')) # Creates route for updating post
@login_required
def update(id):
    post = get_post(id) # Gets post and checks if user is author
    
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['content']
        error = None

        if not title:
            error = 'Title is required.'
        if len(title) > 40:
            error = 'Title must be less than 40 characters long.'
        if len(body) > 500:
            error = 'Body must be less than 500 characters long.'
        if error is not None:
            flash(error, 'error') # Flashes error
        
        else: # If valid, updates post
            db = get_db()
            db.execute(
                'UPDATE post SET title=?, body=?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index')) # Redirects to index
    
    return render_template('blog/update.html', post=post) # Renders the page


@bp.route('/<string:id>/delete', methods=("POST",)) # Creates route for deleting post
@login_required
def delete(id):
    get_post(id) # Makes sure user is the author
    db = get_db()
    # Deletes the post, comments on that post, and removes it from favourites table
    db.execute(
        'DELETE FROM post WHERE id=?', (id,)
    )
    db.execute(
        'DELETE FROM comment WHERE post_id=?', (id,)
    )
    db.execute(
        'DELETE FROM favourite WHERE post_id=?',(id,)
    )
    db.commit()

    return redirect(url_for('blog.index')) # Redirects to index


@bp.route('/user/<string:id>') # Creates route for user profile
def profile(id):
    db = get_db()

    checkUser = db.execute('SELECT id, username FROM user WHERE id = ?', (id,)).fetchone() # Checks if user exists
    if checkUser is None:
        abort(404, f"User doesn't exist.") # Aborts

    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE u.id = ?'
        ' ORDER BY created DESC'
        ,(id,)).fetchall() # Gets all posts from user

    if g.user: # If profile is the current user
        favourites = get_favs(id)
    else:
        favourites=None

    return render_template('blog/profile.html', posts=posts, username = checkUser['username'], id=id, favourites=favourites) # Renders the page


@bp.route('/post/<string:id>', methods=('POST', 'GET',)) # Creates a route for the post
def viewPost(id):
    #SELECTS INFO FOR POST
    get_post(id, check_author=False) # Gets the post but doesn't check for author so anyone can view

    db = get_db()
    
    post = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id' 
        ' WHERE p.id=?', (id,)
    ).fetchone() # Fetches one result
    
    if g.user: # If user is logged in check for favourite
        checkFav = db.execute(
                'SELECT f.post_id, f.id'
                ' FROM favourite f JOIN user u ON f.author_id = u.id'
                ' WHERE f.post_id =? AND f.author_id=?',
                (id, g.user['id'],)).fetchone()

        if checkFav == None:
            isFav = 0
        else:
            isFav = 1
    else:
        isFav=None

    #CODE FOR ADDING COMMENTS
    if request.method == 'POST':
        body = request.form['content'] # Gets the content of the comment
        error = None

        if not body: # Prints error if no body
            error = 'Comment must contain text.'
        if len(body) > 250:
            error = 'Comment must be less than 250 characters long.'
        if error is not None:
            flash(error)
        
        else:
            db = get_db()
            db.execute(
                'INSERT INTO comment (commentID, body, author_id, post_id)'
                ' VALUES (?,?,?,?)',
                (shortuuid.uuid(), body, g.user['id'], id,)
                # Inserts the content of the comment, the id of the author, and the id of the post that the comment is on.
                )
            db.commit()

    comments = db.execute(
        'SELECT c.commentID, c.post_id, c.body, c.created, c.author_id, u.username'
        ' FROM comment c JOIN user u ON c.author_id = u.id'
        ' WHERE c.post_id = (SELECT id FROM post p WHERE p.id = ?)',
        (id,)).fetchall() # Fetches all the comments on the post

    return render_template('blog/post.html', post=post, comments=comments, isFav=isFav) # Renders the page
    

@bp.route('/<string:postID>/<string:commID>/deleteComment') # Creates route for deleting comment
@login_required
def deleteComment(commID, postID):
    db = get_db()
    
    db.execute(
        'DELETE FROM comment WHERE commentID=?', (commID,)
    ) # Deletes comment
    db.commit()

    return redirect(url_for('blog.viewPost', id=postID)) # Redirects the post


@bp.route('/post/<string:id>/addFavourite', methods=('POST',)) # Creates route for adding to favourite
@login_required
def addFavourite(id):
    db = get_db()

    if request.method == "POST":
        db.execute(
            'INSERT INTO favourite (id, post_id, author_id)' 
            ' VALUES (?,?,?)',
            (shortuuid.uuid(), id, g.user['id'],)
            ) # Adds post to the favourite table
        db.commit()

        flash('Post added to favourites.', 'message') # Flashes message
    
    return redirect(url_for('blog.viewPost', id=id)) # Redirects to the post


@bp.route('/post/<string:id>/removeFavourite', methods=('POST',)) # Creates route for removing favourite
@login_required
def removeFavourite(id):
    db = get_db()
    
    if request.method == "POST":
        db.execute(
            'DELETE FROM favourite WHERE post_id=?',(id,)
        ) # Removes from favourite table
        db.commit()

        flash('Post removed from favourites.', 'error') # Flashes message

    return redirect(url_for('blog.viewPost', id=id)) # Redirects to the post