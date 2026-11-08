from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)

# Dates clés affichées sur la page d'accueil (à adapter à votre calendrier)
DATES_CLES = [
    {"etape": "Ouverture du catalogue des sujets", "date": "01/11/2026"},
    {"etape": "Clôture de la saisie des vœux", "date": "15/11/2026"},
    {"etape": "Publication des affectations", "date": "20/11/2026"},
    {"etape": "Date limite de dépôt des livrables", "date": "11/12/2026"},
]


@main_bp.route("/")
def accueil():
    """Page d'accueil publique (F1) : présentation et dates clés."""
    return render_template("accueil.html", dates=DATES_CLES)