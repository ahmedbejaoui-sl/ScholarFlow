from app.models import Assignment, Deliverable, Subject, User, WishValidation
from app.services.deliverable_service import TYPES, depot_ouvert


def etudiants_en_retard():
    """Étudiants affectés (résultat publié) à qui il manque un livrable après la date limite."""
    if depot_ouvert():
        return []

    deposes = {}
    for livrable in Deliverable.query.all():
        deposes.setdefault(livrable.etudiant_id, set()).add(livrable.type)

    retards = []
    for affectation in Assignment.query.filter_by(publie=True).all():
        recus = deposes.get(affectation.etudiant_id, set())
        manquants = [libelle for code, libelle in TYPES.items() if code not in recus]
        if manquants:
            retards.append({"etudiant": affectation.etudiant,
                            "sujet": affectation.sujet,
                            "manquants": manquants})
    retards.sort(key=lambda r: r["etudiant"].nom)
    return retards


def statistiques():
    """Chiffres clés du tableau de bord (F17)."""
    affectes_publies = Assignment.query.filter_by(publie=True).count()
    return {
        "sujets_valides": Subject.query.filter_by(statut="valide").count(),
        "sujets_en_attente": Subject.query.filter_by(statut="en_attente").count(),
        "etudiants": User.query.filter_by(role="etudiant").count(),
        "listes_validees": WishValidation.query.count(),
        "affectes": Assignment.query.count(),
        "affectes_publies": affectes_publies,
        "resultats_publies": affectes_publies > 0,
        "livrables_deposes": Deliverable.query.count(),
        "livrables_valides": Deliverable.query.filter_by(valide=True).count(),
        "livrables_attendus": affectes_publies * len(TYPES),
        "depot_ouvert": depot_ouvert(),
        "retards": etudiants_en_retard(),
    }