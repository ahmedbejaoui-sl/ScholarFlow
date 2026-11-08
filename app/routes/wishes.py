from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user
from app.services import assignment_service

from app.decorators import role_required
from app.services import wish_service as service
from app.services.wish_service import VoeuError

wishes_bp = Blueprint("wishes", __name__, url_prefix="/voeux")


def _executer(action, message_ok, *args):
    """Lance une action du service et affiche le résultat à l'étudiant."""
    try:
        action(current_user, *args)
        flash(message_ok, "success")
    except VoeuError as erreur:
        flash(str(erreur), "danger")
    return redirect(url_for("wishes.mes_voeux"))


@wishes_bp.route("/")
@role_required("etudiant")
def mes_voeux():
    """Liste de vœux de l'étudiant (F4, F5)."""
    return render_template(
        "wishes/mes_voeux.html",
        voeux=service.liste_voeux(current_user),
        valide=service.est_valide(current_user),
        ouverts=service.voeux_ouverts(),
        cloture=current_app.config["DATE_CLOTURE_VOEUX"],
        max_voeux=current_app.config["MAX_VOEUX"],
    )


@wishes_bp.route("/ajouter/<int:sujet_id>", methods=["POST"])
@role_required("etudiant")
def ajouter(sujet_id):
    return _executer(service.ajouter, "Sujet ajouté à vos vœux.", sujet_id)


@wishes_bp.route("/<int:voeu_id>/retirer", methods=["POST"])
@role_required("etudiant")
def retirer(voeu_id):
    return _executer(service.retirer, "Sujet retiré de vos vœux.", voeu_id)


@wishes_bp.route("/<int:voeu_id>/deplacer", methods=["POST"])
@role_required("etudiant")
def deplacer(voeu_id):
    sens = request.form.get("sens")
    if sens not in ("haut", "bas"):
        flash("Déplacement inconnu.", "danger")
        return redirect(url_for("wishes.mes_voeux"))
    try:
        service.deplacer(current_user, voeu_id, sens)
    except VoeuError as erreur:
        flash(str(erreur), "danger")
    return redirect(url_for("wishes.mes_voeux"))


@wishes_bp.route("/valider", methods=["POST"])
@role_required("etudiant")
def valider():
    return _executer(service.valider, "Votre liste de vœux est validée.")


@wishes_bp.route("/rouvrir", methods=["POST"])
@role_required("etudiant")
def rouvrir():
    return _executer(service.rouvrir, "Votre liste est de nouveau modifiable.")


@wishes_bp.route("/annuler", methods=["POST"])
@role_required("etudiant")
def annuler():
    return _executer(service.annuler, "Votre fiche de vœux a été annulée.")
@wishes_bp.route("/resultat")
@role_required("etudiant")
def resultat():
    """Résultat de l'affectation et coordonnées de l'encadrant (F6)."""
    return render_template(
        "wishes/resultat.html",
        affectation=assignment_service.affectation_publiee_de(current_user),
        publie=assignment_service.resultats_publies(),
    )