from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager


def maintenant():
    """Date et heure actuelles (UTC)."""
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    """Utilisateur : étudiant, enseignant ou administrateur."""
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # etudiant | enseignant | admin

    def set_password(self, mot_de_passe):
        self.password_hash = generate_password_hash(mot_de_passe)

    def check_password(self, mot_de_passe):
        return check_password_hash(self.password_hash, mot_de_passe)


class Subject(db.Model):
    """Sujet de projet proposé par un enseignant."""
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    resume = db.Column(db.Text, nullable=False)
    prerequis = db.Column(db.Text)
    technologies = db.Column(db.String(200))
    niveau = db.Column(db.String(50))
    # en_attente | valide | modification | refuse
    statut = db.Column(db.String(20), default="en_attente", nullable=False)
    commentaire_admin = db.Column(db.Text)
    encadrant_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    encadrant = db.relationship("User", backref="sujets")


class Wish(db.Model):
    """Vœu d'un étudiant : un sujet avec un ordre de préférence."""
    id = db.Column(db.Integer, primary_key=True)
    etudiant_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    sujet_id = db.Column(db.Integer, db.ForeignKey("subject.id"), nullable=False)
    priorite = db.Column(db.Integer, nullable=False)  # 1 = premier choix
    date_creation = db.Column(db.DateTime, default=maintenant)

    __table_args__ = (
        db.UniqueConstraint("etudiant_id", "sujet_id"),   # pas de doublon de sujet
        db.UniqueConstraint("etudiant_id", "priorite"),   # une seule place par rang
    )

    etudiant = db.relationship("User")
    sujet = db.relationship("Subject")


class Assignment(db.Model):
    """Affectation d'un sujet à un étudiant."""
    id = db.Column(db.Integer, primary_key=True)
    etudiant_id = db.Column(db.Integer, db.ForeignKey("user.id"),
                            unique=True, nullable=False)
    sujet_id = db.Column(db.Integer, db.ForeignKey("subject.id"),
                         unique=True, nullable=False)
    publie = db.Column(db.Boolean, default=False)

    etudiant = db.relationship("User")
    sujet = db.relationship("Subject")


class Deliverable(db.Model):
    """Livrable déposé par un étudiant."""
    id = db.Column(db.Integer, primary_key=True)
    etudiant_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    type = db.Column(db.String(30), nullable=False)  # cahier | intermediaire | final
    fichier = db.Column(db.String(255), nullable=False)
    date_depot = db.Column(db.DateTime, default=maintenant)
    valide = db.Column(db.Boolean, default=False)

    etudiant = db.relationship("User")


@login_manager.user_loader
def load_user(user_id):
    """Recharge l'utilisateur connecté à chaque requête."""
    return db.session.get(User, int(user_id))