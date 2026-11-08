import io
import os
import zipfile
from datetime import datetime

import pytest

from app import db
from app.models import Assignment, Deliverable, Subject, User


def _utilisateur(nom, email, role):
    user = User(nom=nom, email=email, role=role)
    user.set_password("Test1234")
    db.session.add(user)
    return user


@pytest.fixture
def donnees(app):
    """Un encadrant, un autre enseignant, un étudiant affecté (publié), un étudiant sans sujet."""
    prof = _utilisateur("Mme Test", "prof@test.tn", "enseignant")
    _utilisateur("M. Autre", "autre@test.tn", "enseignant")
    ali = _utilisateur("Ali Test", "ali@test.tn", "etudiant")
    _utilisateur("Sana Test", "sana@test.tn", "etudiant")
    db.session.flush()

    sujet = Subject(titre="Sujet", resume="Resume", niveau="L2",
                    statut="valide", encadrant_id=prof.id)
    db.session.add(sujet)
    db.session.flush()
    db.session.add(Assignment(etudiant_id=ali.id, sujet_id=sujet.id, publie=True))
    db.session.commit()


def _connecte(app, email):
    client = app.test_client()
    client.post("/login", data={"email": email, "mot_de_passe": "Test1234"})
    return client


def _deposer(client, contenu=b"%PDF-1.4 test", nom="rapport.pdf", type_="cahier"):
    return client.post(
        "/livrables/",
        data={"type_livrable": type_, "fichier": (io.BytesIO(contenu), nom)},
        content_type="multipart/form-data",
        follow_redirects=True,
    )


def test_depot_d_un_pdf_valide(app, donnees):
    ali = _connecte(app, "ali@test.tn")
    _deposer(ali)
    assert Deliverable.query.count() == 1
    assert len(os.listdir(app.config["UPLOAD_FOLDER"])) == 1


def test_extension_interdite_refusee(app, donnees):
    ali = _connecte(app, "ali@test.tn")
    _deposer(ali, contenu=b"MZ binaire", nom="virus.exe")
    assert Deliverable.query.count() == 0


def test_faux_pdf_refuse(app, donnees):
    ali = _connecte(app, "ali@test.tn")
    _deposer(ali, contenu=b"ceci n'est pas un pdf", nom="faux.pdf")
    assert Deliverable.query.count() == 0


def test_depot_refuse_apres_la_date_limite(app, donnees):
    app.config["DATE_LIMITE_DEPOT"] = datetime(2020, 1, 1)
    ali = _connecte(app, "ali@test.tn")
    _deposer(ali)
    assert Deliverable.query.count() == 0


def test_depot_refuse_sans_affectation_publiee(app, donnees):
    sana = _connecte(app, "sana@test.tn")
    _deposer(sana)
    assert Deliverable.query.count() == 0


def test_nouveau_depot_remplace_l_ancien(app, donnees):
    ali = _connecte(app, "ali@test.tn")
    _deposer(ali, contenu=b"%PDF-1 version a")
    _deposer(ali, contenu=b"%PDF-1 version b")
    assert Deliverable.query.count() == 1
    assert len(os.listdir(app.config["UPLOAD_FOLDER"])) == 1


def test_livrable_valide_ne_peut_plus_etre_remplace(app, donnees):
    ali = _connecte(app, "ali@test.tn")
    _deposer(ali)
    livrable = Deliverable.query.first()
    livrable.valide = True
    db.session.commit()
    nom_avant = livrable.fichier

    _deposer(ali, contenu=b"%PDF-1 autre version")
    assert Deliverable.query.first().fichier == nom_avant


def test_enseignant_valide_le_livrable_de_son_etudiant(app, donnees):
    _deposer(_connecte(app, "ali@test.tn"))
    livrable_id = Deliverable.query.first().id

    prof = _connecte(app, "prof@test.tn")
    prof.post(f"/livrables/{livrable_id}/valider")
    assert Deliverable.query.first().valide is True


def test_un_autre_enseignant_ne_peut_pas_valider(app, donnees):
    _deposer(_connecte(app, "ali@test.tn"))
    livrable_id = Deliverable.query.first().id

    autre = _connecte(app, "autre@test.tn")
    autre.post(f"/livrables/{livrable_id}/valider")
    assert Deliverable.query.first().valide is False


def test_l_encadrant_peut_telecharger_le_fichier(app, donnees):
    _deposer(_connecte(app, "ali@test.tn"))
    livrable_id = Deliverable.query.first().id

    reponse = _connecte(app, "prof@test.tn").get(f"/livrables/{livrable_id}/telecharger")
    assert reponse.status_code == 200
    assert reponse.data.startswith(b"%PDF")


def test_un_autre_etudiant_ne_peut_pas_telecharger(app, donnees):
    _deposer(_connecte(app, "ali@test.tn"))
    livrable_id = Deliverable.query.first().id

    reponse = _connecte(app, "sana@test.tn").get(f"/livrables/{livrable_id}/telecharger")
    assert reponse.status_code == 403


def test_archive_zip_de_l_encadrant(app, donnees):
    _deposer(_connecte(app, "ali@test.tn"))

    reponse = _connecte(app, "prof@test.tn").get("/livrables/suivi/archive")
    assert reponse.status_code == 200
    with zipfile.ZipFile(io.BytesIO(reponse.data)) as archive:
        assert len(archive.namelist()) == 1