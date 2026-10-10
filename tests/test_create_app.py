from flask import Flask

from student_cgpa import create_app


def test_create_app():
    app = create_app()
    assert isinstance(app, Flask)
