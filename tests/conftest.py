import pytest
from flask import g

from app import create_app, db
from config import TestConfig


@pytest.fixture
def app(tmp_path):
    application = create_app(TestConfig)
    application.config["UPLOAD_FOLDER"] = str(tmp_path)

    @application.before_request
    def oublier_utilisateur_precedent():
        # Les tests gardent un contexte d'application ouvert : sans cette ligne,
        # l'utilisateur de la requête précédente resterait en mémoire.
        g.pop("_login_user", None)

    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()