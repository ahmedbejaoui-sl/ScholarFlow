"""Remplit la base avec des données de démonstration (captures d'écran).

ATTENTION : efface toutes les données existantes (base et fichiers déposés).

    python -m scripts.demo 1   sujets et listes de vœux validées (avant l'affectation)
    python -m scripts.demo 2   + affectation calculée, non publiée
    python -m scripts.demo 3   + ajustement manuel, publication et livrables (défaut)
"""
import os
import sys
import unicodedata
import uuid
from datetime import datetime, timedelta, timezone

from app import create_app, db
from app.models import Deliverable, User, Subject, Wish, WishValidation
from app.services import assignment_service
from app.services.deliverable_service import TYPES
from scripts.seed import creer_utilisateurs

# (titre, résumé, prérequis, technologies, niveau, encadrant, statut, commentaire de la commission)
SUJETS = [
    ("Gestion d'une bibliothèque universitaire",
     "Application de catalogue, d'emprunt et de retour d'ouvrages avec suivi des retards.",
     "Bases de données, HTML/CSS", "Flask, SQLAlchemy, Bootstrap", "L2",
     "karray@isi.tn", "valide", None),
    ("Plateforme de covoiturage étudiant",
     "Mise en relation d'étudiants pour partager leurs trajets vers le campus.",
     "Python, notions de JavaScript", "Flask, JavaScript", "L2",
     "trabelsi@isi.tn", "valide", None),
    ("Suivi des stages en entreprise",
     "Dépôt des offres, candidatures et suivi de l'avancement des stages.",
     "Bases de données", "Flask, SQLite", "L2",
     "karray@isi.tn", "valide", None),
    ("Tableau de bord de consommation énergétique",
     "Visualisation de la consommation électrique des salles du campus.",
     "Python, notions de statistiques", "Python, Chart.js", "L3",
     "trabelsi@isi.tn", "valide", None),
    ("Réservation de salles et de matériel",
     "Calendrier de réservation avec détection des conflits d'horaires.",
     "Bases de données", "Flask, SQLAlchemy", "L2",
     "karray@isi.tn", "valide", None),
    ("Gestion d'un budget personnel",
     "Saisie des dépenses, catégories et bilans mensuels sous forme de graphiques.",
     "HTML/CSS, Python", "Flask, Chart.js", "L2",
     "trabelsi@isi.tn", "valide", None),
    ("Plateforme de quiz en ligne",
     "Création de quiz par les enseignants et passage par les étudiants avec correction automatique.",
     "Python, JavaScript", "Flask, JavaScript", "L2",
     "karray@isi.tn", "valide", None),
    ("Gestion d'un club d'étudiants",
     "Adhésions, événements et communication interne d'un club étudiant.",
     "Bases de données", "Flask, Bootstrap", "L2",
     "trabelsi@isi.tn", "valide", None),
    ("Messagerie interne du département",
     "Échange de messages entre enseignants et étudiants au sein de la plateforme.",
     "Python, bases de données", "Flask, SQLAlchemy", "L3",
     "karray@isi.tn", "en_attente", None),
    ("Boutique en ligne",
     "Catalogue de produits, panier et gestion des commandes.",
     "Python, bases de données", "Flask, SQLAlchemy", "L2",
     "trabelsi@isi.tn", "modification",
     "Précisez le périmètre : le paiement en ligne est exclu pour un projet de L2."),
    ("Recommandation de films par apprentissage automatique",
     "Système de recommandation fondé sur l'historique de notes des utilisateurs.",
     "Apprentissage automatique", "Python, scikit-learn", "M2",
     "karray@isi.tn", "refuse",
     "Sujet hors du programme de L2 (apprentissage automatique)."),
]

# Vœux des étudiants : positions dans la liste SUJETS, du 1er au dernier choix.
# Ahmed, Sana et Youssef veulent tous le sujet 0 : c'est le conflit à résoudre.
VOEUX = {
    "ahmed@isi.tn": [0, 1, 2],
    "sana@isi.tn": [0, 3, 4],
    "youssef@isi.tn": [0, 1, 5],
    "mariem@isi.tn": [1, 3, 6],
    "omar@isi.tn": [2, 4],          # n'a pas validé sa liste
}

# Ordre de validation des listes : il départage les conflits
ORDRE_VALIDATION = ["ahmed@isi.tn", "sana@isi.tn", "youssef@isi.tn", "mariem@isi.tn"]

# Livrables déposés : (type, validé par l'encadrant ?)
LIVRABLES = {
    "ahmed@isi.tn": [("cahier", True), ("intermediaire", False)],
    "sana@isi.tn": [("cahier", False)],
    "mariem@isi.tn": [("cahier", True), ("intermediaire", True)],
}


