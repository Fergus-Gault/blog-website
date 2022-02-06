#IMPORTS
import os
from flask import Flask
from flask.templating import render_template

#404 Error page
def page_not_found(e):
    return render_template('errors/404.html', error=e), 404

#403 Error page
def page_access_forbidden(e):
    return render_template('errors/403.html', error=e), 403

#500 Error page
def internal_server_error(e):
    return render_template('errors/500.html', error=e), 500

def create_app(test_config=None):
    # Create and configure app
    app = Flask(__name__, instance_relative_config=True) # Creates app
    # Registers error handlers and calls function when error is found
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(403, page_access_forbidden)
    app.register_error_handler(500, internal_server_error)
    
    app.config.from_mapping(
        SECRET_KEY='dev', # Secret key !!!CHANGE ON LAUNCH!!!
        DATABASE=os.path.join(app.instance_path, 'website.db'), # DATABASE called in db.py within the instance folder
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)

    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app) # Initialises the app

    from . import auth
    app.register_blueprint(auth.bp) # Registers the auth blueprint

    from . import blog
    app.register_blueprint(blog.bp) # Registers the blog blueprint
    app.add_url_rule('/', endpoint='index') # Sets the index endpoint to the base URL

    return app # Returns configured app
