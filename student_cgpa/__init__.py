from flask import Flask


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "student-cgpa-dev-secret"

    from .routes import register_routes
    register_routes(app)

    return app


app = create_app()
