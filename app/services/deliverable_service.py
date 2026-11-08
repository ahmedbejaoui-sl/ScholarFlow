import io
import os
import uuid
import zipfile
from datetime import datetime

from flask import current_app
from werkzeug.utils import secure_filename

from app import db
from app.models import Assignment, Deliverable, Subject, User, maintenant

TYPES = {
    "cahier": "Cahier des charges",
    "intermediaire": "Rapport intermédiaire",
    "final": "Rapport final",
}

# Les premiers octets d'un vrai fichier de chaque format
SIGNATURES = {"pdf": b"%PDF", "zip": b"PK"}


class DepotError(Exception):
    """Règle de gestion non respectée. Le message est affiché à l'utilisateur."""


# ---------- Outils internes ----------

def _extension(nom_fichier):
    return nom_fichier.rsplit(".", 1)[-1].lower() if "." in nom_fichier else ""


def _chemin(livrable):
    dossier = current_app.config["UPLOAD_FOLDER"]
    return os.path.join(dossier, os.path.basename(livrable.fichier))


def _etudiant_encadre_par(encadrant_id, etudiant_id):
    """Vrai si l'étudiant a une affectation publiée sur un sujet de cet encadrant."""
    return (Assignment.query
            .join(Subject, Assignment.sujet_id == Subject.id)
            .filter(Assignment.etudiant_id == etudiant_id,
                    Assignment.publie.is_(True),
                    Subject.encadrant_id == encadrant_id)
            .first()) is not None


# ---------- Consultation ----------

def depot_ouvert():
    """Vrai tant que la date limite n'est pas dépassée."""
    return datetime.now() <= current_app.config["DATE_LIMITE_DEPOT"]


def a_une_affectation_publiee(etudiant):
    return Assignment.query.filter_by(etudiant_id=etudiant.id, publie=True).first() is not None


def etat_livrables(etudiant):
    """Une ligne par type de livrable : (code, libellé, livrable ou None)."""
    deposes = {l.type: l for l in Deliverable.query.filter_by(etudiant_id=etudiant.id)}
    return [(code, libelle, deposes.get(code)) for code, libelle in TYPES.items()]


def livrables_de_l_encadrant(encadrant):
    """Livrables des étudiants affectés (résultats publiés) aux sujets de l'encadrant."""
    return (Deliverable.query
            .join(Assignment, Assignment.etudiant_id == Deliverable.etudiant_id)
            .join(Subject, Assignment.sujet_id == Subject.id)
            .join(User, Deliverable.etudiant_id == User.id)
            .filter(Subject.encadrant_id == encadrant.id,
                    Assignment.publie.is_(True))
            .order_by(User.nom, Deliverable.date_depot)
            .all())


def peut_telecharger(utilisateur, livrable):
    """Étudiant : ses fichiers. Enseignant : ceux de ses étudiants. Admin : tous."""
    if utilisateur.role == "admin":
        return True
    if utilisateur.role == "etudiant":
        return livrable.etudiant_id == utilisateur.id
    if utilisateur.role == "enseignant":
        return _etudiant_encadre_par(utilisateur.id, livrable.etudiant_id)
    return False


def nom_telechargement(livrable):
    """Nom lisible proposé au téléchargement (le nom stocké sur le disque reste interne)."""
    brut = f"{livrable.etudiant.nom}_{livrable.type}.{_extension(livrable.fichier)}"
    return secure_filename(brut)


# ---------- Actions ----------

def deposer(etudiant, type_livrable, fichier):
    """Enregistre un livrable après vérification de toutes les règles (F7)."""
    if type_livrable not in TYPES:
        raise DepotError("Type de livrable inconnu.")
    if not depot_ouvert():
        raise DepotError("La date limite est dépassée : les dépôts sont fermés.")
    if not a_une_affectation_publiee(etudiant):
        raise DepotError("Vous pourrez déposer vos livrables après la publication de votre affectation.")
    if fichier is None or not fichier.filename:
        raise DepotError("Choisissez un fichier.")

    ext = _extension(fichier.filename)
    if ext not in current_app.config["ALLOWED_EXTENSIONS"]:
        raise DepotError("Seuls les fichiers .pdf et .zip sont acceptés.")

    # Le contenu doit correspondre à l'extension annoncée
    entete = fichier.stream.read(4)
    fichier.stream.seek(0)
    if not entete.startswith(SIGNATURES.get(ext, b"\0")):
        raise DepotError("Le contenu du fichier ne correspond pas à son extension.")

    existant = Deliverable.query.filter_by(etudiant_id=etudiant.id, type=type_livrable).first()
    if existant and existant.valide:
        raise DepotError("Ce livrable a déjà été validé par votre encadrant : il ne peut plus être remplacé.")

    # Nom généré par le serveur : jamais le nom envoyé par l'utilisateur
    nom_stocke = f"{etudiant.id}_{type_livrable}_{uuid.uuid4().hex}.{ext}"
    dossier = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(dossier, exist_ok=True)
    fichier.save(os.path.join(dossier, nom_stocke))

    ancien = None
    if existant:
        ancien = existant.fichier
        existant.fichier = nom_stocke
        existant.date_depot = maintenant()
        existant.valide = False
    else:
        db.session.add(Deliverable(etudiant_id=etudiant.id, type=type_livrable, fichier=nom_stocke))
    db.session.commit()

    if ancien:  # on supprime l'ancien fichier seulement après l'enregistrement réussi
        try:
            os.remove(os.path.join(dossier, os.path.basename(ancien)))
        except OSError:
            pass


def valider(encadrant, livrable_id):
    """L'encadrant valide la réception et la conformité d'un livrable (F11)."""
    livrable = db.session.get(Deliverable, livrable_id)
    if livrable is None or not _etudiant_encadre_par(encadrant.id, livrable.etudiant_id):
        raise DepotError("Livrable introuvable.")
    livrable.valide = True
    db.session.commit()


def archive_zip(encadrant):
    """Archive .zip de tous les documents de ses étudiants (F12). Retourne un flux en mémoire."""
    livrables = livrables_de_l_encadrant(encadrant)
    if not livrables:
        raise DepotError("Aucun document à télécharger pour le moment.")

    flux = io.BytesIO()
    with zipfile.ZipFile(flux, "w", zipfile.ZIP_DEFLATED) as archive:
        for l in livrables:
            chemin = _chemin(l)
            if os.path.exists(chemin):
                dossier_etudiant = secure_filename(f"{l.etudiant.nom}_{l.etudiant.id}")
                archive.write(chemin, f"{dossier_etudiant}/{l.type}.{_extension(l.fichier)}")
    flux.seek(0)
    return flux