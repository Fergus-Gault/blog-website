from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from website.auth import login, login_required
from website.db import get_db

bp = Blueprint('blog', __name__)

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
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
            db.execute('INSERT INTO post (title, body, author_id) VALUES (?,?,?)',
                        (title, body, g.user['id']))
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
        abort(404, f"Post id {id} doesn't exist.")
    
    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
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

@bp.route('/<int:id>/delete', methods=("POST",))
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
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE username = ?'
        ' ORDER BY created DESC'
        ,(username,)).fetchall()

    return render_template('blog/profile.html', posts=posts, username=username)


@bp.route('/<int:id>', methods=('POST', 'GET',))
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
                'INSERT INTO comment (body, author_id, post_id)'
                ' VALUES (?,?,?)',
                (body, g.user['id'], id,)
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


@bp.route('/<int:postID>/<int:commID>/deleteComment', methods=('POST', 'GET',))
def deleteComment(commID, postID):
    db = get_db()
    db.execute(
        'DELETE FROM comment WHERE commentID=?', (commID,)
    )
    db.commit()
    return redirect(url_for('blog.viewPost', id=postID))