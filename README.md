# Plateforme de gestion des PFE et mini-projets

Application web de gestion des PFE et mini-projets : publication des sujets par les enseignants, choix des étudiants, affectation automatique, dépôt et suivi des livrables.

Projet réalisé par Ahmed Bejaoui (Licence 2, Institut Supérieur d'Informatique, 2026/2027).

## Technologies

Python, Flask, SQLAlchemy, Jinja2, Flask-Login, Flask-WTF, Bootstrap 5, pytest.

## Installation

Il faut Python 3.10 ou plus et Git. Dans un terminal :

    git clone https://github.com/Ahmed07-07/pfe_manage.git
    cd pfe_manage
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt

## Lancement

    python -m scripts.seed
    python run.py

Puis ouvrir http://127.0.0.1:5000 dans le navigateur.

## Comptes de test

Mot de passe de tous les comptes : Test1234

| Rôle | E-mail |
|---|---|
| Administrateur | admin@isi.tn |
| Enseignant | karray@isi.tn, trabelsi@isi.tn |
| Étudiant | ahmed@isi.tn, sana@isi.tn, youssef@isi.tn, mariem@isi.tn, omar@isi.tn |

## Tests

    python -m pytest -v

## Fonctionnalités

- Visiteur : présentation, connexion.
- Étudiant : catalogue des sujets, vœux classés, résultat d'affectation, dépôt des livrables.
- Enseignant : proposition de sujets, liste de ses étudiants, validation des livrables.
- Administrateur : validation des sujets, affectation, publication, export CSV, tableau de bord.

## Structure du projet

- app/routes : contrôleurs
- app/services : logique métier (affectation, vœux, livrables, export)
- app/templates : pages HTML
- app/models.py : base de données
- tests : tests pytest
- config.py : configuration
- run.py : lancement

## Limites et perspectives

- Un sujet est attribué à un seul étudiant (pas de binômes).
- Les dates limites sont dans config.py.
- Perspectives : soutenances, notation, notifications par e-mail.