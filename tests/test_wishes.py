from datetime import datetime

import pytest

from app import db
from app.models import Subject, User, Wish
from app.services import wish_service as service
from app.services.wish_service import VoeuError


def _utilisateur(nom, email, role):
    user = User(nom=nom, email=email, role=role)
    user.set_password("Test1234")
    db.session.add(user)
    return user


@pytest.fixture
def donnees(app):
    """Deux étudiants, un enseignant, 6 sujets validés et 1 sujet en attente."""
    prof = _utilisateur("Mme Test", "prof@test.tn", "enseignant")
    ali = _utilisateur("Ali Test", "ali@test.tn", "etudiant")
    sana = _utilisateur("Sana Test", "sana@test.tn", "etudiant")
    db.session.flush()

    sujets = []
    for i in range(6):
        s = Subject(titre=f"Sujet {i}", resume="Resume", niveau="L2",
                    statut="valide", encadrant_id=prof.id)
        db.session.add(s)
        sujets.append(s)
    en_attente = Subject(titre="Sujet en attente", resume="Resume", niveau="L2",
                         statut="en_attente", encadrant_id=prof.id)
    db.session.add(en_attente)
    db.session.commit()
    return {"ali": ali, "sana": sana, "sujets": sujets, "en_attente": en_attente}


def _ordre(etudiant):
    """Liste des (rang, id du sujet) de l'étudiant."""
    return [(v.priorite, v.sujet_id) for v in service.liste_voeux(etudiant)]


def test_ajout_dans_l_ordre(donnees):
    ali, s = donnees["ali"], donnees["sujets"]
    service.ajouter(ali, s[0].id)
    service.ajouter(ali, s[1].id)
    assert _ordre(ali) == [(1, s[0].id), (2, s[1].id)]


def test_doublon_refuse(donnees):
    ali, s = donnees["ali"], donnees["sujets"]
    service.ajouter(ali, s[0].id)
    with pytest.raises(VoeuError, match="déjà"):
        service.ajouter(ali, s[0].id)
    assert len(service.liste_voeux(ali)) == 1


def test_sujet_non_valide_refuse(donnees):
    with pytest.raises(VoeuError, match="pas disponible"):
        service.ajouter(donnees["ali"], donnees["en_attente"].id)


def test_maximum_de_voeux(donnees):
    ali, s = donnees["ali"], donnees["sujets"]
    for sujet in s[:5]:
        service.ajouter(ali, sujet.id)
    with pytest.raises(VoeuError, match="plus de 5"):
        service.ajouter(ali, s[5].id)


def test_retrait_renumerote_les_rangs(donnees):
    ali, s = donnees["ali"], donnees["sujets"]
    for sujet in s[:3]:
        service.ajouter(ali, sujet.id)
    milieu = service.liste_voeux(ali)[1]
    service.retirer(ali, milieu.id)
    assert _ordre(ali) == [(1, s[0].id), (2, s[2].id)]


def test_deplacer_echange_les_rangs(donnees):
    ali, s = donnees["ali"], donnees["sujets"]
    service.ajouter(ali, s[0].id)
    service.ajouter(ali, s[1].id)
    second = service.liste_voeux(ali)[1]
    service.deplacer(ali, second.id, "haut")
    assert _ordre(ali) == [(1, s[1].id), (2, s[0].id)]


def test_liste_validee_est_verrouillee(donnees):
    ali, s = donnees["ali"], donnees["sujets"]
    service.ajouter(ali, s[0].id)
    service.valider(ali)
    assert service.est_valide(ali)
    with pytest.raises(VoeuError, match="validée"):
        service.ajouter(ali, s[1].id)


def test_validation_d_une_liste_vide_refusee(donnees):
    with pytest.raises(VoeuError, match="au moins"):
        service.valider(donnees["ali"])


def test_rouvrir_permet_de_modifier(donnees):
    ali, s = donnees["ali"], donnees["sujets"]
    service.ajouter(ali, s[0].id)
    service.valider(ali)
    service.rouvrir(ali)
    assert not service.est_valide(ali)
    service.ajouter(ali, s[1].id)
    assert len(service.liste_voeux(ali)) == 2


def test_aucune_modification_apres_la_cloture(app, donnees):
    ali, s = donnees["ali"], donnees["sujets"]
    service.ajouter(ali, s[0].id)
    app.config["DATE_CLOTURE_VOEUX"] = datetime(2020, 1, 1)
    with pytest.raises(VoeuError, match="clôture"):
        service.ajouter(ali, s[1].id)
    with pytest.raises(VoeuError, match="clôture"):
        service.annuler(ali)


def test_annuler_supprime_toute_la_fiche(donnees):
    ali, s = donnees["ali"], donnees["sujets"]
    service.ajouter(ali, s[0].id)
    service.ajouter(ali, s[1].id)
    service.valider(ali)
    service.annuler(ali)
    assert service.liste_voeux(ali) == []
    assert not service.est_valide(ali)


def test_un_etudiant_ne_touche_pas_aux_voeux_d_un_autre(donnees):
    ali, sana, s = donnees["ali"], donnees["sana"], donnees["sujets"]
    service.ajouter(sana, s[0].id)
    voeu_de_sana = service.liste_voeux(sana)[0]
    with pytest.raises(VoeuError, match="introuvable"):
        service.retirer(ali, voeu_de_sana.id)
    assert len(service.liste_voeux(sana)) == 1


def test_ajout_par_la_page_web(app, donnees):
    client = app.test_client()
    client.post("/login", data={"email": "ali@test.tn", "mot_de_passe": "Test1234"})
    client.post(f"/voeux/ajouter/{donnees['sujets'][0].id}")
    assert Wish.query.count() == 1


def test_un_enseignant_ne_peut_pas_ajouter_de_voeu(app, donnees):
    client = app.test_client()
    client.post("/login", data={"email": "prof@test.tn", "mot_de_passe": "Test1234"})
    reponse = client.post(f"/voeux/ajouter/{donnees['sujets'][0].id}")
    assert reponse.status_code == 403
    assert Wish.query.count() == 0
    