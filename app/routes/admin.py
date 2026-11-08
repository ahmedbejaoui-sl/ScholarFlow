from flask import Blueprint, render_template, redirect, url_for, flash, request

from app import db
from app.decorators import role_required
from app.models import Subject
from app.services import assignment_service as service
from app.services.assignment_service import AffectationError
from app.services.wish_service import voeux_ouverts

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Décision choisie -> (nouveau statut, commentaire obligatoire ?)
DECISIONS = {
    "valider": ("valide", False),
    "modification": ("modification", True),
    "refuser": ("refuse", True),
}


@admin_bp.route("/sujets")
@role_required("admin")
def validation_sujets():
    """Liste des sujets en attente de décision (F13)."""
    sujets = (Subject.query
              .filter_by(statut="en_attente")
              .order_by(Subject.id)
              .all())
    return render_template("admin/validation_sujets.html", sujets=sujets)


@admin_bp.route("/sujets/<int:sujet_id>/decision", methods=["POST"])
@role_required("admin")
def decision_sujet(sujet_id):
    """Enregistre la décision de la commission sur un sujet (F13)."""
    sujet = db.get_or_404(Subject, sujet_id)

    if sujet.statut != "en_attente":
        flash("Ce sujet a déjà fait l'objet d'une décision.", "warning")
        return redirect(url_for("admin.validation_sujets"))

    choix = request.form.get("decision")
    commentaire = request.form.get("commentaire", "").strip()

    if choix not in DECISIONS:
        flash("Décision inconnue.", "danger")
        return redirect(url_for("admin.validation_sujets"))

    nouveau_statut, commentaire_obligatoire = DECISIONS[choix]
    if commentaire_obligatoire and not commentaire:
        flash("Un commentaire est obligatoire pour demander une modification ou refuser un sujet.",
              "danger")
        return redirect(url_for("admin.validation_sujets"))

    sujet.statut = nouveau_statut
    sujet.commentaire_admin = commentaire or None
    db.session.commit()

    messages = {
        "valide": "Sujet validé : il est maintenant visible dans le catalogue.",
        "modification": "Modification demandée à l'enseignant.",
        "refuse": "Sujet refusé.",
    }
    flash(messages[nouveau_statut], "success")
    return redirect(url_for("admin.validation_sujets"))
# ---------- Affectation des sujets (F14, F15) ----------

def _retour_affectations():
    return redirect(url_for("admin.affectations"))


@admin_bp.route("/affectations")
@role_required("admin")
def affectations():
    """Tableau de pilotage des affectations."""
    return render_template(
        "admin/affectations.html",
        lignes=service.lignes_affectations(),
        sans_sujet=service.etudiants_sans_affectation(),
        libres=service.sujets_libres(),
        publie=service.resultats_publies(),
        voeux_ouverts=voeux_ouverts(),
    )


@admin_bp.route("/affectations/lancer", methods=["POST"])
@role_required("admin")
def lancer_affectation():
    try:
        affectes, participants = service.lancer()
        flash(f"Affectation terminée : {affectes} étudiant(s) affecté(s) sur {participants} "
              f"liste(s) de vœux validée(s).", "success")
    except AffectationError as erreur:
        flash(str(erreur), "danger")
    return _retour_affectations()


@admin_bp.route("/affectations/manuel", methods=["POST"])
@role_required("admin")
def affectation_manuelle():
    etudiant_id = request.form.get("etudiant_id", type=int)
    sujet_id = request.form.get("sujet_id", type=int)
    try:
        service.affecter_manuellement(etudiant_id, sujet_id)
        flash("Affectation manuelle enregistrée.", "success")
    except AffectationError as erreur:
        flash(str(erreur), "danger")
    return _retour_affectations()


@admin_bp.route("/affectations/<int:affectation_id>/retirer", methods=["POST"])
@role_required("admin")
def retirer_affectation(affectation_id):
    try:
        service.retirer_affectation(affectation_id)
        flash("Affectation retirée.", "info")
    except AffectationError as erreur:
        flash(str(erreur), "danger")
    return _retour_affectations()


@admin_bp.route("/affectations/publier", methods=["POST"])
@role_required("admin")
def publier_affectations():
    try:
        service.publier()
        flash("Résultats publiés : les étudiants peuvent consulter leur affectation.", "success")
    except AffectationError as erreur:
        flash(str(erreur), "danger")
    return _retour_affectations()