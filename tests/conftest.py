import pytest
from app import create_app
from app.database_models import db

@pytest.fixture(scope='module')
def test_app():
    """
    Creates a test instance of the Flask app.
    Configured for testing with an in-memory SQLite database.
    """
    app = create_app()
    app.config.update({
        "TESTING": True,
        # Use an in-memory SQLite database for tests
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,  # Disable CSRF for testing forms if you add them later
        "DEBUG": False,
    })

    with app.app_context():
        db.create_all()
        yield app  # The test app is now available to the tests
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='module')
def test_client(test_app):
    """
    Creates a test client for the Flask app.
    This client can be used to send requests to the app's endpoints.
    """
    return test_app.test_client() 