def _utilisateur(email):
    return User.query.filter_by(email=email).one()


def pdf_minimal(texte):
    """Construit un petit PDF valide contenant une ligne de texte."""
    texte = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()
    texte = texte.replace("\\", " ").replace("(", " ").replace(")", " ")
    flux = f"BT /F1 16 Tf 40 150 Td ({texte}) Tj ET".encode()
    objets = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 400 300] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(flux) + flux + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    sortie = bytearray(b"%PDF-1.4\n")
    decalages = []
    for numero, objet in enumerate(objets, start=1):
        decalages.append(len(sortie))
        sortie += f"{numero} 0 obj\n".encode() + objet + b"\nendobj\n"
    debut_xref = len(sortie)
    sortie += f"xref\n0 {len(objets) + 1}\n".encode()
    sortie += b"0000000000 65535 f \n"
    for decalage in decalages:
        sortie += f"{decalage:010d} 00000 n \n".encode()
    sortie += (f"trailer\n<< /Size {len(objets) + 1} /Root 1 0 R >>\n"
               f"startxref\n{debut_xref}\n%%EOF\n").encode()
    return bytes(sortie)


def vider_depots(dossier):
    """Supprime les fichiers déposés lors d'essais précédents."""
    if os.path.isdir(dossier):
        for nom in os.listdir(dossier):
            chemin = os.path.join(dossier, nom)
            if os.path.isfile(chemin):
                os.remove(chemin)


def creer_sujets():
    sujets = []
    for titre, resume, prerequis, techno, niveau, email, statut, commentaire in SUJETS:
        sujet = Subject(titre=titre, resume=resume, prerequis=prerequis,
                        technologies=techno, niveau=niveau, statut=statut,
                        commentaire_admin=commentaire,
                        encadrant_id=_utilisateur(email).id)
        db.session.add(sujet)
        sujets.append(sujet)
    db.session.commit()
    return sujets


def creer_voeux(sujets):
    for email, positions in VOEUX.items():
        etudiant = _utilisateur(email)
        for rang, position in enumerate(positions, start=1):
            db.session.add(Wish(etudiant_id=etudiant.id,
                                sujet_id=sujets[position].id, priorite=rang))

    debut = datetime(2026, 11, 3, 9, 0)
    for n, email in enumerate(ORDRE_VALIDATION):
        db.session.add(WishValidation(etudiant_id=_utilisateur(email).id,
                                      date_validation=debut + timedelta(hours=n)))
    db.session.commit()


def creer_livrables(dossier):
    os.makedirs(dossier, exist_ok=True)
    maintenant = datetime.now(timezone.utc)
    for email, liste in LIVRABLES.items():
        etudiant = _utilisateur(email)
        for n, (type_livrable, valide) in enumerate(liste):
            nom = f"{etudiant.id}_{type_livrable}_{uuid.uuid4().hex}.pdf"
            contenu = pdf_minimal(f"{etudiant.nom} - {TYPES[type_livrable]}")
            with open(os.path.join(dossier, nom), "wb") as fichier:
                fichier.write(contenu)
            db.session.add(Deliverable(etudiant_id=etudiant.id, type=type_livrable,
                                       fichier=nom, valide=valide,
                                       date_depot=maintenant - timedelta(days=4 - n)))
    db.session.commit()


def main(etape):
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        vider_depots(app.config["UPLOAD_FOLDER"])

        creer_utilisateurs()
        sujets = creer_sujets()
        creer_voeux(sujets)
        print("Étape 1 : sujets et listes de vœux créés.")

        if etape >= 2:
            affectes, participants = assignment_service.lancer()
            print(f"Étape 2 : affectation calculée ({affectes} affecté(s) sur {participants}).")

        if etape >= 3:
            # Omar n'a pas validé sa liste : la commission lui attribue un sujet libre
            assignment_service.affecter_manuellement(_utilisateur("omar@isi.tn").id,
                                                     sujets[2].id)
            assignment_service.publier()
            creer_livrables(app.config["UPLOAD_FOLDER"])
            print("Étape 3 : résultats publiés et livrables déposés.")

    print("Terminé. Lancez : python run.py (mot de passe de tous les comptes : Test1234)")


if __name__ == "__main__":
    etape = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 3
    if etape not in (1, 2, 3):
        sys.exit("Utilisation : python -m scripts.demo [1|2|3]")
    reponse = input("Cette commande efface toutes les données existantes. "
                    "Tapez OUI pour continuer : ")
    if reponse.strip() != "OUI":
        sys.exit("Annulé.")
    main(etape)