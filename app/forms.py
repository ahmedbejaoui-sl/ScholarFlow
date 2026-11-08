from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Optional


class LoginForm(FlaskForm):
    """Formulaire de connexion (F2)."""
    email = StringField(
        "Adresse e-mail",
        validators=[DataRequired(message="L'adresse e-mail est obligatoire."),
                    Length(max=120)],
    )
    mot_de_passe = PasswordField(
        "Mot de passe",
        validators=[DataRequired(message="Le mot de passe est obligatoire.")],
    )
    submit = SubmitField("Se connecter")
class SubjectForm(FlaskForm):
    """Proposition d'un sujet par un enseignant (F8)."""
    titre = StringField(
        "Titre du sujet",
        validators=[DataRequired(message="Le titre est obligatoire."),
                    Length(max=200)],
    )
    resume = TextAreaField(
        "Résumé",
        validators=[DataRequired(message="Le résumé est obligatoire.")],
    )
    prerequis = TextAreaField("Prérequis", validators=[Optional()])
    technologies = StringField(
        "Technologies (séparées par des virgules)",
        validators=[Optional(), Length(max=200)],
    )
    niveau = SelectField(
        "Niveau",
        choices=[("L2", "Licence 2"), ("L3", "Licence 3"), ("M2", "Master 2")],
    )
    submit = SubmitField("Enregistrer le sujet")