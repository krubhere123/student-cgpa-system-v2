from pathlib import Path
from flask import Flask


def create_app():
    root_dir = Path(__file__).resolve().parent.parent
    template_dir = root_dir / "templates"
    static_dir = root_dir / "static"

    app = Flask(
        __name__,
        template_folder=str(template_dir),
        static_folder=str(static_dir),
    )
    app.config["SECRET_KEY"] = "student-cgpa-dev-secret"

    from .routes import register_routes
    register_routes(app)

    return app


app = create_app()
