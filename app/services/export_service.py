import csv
import io

from app.models import Assignment, Deliverable, User
from app.services.deliverable_service import TYPES

ENTETE = (["Étudiant", "E-mail", "Sujet", "Encadrant", "Résultat publié"]
          + list(TYPES.values()))


def _securiser(valeur):
    """Neutralise les cellules qu'Excel interpréterait comme une formule (=, +, -, @)."""
    texte = "" if valeur is None else str(valeur)
    if texte and texte[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + texte
    return texte


def _statut(livrable):
    if livrable is None:
        return "Non déposé"
    return "Validé" if livrable.valide else "Déposé"


def generer_csv():
    """État récapitulatif des affectations et des livrables, une ligne par étudiant (F16)."""
    affectations = {a.etudiant_id: a for a in Assignment.query.all()}
    livrables = {(l.etudiant_id, l.type): l for l in Deliverable.query.all()}

    sortie = io.StringIO()
    ecrivain = csv.writer(sortie, delimiter=";")
    ecrivain.writerow(ENTETE)

    for etudiant in User.query.filter_by(role="etudiant").order_by(User.nom):
        a = affectations.get(etudiant.id)
        ligne = [
            etudiant.nom,
            etudiant.email,
            a.sujet.titre if a else "",
            a.sujet.encadrant.nom if a else "",
            ("Oui" if a.publie else "Non") if a else "",
        ]
        ligne += [_statut(livrables.get((etudiant.id, code))) for code in TYPES]
        ecrivain.writerow([_securiser(c) for c in ligne])

    return sortie.getvalue()