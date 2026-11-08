from app import db
from app.models import Assignment, Subject, User, Wish, WishValidation


class AffectationError(Exception):
    """Règle de gestion non respectée. Le message est affiché à l'administrateur."""


# ---------- Algorithme (fonction pure, sans base de données) ----------

def calculer_affectations(voeux_par_etudiant, ordre):
    """Calcule les affectations par ordre de priorité des vœux.

    voeux_par_etudiant : {etudiant_id: [sujet_id, ...]} du 1er au dernier choix
    ordre              : liste des etudiant_id par ordre de départage (en cas de conflit,
                         le premier de la liste gagne)
    Retourne           : {etudiant_id: sujet_id}
    """
    affectations = {}
    sujets_pris = set()
    nb_tours = max((len(v) for v in voeux_par_etudiant.values()), default=0)

    for rang in range(nb_tours):          # tour 1 = tous les premiers choix, etc.
        for etudiant_id in ordre:
            if etudiant_id in affectations:
                continue
            liste = voeux_par_etudiant.get(etudiant_id, [])
            if rang >= len(liste):
                continue
            sujet_id = liste[rang]
            if sujet_id not in sujets_pris:
                affectations[etudiant_id] = sujet_id
                sujets_pris.add(sujet_id)
    return affectations


# ---------- Consultation ----------

def resultats_publies():
    return Assignment.query.filter_by(publie=True).first() is not None


def lignes_affectations():
    """Affectations avec le rang du vœu obtenu (None si affectation manuelle)."""
    rangs = {(w.etudiant_id, w.sujet_id): w.priorite for w in Wish.query.all()}
    affectations = (Assignment.query
                    .join(User, Assignment.etudiant_id == User.id)
                    .order_by(User.nom).all())
    return [{"affectation": a, "rang": rangs.get((a.etudiant_id, a.sujet_id))}
            for a in affectations]


def etudiants_sans_affectation():
    pris = [a.etudiant_id for a in Assignment.query.all()]
    return (User.query.filter_by(role="etudiant")
            .filter(User.id.notin_(pris)).order_by(User.nom).all())


def sujets_libres():
    pris = [a.sujet_id for a in Assignment.query.all()]
    return (Subject.query.filter_by(statut="valide")
            .filter(Subject.id.notin_(pris)).order_by(Subject.titre).all())


# ---------- Actions ----------

def _verifier_non_publie():
    if resultats_publies():
        raise AffectationError("Les résultats sont déjà publiés : ils ne peuvent plus être modifiés.")


def lancer():
    """Calcule et enregistre les affectations. Remplace un calcul précédent non publié."""
    _verifier_non_publie()
    Assignment.query.delete()

    validations = (WishValidation.query
                   .order_by(WishValidation.date_validation, WishValidation.id).all())
    ordre = [v.etudiant_id for v in validations]
    sujets_valides = {s.id for s in Subject.query.filter_by(statut="valide")}

    voeux = {}
    voeux_en_base = (Wish.query.filter(Wish.etudiant_id.in_(ordre))
                     .order_by(Wish.etudiant_id, Wish.priorite).all())
    for w in voeux_en_base:
        if w.sujet_id in sujets_valides:
            voeux.setdefault(w.etudiant_id, []).append(w.sujet_id)

    resultat = calculer_affectations(voeux, ordre)
    for etudiant_id, sujet_id in resultat.items():
        db.session.add(Assignment(etudiant_id=etudiant_id, sujet_id=sujet_id))
    db.session.commit()
    return len(resultat), len(ordre)


def affecter_manuellement(etudiant_id, sujet_id):
    """Ajustement manuel en cas de conflit ou d'étudiant sans affectation."""
    _verifier_non_publie()

    etudiant = db.session.get(User, etudiant_id)
    sujet = db.session.get(Subject, sujet_id)
    if etudiant is None or etudiant.role != "etudiant":
        raise AffectationError("Étudiant introuvable.")
    if sujet is None or sujet.statut != "valide":
        raise AffectationError("Seuls les sujets validés peuvent être attribués.")
    if Assignment.query.filter_by(etudiant_id=etudiant.id).first():
        raise AffectationError("Cet étudiant a déjà un sujet.")
    if Assignment.query.filter_by(sujet_id=sujet.id).first():
        raise AffectationError("Ce sujet est déjà attribué.")

    db.session.add(Assignment(etudiant_id=etudiant.id, sujet_id=sujet.id))
    db.session.commit()


def retirer_affectation(affectation_id):
    _verifier_non_publie()
    affectation = db.session.get(Assignment, affectation_id)
    if affectation is None:
        raise AffectationError("Affectation introuvable.")
    db.session.delete(affectation)
    db.session.commit()


def publier():
    """Rend les affectations visibles des étudiants et des encadrants (F15)."""
    _verifier_non_publie()
    if Assignment.query.count() == 0:
        raise AffectationError("Aucune affectation à publier. Lancez d'abord l'affectation.")
    Assignment.query.update({"publie": True})
    db.session.commit()
# ---------- Consultation des résultats publiés (F6, F10) ----------

def affectation_publiee_de(etudiant):
    """Affectation publiée de l'étudiant, ou None."""
    return Assignment.query.filter_by(etudiant_id=etudiant.id, publie=True).first()


def affectations_publiees_de(encadrant):
    """Étudiants affectés aux sujets de cet encadrant (résultats publiés seulement)."""
    return (Assignment.query
            .join(Subject, Assignment.sujet_id == Subject.id)
            .join(User, Assignment.etudiant_id == User.id)
            .filter(Subject.encadrant_id == encadrant.id,
                    Assignment.publie.is_(True))
            .order_by(Subject.titre, User.nom)
            .all())