from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length


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