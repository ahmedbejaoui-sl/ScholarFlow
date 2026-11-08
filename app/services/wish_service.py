from datetime import datetime

from flask import current_app

from app import db
from app.models import Subject, Wish, WishValidation


class VoeuError(Exception):
    """Règle de gestion non respectée. Le message est affiché à l'étudiant."""


# ---------- Consultation ----------

def voeux_ouverts():
    """Vrai tant que la date de clôture n'est pas dépassée."""
    return datetime.now() <= current_app.config["DATE_CLOTURE_VOEUX"]


def est_valide(etudiant):
    """Vrai si l'étudiant a validé définitivement sa liste."""
    return WishValidation.query.filter_by(etudiant_id=etudiant.id).first() is not None


def liste_voeux(etudiant):
    """Vœux de l'étudiant, du premier au dernier choix."""
    return (Wish.query.filter_by(etudiant_id=etudiant.id)
            .order_by(Wish.priorite).all())


# ---------- Outils internes ----------

def _verifier_modifiable(etudiant):
    if not voeux_ouverts():
        raise VoeuError("La date de clôture des vœux est dépassée.")
    if est_valide(etudiant):
        raise VoeuError("Votre liste est validée. Rouvrez-la pour la modifier.")


def _voeu_de(etudiant, voeu_id):
    voeu = db.session.get(Wish, voeu_id)
    if voeu is None or voeu.etudiant_id != etudiant.id:
        raise VoeuError("Vœu introuvable.")
    return voeu


def _renumeroter(etudiant):
    """Rend les priorités contiguës (1, 2, 3...) après une suppression."""
    for rang, voeu in enumerate(liste_voeux(etudiant), start=1):
        if voeu.priorite != rang:
            voeu.priorite = rang
            db.session.flush()  # évite un conflit transitoire sur (étudiant, priorité)


# ---------- Actions ----------

def ajouter(etudiant, sujet_id):
    """Ajoute un sujet validé en dernière position de la liste."""
    _verifier_modifiable(etudiant)

    sujet = db.session.get(Subject, sujet_id)
    if sujet is None or sujet.statut != "valide":
        raise VoeuError("Ce sujet n'est pas disponible.")

    voeux = liste_voeux(etudiant)
    if any(v.sujet_id == sujet.id for v in voeux):
        raise VoeuError("Ce sujet est déjà dans votre liste.")

    maximum = current_app.config["MAX_VOEUX"]
    if len(voeux) >= maximum:
        raise VoeuError(f"Vous ne pouvez pas choisir plus de {maximum} sujets.")

    db.session.add(Wish(etudiant_id=etudiant.id, sujet_id=sujet.id,
                        priorite=len(voeux) + 1))
    db.session.commit()


def retirer(etudiant, voeu_id):
    """Retire un sujet de la liste."""
    _verifier_modifiable(etudiant)
    voeu = _voeu_de(etudiant, voeu_id)
    db.session.delete(voeu)
    _renumeroter(etudiant)
    db.session.commit()


def deplacer(etudiant, voeu_id, sens):
    """Échange un vœu avec son voisin du dessus ("haut") ou du dessous ("bas")."""
    _verifier_modifiable(etudiant)
    voeu = _voeu_de(etudiant, voeu_id)

    rang_voisin = voeu.priorite - 1 if sens == "haut" else voeu.priorite + 1
    voisin = Wish.query.filter_by(etudiant_id=etudiant.id,
                                  priorite=rang_voisin).first()
    if voisin is None:
        return  # déjà en première ou dernière position

    rang_a, rang_b = voeu.priorite, voisin.priorite
    voeu.priorite = 0            # valeur temporaire (les rangs réels commencent à 1)
    db.session.flush()
    voisin.priorite = rang_a
    db.session.flush()
    voeu.priorite = rang_b
    db.session.commit()


def valider(etudiant):
    """Valide définitivement la liste (elle devient non modifiable)."""
    _verifier_modifiable(etudiant)
    minimum = current_app.config["MIN_VOEUX"]
    if len(liste_voeux(etudiant)) < minimum:
        raise VoeuError(f"Choisissez au moins {minimum} sujet(s) avant de valider.")
    db.session.add(WishValidation(etudiant_id=etudiant.id))
    db.session.commit()


def rouvrir(etudiant):
    """Annule la validation pour pouvoir modifier la liste (avant la clôture)."""
    if not voeux_ouverts():
        raise VoeuError("La date de clôture des vœux est dépassée.")
    WishValidation.query.filter_by(etudiant_id=etudiant.id).delete()
    db.session.commit()


def annuler(etudiant):
    """Supprime toute la fiche de vœux (avant la clôture)."""
    if not voeux_ouverts():
        raise VoeuError("La date de clôture des vœux est dépassée.")
    Wish.query.filter_by(etudiant_id=etudiant.id).delete()
    WishValidation.query.filter_by(etudiant_id=etudiant.id).delete()
    db.session.commit()