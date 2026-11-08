import pytest

from app import db
from app.models import User


def _utilisateur(nom, email, role):
    user = User(nom=nom, email=email, role=role)
    user.set_password("Test1234")
    db.session.add(user)
    return user


@pytest.fixture
def comptes(app):
    _utilisateur("Ali Test", "ali@test.tn", "etudiant")
    _utilisateur("Mme Test", "prof@test.tn", "enseignant")
    _utilisateur("Admin Test", "admin@test.tn", "admin")
    db.session.commit()


def _connexion(client, email="ali@test.tn", mot_de_passe="Test1234", suite="/login"):
    return client.post(suite, data={"email": email, "mot_de_passe": mot_de_passe})


def test_connexion_reussie(client, comptes):
    reponse = _connexion(client)
    assert reponse.status_code == 302
    page = client.get("/").get_data(as_text=True)
    assert "Se déconnecter" in page
    assert "Ali Test" in page


def test_mauvais_mot_de_passe(client, comptes):
    page = _connexion(client, mot_de_passe="faux").get_data(as_text=True)
    assert "incorrect" in page
    assert client.get("/subjects/").status_code == 302  # toujours non connecté


def test_email_inconnu(client, comptes):
    page = _connexion(client, email="inconnu@test.tn").get_data(as_text=True)
    assert "incorrect" in page


def test_champs_vides(client, comptes):
    page = client.post("/login", data={"email": "", "mot_de_passe": ""}).get_data(as_text=True)
    assert "obligatoire" in page


def test_page_protegee_redirige_vers_la_connexion(client, comptes):
    reponse = client.get("/subjects/")
    assert reponse.status_code == 302
    assert "/login" in reponse.headers["Location"]


def test_deconnexion(client, comptes):
    _connexion(client)
    page = client.get("/logout", follow_redirects=True).get_data(as_text=True)
    assert "déconnecté" in page
    assert client.get("/subjects/").status_code == 302


def test_mot_de_passe_stocke_hache(app, comptes):
    user = User.query.filter_by(email="ali@test.tn").first()
    assert user.password_hash != "Test1234"
    assert user.check_password("Test1234")
    assert not user.check_password("autre")


def test_acces_refuse_selon_le_role(app, comptes):
    etudiant = app.test_client()
    _connexion(etudiant, "ali@test.tn")
    assert etudiant.get("/admin/sujets").status_code == 403
    assert etudiant.get("/subjects/nouveau").status_code == 403

    enseignant = app.test_client()
    _connexion(enseignant, "prof@test.tn")
    assert enseignant.get("/voeux/").status_code == 403
    assert enseignant.get("/admin/").status_code == 403


def test_redirection_vers_un_site_externe_ignoree(client, comptes):
    reponse = _connexion(client, suite="/login?next=//evil.com")
    assert reponse.status_code == 302
    assert "evil.com" not in reponse.headers["Location"]


def test_redirection_interne_acceptee(client, comptes):
    reponse = _connexion(client, suite="/login?next=/subjects/")
    assert reponse.headers["Location"].endswith("/subjects/")