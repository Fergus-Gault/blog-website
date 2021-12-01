import os
from flask import Flask
from flask.templating import render_template

def page_not_found(e):
    return render_template('errors/404.html', error=e), 404

def page_access_forbidden(e):
    return render_template('errors/403.html', error=e), 403

def internal_server_error(e):
    return render_template('errors/500.html', error=e), 500

def create_app(test_config=None):
    # Create and configure app
    app = Flask(__name__, instance_relative_config=True)
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(403, page_access_forbidden)
    app.register_error_handler(500, internal_server_error)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'website.sqlite'),
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
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='index')

    return app
