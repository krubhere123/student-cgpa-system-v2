from student_cgpa import app


def test_login_and_dashboard():
    client = app.test_client()

    response = client.post(
        "/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Dashboard" in response.data or b"Admin Dashboard" in response.data

    response = client.get("/dashboard")
    assert response.status_code == 200

    response = client.get("/logout")
    assert response.status_code == 302


def test_student_login():
    client = app.test_client()
    response = client.post(
        "/login",
        data={"username": "student", "password": "student123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Ada Johnson" in response.data
