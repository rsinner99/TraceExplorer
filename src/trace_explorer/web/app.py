from flask import Flask

from .web import bp

def create_app(*args, **kwargs):
    app = Flask(__name__, instance_relative_config=True)
    app.debug = True
    app.config.from_object('trace_explorer.web.settings')
    app.register_blueprint(bp)
    return app

app = create_app()

if __name__ == '__main__':
    app.run(port=8080)