from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask import Flask, render_template

from config import Config

# Extensions créées une seule fois, branchées à l'application ensuite
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

login_manager.login_view = "auth.login"
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "warning"


def create_app(config_class=Config):
    """Crée et configure l'application Flask."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Charge les modèles pour que SQLAlchemy connaisse les tables
    from app import models  # noqa: F401
    # Enregistrement des blueprints (routes)
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)
    from app.routes.subjects import subjects_bp
    app.register_blueprint(subjects_bp)
    # Pages d'erreur personnalisées
    def page_erreur(code, titre, message):
        return render_template("errors/erreur.html",
                               code=code, titre=titre, message=message), code

    @app.errorhandler(403)
    def acces_refuse(e):
        return page_erreur(403, "Accès refusé",
                           "Vous n'avez pas les droits nécessaires pour consulter cette page.")

    @app.errorhandler(404)
    def page_introuvable(e):
        return page_erreur(404, "Page introuvable",
                           "L'adresse demandée n'existe pas ou a été déplacée.")

    @app.errorhandler(500)
    def erreur_serveur(e):
        db.session.rollback()
        return page_erreur(500, "Erreur du serveur",
                           "Un problème est survenu. Réessayez dans quelques instants.")
    
    return app