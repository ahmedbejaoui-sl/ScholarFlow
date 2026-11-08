from flask import (Blueprint, render_template, redirect, url_for, flash, abort,
                   send_file, send_from_directory, current_app)
from flask_login import current_user, login_required

from app import db
from app.decorators import role_required
from app.forms import DeliverableForm
from app.models import Deliverable
from app.services import deliverable_service as service
from app.services.deliverable_service import DepotError

deliverables_bp = Blueprint("deliverables", __name__, url_prefix="/livrables")


@deliverables_bp.route("/", methods=["GET", "POST"])
@role_required("etudiant")
def mes_livrables():
    """Dépôt et suivi des livrables de l'étudiant (F7)."""
    form = DeliverableForm()
    if form.validate_on_submit():
        try:
            service.deposer(current_user, form.type_livrable.data, form.fichier.data)
            flash("Livrable déposé.", "success")
            return redirect(url_for("deliverables.mes_livrables"))
        except DepotError as erreur:
            flash(str(erreur), "danger")

    return render_template(
        "deliverables/mes_livrables.html",
        form=form,
        etats=service.etat_livrables(current_user),
        ouvert=service.depot_ouvert(),
        affecte=service.a_une_affectation_publiee(current_user),
        limite=current_app.config["DATE_LIMITE_DEPOT"],
    )


@deliverables_bp.route("/suivi")
@role_required("enseignant")
def suivi():
    """Livrables déposés par les étudiants de l'enseignant (F11)."""
    return render_template(
        "deliverables/suivi.html",
        livrables=service.livrables_de_l_encadrant(current_user),
        types=service.TYPES,
    )


@deliverables_bp.route("/<int:livrable_id>/valider", methods=["POST"])
@role_required("enseignant")
def valider(livrable_id):
    try:
        service.valider(current_user, livrable_id)
        flash("Livrable validé.", "success")
    except DepotError as erreur:
        flash(str(erreur), "danger")
    return redirect(url_for("deliverables.suivi"))


@deliverables_bp.route("/suivi/archive")
@role_required("enseignant")
def archive():
    """Archive de tous les documents de ses étudiants (F12)."""
    try:
        flux = service.archive_zip(current_user)
    except DepotError as erreur:
        flash(str(erreur), "warning")
        return redirect(url_for("deliverables.suivi"))
    return send_file(flux, mimetype="application/zip",
                     as_attachment=True, download_name="livrables.zip")


@deliverables_bp.route("/<int:livrable_id>/telecharger")
@login_required
def telecharger(livrable_id):
    """Téléchargement d'un fichier, réservé à son auteur, son encadrant et l'administration."""
    livrable = db.get_or_404(Deliverable, livrable_id)
    if not service.peut_telecharger(current_user, livrable):
        abort(403)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], livrable.fichier,
                               as_attachment=True,
                               download_name=service.nom_telechargement(livrable))