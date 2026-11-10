# Plateforme de gestion des PFE et mini-projets

Application web qui centralise le cycle de vie des PFE et mini-projets : publication des sujets par les enseignants, choix hiérarchisés par les étudiants, affectation automatique, puis dépôt et suivi des livrables.

Projet réalisé par Ahmed Bejaoui (Licence 2, Institut Supérieur d'Informatique, 2026/2027), dans le cadre de la matière « Outils de travail collaboratif (Génie logiciel) ».

## Technologies

Python 3, Flask, SQLAlchemy (SQLite en développement), Jinja2, Flask-Login, Flask-WTF, Bootstrap 5, pytest, Git et GitHub.

## Installation

Prérequis : Python 3.10 ou plus récent, et Git.

    git clone https://github.com/ahmedbejaoui-sl/ScholarFlow.git
    cd ScholarFlow
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt

Sous Mac ou Linux, remplacer la quatrième commande par : source venv/bin/activate

## Lancement

    python -m scripts.seed
    python run.py

Puis ouvrir http://127.0.0.1:5000 dans le navigateur. La première commande crée les comptes de test et n'est à lancer qu'une fois.

## Comptes de test

Mot de passe de tous les comptes : Test1234

| Rôle | E-mail |
|---|---|
| Administrateur | admin@isi.tn |
| Enseignant | karray@isi.tn, trabelsi@isi.tn |
| Étudiant | ahmed@isi.tn, sana@isi.tn, youssef@isi.tn, mariem@isi.tn, omar@isi.tn |

Ces comptes servent uniquement à la démonstration.

## Fonctionnalités

| Rôle | Fonctionnalités |
|---|---|
| Visiteur | Présentation, dates clés, connexion (F1, F2) |
| Étudiant | Catalogue filtré, vœux classés et validés, résultat d'affectation, dépôt des livrables (F3 à F7) |
| Enseignant | Proposition, modification et suppression de sujets, liste de ses étudiants, validation et téléchargement des livrables (F8 à F12) |
| Administrateur | Validation des sujets, affectation automatique et manuelle, publication, export CSV, tableau de bord (F13 à F17) |

## Parcours de démonstration

1. Un enseignant propose des sujets.
2. L'administrateur les valide.
3. Les étudiants classent leurs vœux et valident leur liste.
4. L'administrateur lance l'affectation, ajuste si besoin, puis publie les résultats.
5. Les étudiants consultent leur sujet et déposent leurs livrables.
6. Les enseignants valident les livrables ; l'administrateur suit le tableau de bord et exporte le CSV.

## Tests

    python -m pytest -v

54 tests automatisés : algorithme d'affectation, authentification et contrôle des rôles, règles de gestion des vœux, dépôt des livrables, export CSV. Ils utilisent une base en mémoire et ne touchent pas aux données de développement.

## Structure du projet

- app/routes : contrôleurs (un blueprint par domaine)
- app/services : logique métier (affectation, vœux, livrables, export, tableau de bord)
- app/templates : pages HTML (Jinja2)
- app/models.py : modèles de la base de données
- app/forms.py : formulaires
- app/decorators.py : contrôle d'accès par rôle
- scripts/seed.py : données de test
- tests : tests pytest
- config.py : configuration (dates limites, taille des fichiers)
- run.py : lancement

## Règles de gestion principales

- Un sujet n'est attribué qu'à un seul étudiant, et seuls les sujets validés par la commission sont affectables.
- Un étudiant choisit jusqu'à 5 sujets et peut modifier ou annuler sa fiche jusqu'à la clôture.
- L'affectation traite les vœux tour par tour. En cas de conflit, l'étudiant qui a validé sa liste en premier l'emporte.
- Les résultats ne sont visibles qu'après publication par la commission.
- Les livrables sont des fichiers .pdf ou .zip de 10 Mo maximum, déposés avant la date limite.
- Un enseignant n'accède qu'aux travaux de ses propres étudiants.

## Limites et perspectives

- Un sujet est attribué à un seul étudiant (pas de binômes).
- Les dates limites sont dans config.py, sans interface d'administration.
- Les heures sont enregistrées en UTC.
- Perspectives : gestion des soutenances, notation, notifications par e-mail, binômes.
