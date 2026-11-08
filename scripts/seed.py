"""Crée des utilisateurs de test (administrateur, enseignants, étudiants).

Lancement, depuis la racine du projet :
    python -m scripts.seed
"""
from app import create_app, db
from app.models import User

MOT_DE_PASSE_TEST = "Test1234"

UTILISATEURS = [
    ("Commission PFE", "admin@isi.tn", "admin"),
    ("Mme Karray", "karray@isi.tn", "enseignant"),
    ("M. Trabelsi", "trabelsi@isi.tn", "enseignant"),
    ("Ahmed Bejaoui", "ahmed@isi.tn", "etudiant"),
    ("Sana Ben Ali", "sana@isi.tn", "etudiant"),
    ("Youssef Gharbi", "youssef@isi.tn", "etudiant"),
    ("Mariem Jlassi", "mariem@isi.tn", "etudiant"),
    ("Omar Hamdi", "omar@isi.tn", "etudiant"),
]


def creer_utilisateurs():
    """Ajoute les utilisateurs absents de la base (peut être relancé sans risque)."""
    ajoutes = 0
    for nom, email, role in UTILISATEURS:
        if User.query.filter_by(email=email).first():
            continue
        user = User(nom=nom, email=email, role=role)
        user.set_password(MOT_DE_PASSE_TEST)
        db.session.add(user)
        ajoutes += 1
    db.session.commit()
    return ajoutes


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
        n = creer_utilisateurs()
        print(f"{n} utilisateur(s) ajouté(s). Mot de passe de test : {MOT_DE_PASSE_TEST}")