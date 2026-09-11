"""WTForms used for authentication.

Using Flask-WTF gives us CSRF protection and server-side validation for free
instead of trusting whatever the client sends.
"""

from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from app.models import User


class LoginForm(FlaskForm):
    email = StringField("Email Address", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = SelectField(
        "Keep me signed in", choices=[("no", "No"), ("yes", "Yes")], default="no"
    )
    submit = SubmitField("Sign In to Dashboard")


class RegisterForm(FlaskForm):
    name = StringField("Full Name / Channel Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email Address", validators=[DataRequired(), Email(), Length(max=255)])
    role = SelectField(
        "I am a...", choices=[("creator", "Content Creator"), ("editor", "Video Editor")],
        default="creator",
    )
    password = PasswordField(
        "Create Password", validators=[DataRequired(), Length(min=8, message="Use at least 8 characters.")]
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create Account")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError("An account with that email already exists.")
