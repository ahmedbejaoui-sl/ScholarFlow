import pytest

from app import db
from app.models import Assignment, Subject, User


def _utilisateur(nom, email, role):
    user = User(nom=nom, email=email, role=role)
    user.set_password("Test1234")
    db.session.add(user)
    return user


@pytest.fixture
def donnees(app):
    """Une enseignante, un étudiant, un sujet validé et une affectation non publiée."""
    prof = _utilisateur("Mme Test", "prof@test.tn", "enseignant")
    autre_prof = _utilisateur("M. Autre", "autre@test.tn", "enseignant")
    etudiant = _utilisateur("Ali Test", "ali@test.tn", "etudiant")
    db.session.flush()

    sujet = Subject(titre="Sujet de demonstration", resume="Un resume", niveau="L2",
                    statut="valide", encadrant_id=prof.id)
    db.session.add(sujet)
    db.session.flush()

    affectation = Assignment(etudiant_id=etudiant.id, sujet_id=sujet.id, publie=False)
    db.session.add(affectation)
    db.session.commit()
    return {"affectation": affectation}


def _connexion(client, email):
    return client.post("/login", data={"email": email, "mot_de_passe": "Test1234"})


def _publier(donnees):
    donnees["affectation"].publie = True
    db.session.commit()


def test_etudiant_ne_voit_rien_avant_publication(client, donnees):
    _connexion(client, "ali@test.tn")
    page = client.get("/voeux/resultat").get_data(as_text=True)
    assert "pas encore publiés" in page
    assert "Sujet de demonstration" not in page


def test_etudiant_voit_son_sujet_et_son_encadrant_apres_publication(client, donnees):
    _publier(donnees)
    _connexion(client, "ali@test.tn")
    page = client.get("/voeux/resultat").get_data(as_text=True)
    assert "Sujet de demonstration" in page
    assert "prof@test.tn" in page


def test_enseignant_ne_voit_rien_avant_publication(client, donnees):
    _connexion(client, "prof@test.tn")
    page = client.get("/subjects/mes-etudiants").get_data(as_text=True)
    assert "Ali Test" not in page


def test_enseignant_voit_ses_etudiants_apres_publication(client, donnees):
    _publier(donnees)
    _connexion(client, "prof@test.tn")
    page = client.get("/subjects/mes-etudiants").get_data(as_text=True)
    assert "Ali Test" in page


def test_enseignant_ne_voit_pas_les_etudiants_d_un_autre(client, donnees):
    _publier(donnees)
    _connexion(client, "autre@test.tn")
    page = client.get("/subjects/mes-etudiants").get_data(as_text=True)
    assert "Ali Test" not in page


def test_etudiant_ne_peut_pas_ouvrir_la_page_enseignant(client, donnees):
    _connexion(client, "ali@test.tn")
    assert client.get("/subjects/mes-etudiants").status_code == 403