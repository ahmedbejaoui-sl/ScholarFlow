from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import current_user, login_required

from app import db
from app.decorators import role_required
from app.forms import SubjectForm
from app.models import Subject, User

subjects_bp = Blueprint("subjects", __name__, url_prefix="/subjects")


@subjects_bp.route("/mes-sujets")
@role_required("enseignant")
def mes_sujets():
    """Liste des sujets de l'enseignant connecté, avec leur statut."""
    sujets = (Subject.query
              .filter_by(encadrant_id=current_user.id)
              .order_by(Subject.id.desc())
              .all())
    return render_template("subjects/mes_sujets.html", sujets=sujets)


@subjects_bp.route("/nouveau", methods=["GET", "POST"])
@role_required("enseignant")
def nouveau():
    """Dépôt d'une proposition de sujet (F8)."""
    form = SubjectForm()
    if form.validate_on_submit():
        sujet = Subject(
            titre=form.titre.data.strip(),
            resume=form.resume.data.strip(),
            prerequis=(form.prerequis.data or "").strip() or None,
            technologies=(form.technologies.data or "").strip() or None,
            niveau=form.niveau.data,
            statut="en_attente",
            encadrant_id=current_user.id,
        )
        db.session.add(sujet)
        db.session.commit()
        flash("Sujet enregistré. Il sera visible des étudiants après validation par la commission.",
              "success")
        return redirect(url_for("subjects.mes_sujets"))

    return render_template("subjects/form.html", form=form, titre_page="Proposer un sujet")
def _sujet_de_l_enseignant(sujet_id):
    """Retourne le sujet demandé, à condition qu'il appartienne à l'enseignant connecté."""
    sujet = db.get_or_404(Subject, sujet_id)
    if sujet.encadrant_id != current_user.id:
        abort(403)
    return sujet


@subjects_bp.route("/<int:sujet_id>/modifier", methods=["GET", "POST"])
@role_required("enseignant")
def modifier(sujet_id):
    """Modification d'un sujet non validé (F9)."""
    sujet = _sujet_de_l_enseignant(sujet_id)

    if sujet.statut == "valide":
        flash("Un sujet validé ne peut plus être modifié.", "warning")
        return redirect(url_for("subjects.mes_sujets"))

    form = SubjectForm(obj=sujet)
    if form.validate_on_submit():
        sujet.titre = form.titre.data.strip()
        sujet.resume = form.resume.data.strip()
        sujet.prerequis = (form.prerequis.data or "").strip() or None
        sujet.technologies = (form.technologies.data or "").strip() or None
        sujet.niveau = form.niveau.data
        # Le sujet repart en examen auprès de la commission
        sujet.statut = "en_attente"
        sujet.commentaire_admin = None
        db.session.commit()
        flash("Sujet modifié. Il est de nouveau en attente de validation.", "success")
        return redirect(url_for("subjects.mes_sujets"))

    return render_template("subjects/form.html", form=form, titre_page="Modifier le sujet")


@subjects_bp.route("/<int:sujet_id>/supprimer", methods=["POST"])
@role_required("enseignant")
def supprimer(sujet_id):
    """Suppression d'un sujet non validé (F9). Uniquement par POST."""
    sujet = _sujet_de_l_enseignant(sujet_id)

    if sujet.statut == "valide":
        flash("Un sujet validé ne peut plus être supprimé.", "warning")
        return redirect(url_for("subjects.mes_sujets"))

    db.session.delete(sujet)
    db.session.commit()
    flash("Sujet supprimé.", "info")
    return redirect(url_for("subjects.mes_sujets"))
SUJETS_PAR_PAGE = 6


@subjects_bp.route("/")
@login_required
def catalogue():
    """Catalogue des sujets validés, avec filtres et pagination (F3)."""
    page = request.args.get("page", 1, type=int)
    mot_cle = request.args.get("q", "").strip()
    techno = request.args.get("techno", "").strip()
    encadrant_id = request.args.get("encadrant", type=int)

    requete = Subject.query.filter_by(statut="valide")

    if mot_cle:
        motif = f"%{mot_cle}%"
        requete = requete.filter(
            db.or_(Subject.titre.ilike(motif), Subject.resume.ilike(motif))
        )
    if techno:
        requete = requete.filter(Subject.technologies.ilike(f"%{techno}%"))
    if encadrant_id:
        requete = requete.filter_by(encadrant_id=encadrant_id)

    pagination = requete.order_by(Subject.titre).paginate(
        page=page, per_page=SUJETS_PAR_PAGE, error_out=False
    )
    encadrants = User.query.filter_by(role="enseignant").order_by(User.nom).all()

    return render_template(
        "subjects/catalogue.html",
        pagination=pagination,
        encadrants=encadrants,
        q=mot_cle,
        techno=techno,
        encadrant_id=encadrant_id,
    )


@subjects_bp.route("/<int:sujet_id>")
@login_required
def detail(sujet_id):
    """Détail d'un sujet. Un sujet non validé n'est visible que par son encadrant et l'admin."""
    sujet = db.get_or_404(Subject, sujet_id)
    if sujet.statut != "valide":
        if current_user.role != "admin" and sujet.encadrant_id != current_user.id:
            abort(404)
    return render_template("subjects/detail.html", sujet=sujet)