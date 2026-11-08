from datetime import datetime

import pytest

from app import db
from app.models import Assignment, Subject, User
from app.services import dashboard_service


def _utilisateur(nom, email, role):
    user = User(nom=nom, email=email, role=role)
    user.set_password("Test1234")
    db.session.add(user)
    return user


@pytest.fixture
def donnees(app):
    """Un admin, un enseignant, Ali (affecté, publié) et Sana (sans sujet)."""
    _utilisateur("Admin Test", "admin@test.tn", "admin")
    prof = _utilisateur("Mme Test", "prof@test.tn", "enseignant")
    ali = _utilisateur("Ali Test", "ali@test.tn", "etudiant")
    _utilisateur("Sana Test", "sana@test.tn", "etudiant")
    db.session.flush()

    sujet = Subject(titre="Sujet de demonstration", resume="Resume", niveau="L2",
                    statut="valide", encadrant_id=prof.id)
    db.session.add(sujet)
    db.session.flush()
    db.session.add(Assignment(etudiant_id=ali.id, sujet_id=sujet.id, publie=True))
    db.session.commit()


def _connecte(app, email):
    client = app.test_client()
    client.post("/login", data={"email": email, "mot_de_passe": "Test1234"})
    return client


def test_export_csv_contient_affectations_et_livrables(app, donnees):
    reponse = _connecte(app, "admin@test.tn").get("/admin/export.csv")
    assert reponse.status_code == 200
    assert "text/csv" in reponse.content_type

    lignes = reponse.data.decode("utf-8-sig").splitlines()
    assert lignes[0].startswith("Étudiant;E-mail;Sujet")

    ligne_ali = next(l for l in lignes if "ali@test.tn" in l)
    assert "Sujet de demonstration" in ligne_ali
    assert "Mme Test" in ligne_ali
    assert "Non déposé" in ligne_ali

    ligne_sana = next(l for l in lignes if "sana@test.tn" in l)
    assert "Sujet de demonstration" not in ligne_sana


def test_export_csv_neutralise_les_formules(app, donnees):
    _utilisateur("=2+2", "pirate@test.tn", "etudiant")
    db.session.commit()

    texte = _connecte(app, "admin@test.tn").get("/admin/export.csv").data.decode("utf-8-sig")
    assert "'=2+2" in texte


def test_export_et_tableau_de_bord_reserves_a_l_admin(app, donnees):
    etudiant = _connecte(app, "ali@test.tn")
    assert etudiant.get("/admin/export.csv").status_code == 403
    assert etudiant.get("/admin/").status_code == 403


def test_statistiques(app, donnees):
    stats = dashboard_service.statistiques()
    assert stats["sujets_valides"] == 1
    assert stats["etudiants"] == 2
    assert stats["affectes"] == 1
    assert stats["livrables_attendus"] == 3
    assert stats["livrables_deposes"] == 0


def test_retards_listes_apres_la_date_limite(app, donnees):
    app.config["DATE_LIMITE_DEPOT"] = datetime(2020, 1, 1)
    page = _connecte(app, "admin@test.tn").get("/admin/").get_data(as_text=True)
    assert "Ali Test" in page


def test_pas_de_retard_avant_la_date_limite(app, donnees):
    page = _connecte(app, "admin@test.tn").get("/admin/").get_data(as_text=True)
    assert "Ali Test" not in page