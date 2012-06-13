import os

import path

from flask import Flask
from flaskext.cache import Cache
from jinja2 import ModuleLoader

from kardboard.util import (
    PortAwareMongoEngine,
    slugify,
    timesince,
    jsonencode,
    configure_logging,
    newrelic_head,
    newrelic_foot,
    FixGunicorn
)


def get_app():
    app = Flask('kardboard')
    app.config.from_object('kardboard.default_settings')
    if os.getenv('KARDBOARD_SETTINGS', None):
        app.config.from_envvar('KARDBOARD_SETTINGS')

    app.secret_key = app.config['SECRET_KEY']

    app.db = PortAwareMongoEngine(app)

    app.jinja_env.add_extension('kardboard.util.Markdown2Extension')
    app.jinja_env.filters['slugify'] = slugify
    app.jinja_env.filters['timesince'] = timesince
    app.jinja_env.filters['jsonencode'] = jsonencode
    app.jinja_env.globals['newrelic_head'] = newrelic_head
    app.jinja_env.globals['newrelic_foot'] = newrelic_foot

    compiled_templates = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'compiled_templates')
    compiled_files = path.path(compiled_templates).files()
    if len(compiled_files) <= 1:
        app.jinja_env.compile_templates(compiled_templates, zip=None, py_compile=True)

    if not app.config.get('TEMPLATE_DEBUG', False):
        app.jinja_env.loader = ModuleLoader(compiled_templates)

    configure_logging(app)

    try:
        from flaskext.exceptional import Exceptional
    except ImportError:
        pass
    exceptional_key = app.config.get('EXCEPTIONAL_API_KEY', '')
    if exceptional_key:
        exceptional = Exceptional(app)
        app._exceptional = exceptional

    app.wsgi_app = FixGunicorn(app.wsgi_app)

    return app

app = get_app()
cache = Cache(app)
