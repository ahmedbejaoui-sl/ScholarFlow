from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def role_required(*roles):
    """Réserve une route aux utilisateurs ayant l'un des rôles indiqués.

    Utilisation :
        @role_required("admin")
        @role_required("enseignant", "admin")

    - Non connecté : redirigé vers la page de connexion.
    - Connecté avec un mauvais rôle : erreur 403 (accès refusé).
    """
    def decorateur(vue):
        @wraps(vue)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return vue(*args, **kwargs)
        return wrapper
    return decorateur