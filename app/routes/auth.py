from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required

from app.forms import LoginForm
from app.models import User

auth_bp = Blueprint("auth", __name__)


def _adresse_interne(url):
    """Accepte seulement une adresse du site (évite une redirection vers un site externe)."""
    return bool(url) and url.startswith("/") and not url.startswith("//")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Connexion d'un utilisateur (F2)."""
    if current_user.is_authenticated:
        return redirect(url_for("main.accueil"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        if user is None or not user.check_password(form.mot_de_passe.data):
            flash("Adresse e-mail ou mot de passe incorrect.", "danger")
            return render_template("login.html", form=form)

        login_user(user)
        flash(f"Bienvenue {user.nom}.", "success")

        suivant = request.args.get("next")
        if _adresse_interne(suivant):
            return redirect(suivant)
        return redirect(url_for("main.accueil"))

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    """Déconnexion."""
    logout_user()
    flash("Vous êtes déconnecté.", "info")
    return redirect(url_for("main.accueil"))